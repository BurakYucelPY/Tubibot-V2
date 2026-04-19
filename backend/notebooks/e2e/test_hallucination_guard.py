"""
e2e/test_hallucination_guard.py

Halüsinasyon koruması: alan dışı sorularda LLM "bilmiyorum"
benzeri bir yanıt vermeli, uydurma yapmamalı.
- PDF RAG (get_rag_chain) 3 OOS soru
- Gündem RAG (get_gundem_retriever + GUNDEM_PROMPT | llm) 3 OOS soru

Live: Groq API + her iki vector_db.
"""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from _helpers.bootstrap import setup_backend_path
BACKEND_ROOT = setup_backend_path()

from _helpers.runner import TestRunner


GUARD_KEYWORDS = (
    "bilgi yer almıyor",
    "bilgi bulunamadı",
    "bilgi bulunmuyor",
    "bilmiyorum",
    "cevap veremem",
    "mevcut değil",
    "yer almamakta",
    "bulunmamakta",
    "emin değil",
    "kaynaklarda",
    "belgede yer almıyor",
    "belirtilmemiş",
)


def _is_guarded(text: str) -> bool:
    t = (text or "").lower()
    return any(k in t for k in GUARD_KEYWORDS)


def main():
    runner = TestRunner("e2e/test_hallucination_guard")

    if not os.getenv("GROQ_API_KEY"):
        runner.check("GROQ_API_KEY mevcut", False, "Ortamda tanımlı değil")
        return runner.summary()

    # --- PDF tarafı ---
    from main import get_rag_chain
    chain = get_rag_chain()

    pdf_oos = [
        "New York Yankees bu yıl kaç kupa kazandı?",
        "İstanbul'da yarın hava nasıl olacak?",
        "Python'da list comprehension nasıl yazılır?",
    ]
    pdf_guarded = 0
    for q in pdf_oos:
        runner.info(f"[PDF OOS] {q}")
        try:
            ans = chain(q)
        except Exception as e:
            runner.check(f"PDF chain crash — {type(e).__name__}", False, str(e)[:80])
            continue
        guarded = _is_guarded(ans)
        if guarded:
            pdf_guarded += 1
        runner.check(
            f"[PDF] '{q[:35]}...' → guard",
            guarded,
            f"yanıt ilk 120: {(ans or '')[:120]!r}",
        )
    runner.check(
        f"PDF OOS guard oranı ≥ 2/{len(pdf_oos)}",
        pdf_guarded >= 2,
        f"{pdf_guarded}/{len(pdf_oos)}",
    )

    # --- Gündem tarafı ---
    gundem_db = os.path.join(BACKEND_ROOT, "data", "gundem_vector_db")
    if not os.path.isdir(gundem_db):
        runner.info("gundem_vector_db yok — gündem OOS testleri atlandı.")
        return runner.summary()

    from langchain_core.output_parsers import StrOutputParser
    from src.retrieval.retriever_gundem import get_gundem_retriever
    from src.generation.generator import get_llm
    from api.formatters import format_gundem_docs
    from api.prompts import GUNDEM_PROMPT

    g_retriever = get_gundem_retriever()
    llm = get_llm()
    parser = StrOutputParser()
    g_chain = GUNDEM_PROMPT | llm | parser

    gundem_oos = [
        "Lionel Messi kaç Ballon d'Or kazandı?",
        "En iyi sushi tarifi nedir?",
        "Kuantum mekaniğinde Schrödinger denklemi ne işe yarar?",
    ]
    g_guarded = 0
    for q in gundem_oos:
        runner.info(f"[Gündem OOS] {q}")
        try:
            docs = g_retriever.invoke(q)
            ctx = format_gundem_docs(docs) if docs else "(bağlam yok)"
            ans = g_chain.invoke({"context": ctx, "question": q})
        except Exception as e:
            runner.check(f"Gündem chain crash — {type(e).__name__}", False, str(e)[:80])
            continue
        guarded = _is_guarded(ans)
        if guarded:
            g_guarded += 1
        runner.check(
            f"[Gündem] '{q[:35]}...' → guard",
            guarded,
            f"yanıt ilk 120: {(ans or '')[:120]!r}",
        )
    runner.check(
        f"Gündem OOS guard oranı ≥ 2/{len(gundem_oos)}",
        g_guarded >= 2,
        f"{g_guarded}/{len(gundem_oos)}",
    )

    return runner.summary()


if __name__ == "__main__":
    sys.exit(main())
