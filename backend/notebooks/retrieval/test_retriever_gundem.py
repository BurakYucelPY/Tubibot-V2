"""
retrieval/test_retriever_gundem.py

Gündem retriever factory davranış farkları (vs. PDF retriever):
- max_per_source=2 (her duyuru/haberden en fazla 2 chunk)
- sibling_expansion=False
- vector_k=20, bm25_k=20 (geniş aday havuzu)
- "son duyurular" sorgusu kaynak çeşitliliği üretiyor mu?

Live: backend/data/gundem_vector_db kullanılır.
"""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from _helpers.bootstrap import setup_backend_path
BACKEND_ROOT = setup_backend_path()

from _helpers.runner import TestRunner


def main():
    from src.retrieval.retriever import HybridRetriever
    from src.retrieval.retriever_gundem import QUERY_TYPE_HINTS_GUNDEM, get_gundem_retriever

    runner = TestRunner("retrieval/test_retriever_gundem")

    persist_dir = os.path.join(BACKEND_ROOT, "data", "gundem_vector_db")
    runner.check("gundem_vector_db dizini mevcut", os.path.isdir(persist_dir))

    if not os.path.isdir(persist_dir):
        runner.info("DB yok — build_gundem_vector_database() çalıştırın.")
        return runner.summary()

    retriever = get_gundem_retriever()
    runner.check("get_gundem_retriever() HybridRetriever instance'ı döner", isinstance(retriever, HybridRetriever))
    runner.check("max_per_source == 2", retriever.max_per_source == 2)
    runner.check("sibling_expansion kapalı", retriever.sibling_expansion is False)
    runner.check("top_k == 8", retriever.top_k == 8)
    runner.check(
        "hints_map gündem hints ile aynı",
        retriever.hints_map is QUERY_TYPE_HINTS_GUNDEM,
    )

    # --- Gerçek sorgu ---
    soru = "Son açılan duyurular ve yeni çağrılar"
    runner.info(f"Sorgu: {soru}")
    docs = retriever.invoke(soru)
    runner.check("Sorgu sonuçları var", len(docs) > 0, f"{len(docs)} chunk")

    if not docs:
        return runner.summary()

    sources = [d.metadata.get("source_document") for d in docs]
    runner.info(f"Dönen kaynaklar: {list(set(sources))[:5]}")

    # max_per_source=2 sıkıştırması
    source_counts = {}
    for s in sources:
        source_counts[s] = source_counts.get(s, 0) + 1
    max_per = max(source_counts.values()) if source_counts else 0
    runner.check(
        "Aynı kaynaktan ≤ 2 chunk (per-source cap)",
        max_per <= 2,
        f"en yoğun kaynak: {max_per}",
    )

    # Kaynak çeşitliliği: ≥ 3 farklı source_document
    unique_sources = len(set(sources))
    runner.check(
        "Kaynak çeşitliliği ≥ 3 farklı source_document",
        unique_sources >= 3,
        f"{unique_sources} farklı kaynak",
    )

    # Her chunk'ın document_type ∈ {duyuru, haber}
    allowed = {"duyuru", "haber"}
    all_ok = all(d.metadata.get("document_type") in allowed for d in docs)
    runner.check("Tüm sonuçlar duyuru/haber tipinde", all_ok)

    return runner.summary()


if __name__ == "__main__":
    sys.exit(main())
