import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from src.retrieval.retriever import get_retriever
from src.generation.generator import get_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

app = FastAPI(title="Tubibot V2 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- RAG pipeline (main.py'den aynen) ---

QUERY_EXPANSION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "Kullanıcının sorusunu vektör veritabanında arama için HAFİFÇE genişlet. "
               "KESİNLİKLE soruya cevap verme.\n\n"
               "KURALLAR:\n"
               "1. Orijinal soruyu neredeyse AYNEN koru.\n"
               "2. SADECE kısaltmaların açılımını parantez içinde ekle:\n"
               "   - SKA -> Sürdürülebilir Kalkınma Amaçları (SKA)\n"
               "   - 2209-A -> TÜBİTAK 2209-A\n"
               "3. Kendi bilginden ek anahtar kelime, konu veya alan EKLEME.\n"
               "4. Soruda birden fazla alt soru veya konu varsa HEPSİNİ koru.\n"
               "5. Sorunun niyetini DEĞİŞTİRME.\n"
               "6. Yazım hatalarını düzelt."),
    ("human", "{question}")
])

RAG_SYSTEM_PROMPT = """Sen "Tubibot"sun — TÜBİTAK 2209-A ve Sürdürülebilir Kalkınma Amaçları (SKA) konusunda yardımcı bir asistan.
Aşağıdaki bağlamı kullanarak soruyu cevapla. Bilgiyi kullanıcının sorusuyla ilişkilendirerek açıkla.
Bağlamda olmayan bilgiyi uydurma. Kaynak veya referans numarası belirtme. Metin içindeki dahili belge atıflarını çıkar.

BAĞLAM:
{context}"""

RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", RAG_SYSTEM_PROMPT),
    ("human", "{question}")
])


def format_docs_plain(docs):
    formatted_parts = []
    for doc in docs:
        source = doc.metadata.get("source_document", "Bilinmeyen Belge")
        section = doc.metadata.get("section_heading", "Genel")
        header = f"[Kaynak: {source} | Bölüm: {section}]"
        formatted_parts.append(f"{header}\n{doc.page_content}")
    return "\n\n---\n\n".join(formatted_parts)


# Uygulama baslarken RAG bilesenlerini yukle
retriever = None
llm = None
parser = StrOutputParser()
query_expansion_chain = None


@app.on_event("startup")
def startup():
    global retriever, llm, query_expansion_chain
    print("[INFO] Tubibot V2 API baslatiliyor...")
    retriever = get_retriever()
    llm = get_llm()
    query_expansion_chain = QUERY_EXPANSION_PROMPT | llm | parser
    print("[INFO] RAG pipeline hazir.")


class ChatRequest(BaseModel):
    message: str


@app.post("/api/chat")
async def chat(request: ChatRequest):
    raw_question = request.message

    # 1. Query Expansion
    try:
        expanded_question = query_expansion_chain.invoke({"question": raw_question}).strip()
    except Exception:
        expanded_question = raw_question

    # 2. Retrieval
    docs = retriever.invoke(expanded_question)

    if not docs:
        async def empty_stream():
            yield "Bu konuyla ilgili mevcut belgelerde herhangi bir bilgi bulunamadı."
        return StreamingResponse(empty_stream(), media_type="text/plain")

    # 3. Context
    context = format_docs_plain(docs)

    # 4. Streaming LLM response
    response_chain = RAG_PROMPT | llm

    async def generate():
        for chunk in response_chain.stream({
            "context": context,
            "question": raw_question
        }):
            if hasattr(chunk, "content") and chunk.content:
                yield chunk.content
                await asyncio.sleep(0)

    return StreamingResponse(generate(), media_type="text/plain", headers={
        "Cache-Control": "no-cache",
        "X-Content-Type-Options": "nosniff",
    })


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "Tubibot V2"}
