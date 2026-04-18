import asyncio
import json
import os
from urllib.parse import unquote

import fitz  # PyMuPDF
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from api import state
from api.formatters import format_docs_plain, format_gundem_docs
from api.paths import DUYURULAR_JSON, HABERLER_JSON, PDF_DIR, THUMB_DIR
from api.prompts import GUNDEM_PROMPT, RAG_PROMPT
from api.schemas import ChatRequest

router = APIRouter()


# ====================================================================
# Health
# ====================================================================

@router.get("/api/health")
async def health():
    return {"status": "ok", "service": "Tubibot V2"}


# ====================================================================
# Chat — ana PDF RAG (/api/chat)
# ====================================================================

@router.post("/api/chat")
async def chat(request: ChatRequest):
    raw_question = request.message
    selected_llm = state._get_or_create_llm(request.model)

    try:
        expanded_question = state.query_expansion_chain.invoke(
            {"question": raw_question}
        ).strip()
    except Exception:
        expanded_question = raw_question

    docs = state.retriever.invoke(expanded_question)

    if not docs:
        async def empty_stream():
            yield "Bu konuyla ilgili mevcut belgelerde herhangi bir bilgi bulunamadı."
        return StreamingResponse(empty_stream(), media_type="text/plain")

    context = format_docs_plain(docs)
    response_chain = RAG_PROMPT | selected_llm

    async def generate():
        for chunk in response_chain.stream({
            "context": context,
            "question": raw_question,
        }):
            if hasattr(chunk, "content") and chunk.content:
                yield chunk.content
                await asyncio.sleep(0)

    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "X-Content-Type-Options": "nosniff",
        },
    )


# ====================================================================
# Chat — gündem RAG (/api/chat-gundem)
# ====================================================================

@router.post("/api/chat-gundem")
async def chat_gundem(request: ChatRequest):
    """
    Gündem (duyuru + haber) sohbeti. Yalnızca backend/data/gundem_vector_db
    veritabanından cevap verir; ana PDF DB'sine dokunmaz.
    """
    if state.gundem_retriever is None:
        async def not_ready():
            yield "Gündem veritabanı henüz hazır değil. Lütfen önce içerik güncellemesi yapın."
        return StreamingResponse(not_ready(), media_type="text/plain")

    raw_question = request.message
    selected_llm = state._get_or_create_llm(request.model)

    docs = state.gundem_retriever.invoke(raw_question)

    if not docs:
        async def empty_stream():
            yield "Bu konuyla ilgili güncel bir duyuru veya haber bulunamadı."
        return StreamingResponse(empty_stream(), media_type="text/plain")

    context = format_gundem_docs(docs)
    response_chain = GUNDEM_PROMPT | selected_llm

    async def generate():
        for chunk in response_chain.stream({
            "context": context,
            "question": raw_question,
        }):
            if hasattr(chunk, "content") and chunk.content:
                yield chunk.content
                await asyncio.sleep(0)

    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "X-Content-Type-Options": "nosniff",
        },
    )


# ====================================================================
# Duyuru / Haber JSON + scraper trigger
# ====================================================================

def _read_json(path: str) -> list:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


@router.post("/api/icerikleri-guncelle")
async def icerikleri_guncelle():
    """
    Her iki scraper'ı çalıştırıp duyurular.json + haberler.json günceller,
    ardından yalnızca gündem vektör veritabanını yeniden inşa eder.
    Ana PDF DB'sine (backend/data/vector_db) DOKUNULMAZ.
    """
    try:
        from scraper_duyurular import run_scraper as run_duyurular
        from scraper_haberler import run_scraper as run_haberler
        from src.database.gundem_vector_store import build_gundem_vector_database
        from src.retrieval.retriever import get_gundem_retriever

        duyurular = await asyncio.to_thread(run_duyurular)
        haberler = await asyncio.to_thread(run_haberler)

        await asyncio.to_thread(build_gundem_vector_database)

        state.gundem_retriever = await asyncio.to_thread(get_gundem_retriever)

        return {
            "status": "ok",
            "duyuru_count": len(duyurular),
            "haber_count": len(haberler),
            "gundem_rag_rebuilt": True,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/api/duyurular")
async def get_duyurular():
    return _read_json(DUYURULAR_JSON)


@router.get("/api/haberler")
async def get_haberler():
    return _read_json(HABERLER_JSON)


# ====================================================================
# Dokümanlar (PDF list / thumbnail / download)
# ====================================================================

def _thumb_path_for(pdf_name: str) -> str:
    base = pdf_name
    while base.lower().endswith(".pdf"):
        base = base[:-4]
    return os.path.join(THUMB_DIR, base + ".jpg")


def _ensure_thumbnail(pdf_name: str):
    pdf_path = os.path.join(PDF_DIR, pdf_name)
    if not os.path.isfile(pdf_path):
        return None
    os.makedirs(THUMB_DIR, exist_ok=True)
    thumb = _thumb_path_for(pdf_name)
    if os.path.isfile(thumb) and os.path.getmtime(thumb) >= os.path.getmtime(pdf_path):
        return thumb
    try:
        with fitz.open(pdf_path) as doc:
            page = doc.load_page(0)
            pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0), alpha=False)
            pix.save(thumb, jpg_quality=80)
        return thumb
    except Exception:
        return None


@router.get("/api/dokumanlar")
async def get_dokumanlar():
    if not os.path.isdir(PDF_DIR):
        return []
    items = []
    for fname in sorted(os.listdir(PDF_DIR)):
        if not fname.lower().endswith(".pdf"):
            continue
        fpath = os.path.join(PDF_DIR, fname)
        title = fname
        while title.lower().endswith(".pdf"):
            title = title[:-4]
        title = title.replace("_", " ").strip()
        items.append({
            "filename": fname,
            "title": title,
            "size_bytes": os.path.getsize(fpath),
            "download_url": f"/api/dokumanlar/indir/{fname}",
            "thumbnail_url": f"/api/dokumanlar/thumb/{fname}",
        })
    return items


@router.get("/api/dokumanlar/thumb/{filename:path}")
async def get_dokuman_thumb(filename: str):
    safe_name = os.path.basename(unquote(filename))
    if not safe_name.lower().endswith(".pdf"):
        raise HTTPException(status_code=404, detail="PDF değil")
    thumb = await asyncio.to_thread(_ensure_thumbnail, safe_name)
    if not thumb or not os.path.isfile(thumb):
        raise HTTPException(status_code=404, detail="Thumbnail üretilemedi")
    return FileResponse(thumb, media_type="image/jpeg")


@router.get("/api/dokumanlar/indir/{filename:path}")
async def download_dokuman(filename: str):
    safe_name = os.path.basename(unquote(filename))
    fpath = os.path.join(PDF_DIR, safe_name)
    if not os.path.isfile(fpath) or not safe_name.lower().endswith(".pdf"):
        raise HTTPException(status_code=404, detail="Doküman bulunamadı")
    return FileResponse(
        fpath,
        media_type="application/pdf",
        filename=safe_name,
    )
