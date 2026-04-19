"""
retrieval/test_retriever_pdf.py

PDF retriever factory uçtan uca davranış:
- get_retriever() bir HybridRetriever dönüyor mu?
- "2209-A'ya kimler başvurabilir?" → sonuç listesi dolu, ilgili kaynaklar geliyor
- Sibling expansion açık (aynı source_document'ten ≥ 2 chunk)
- max_per_source=None (ana PDF retriever'da limit yok)

Live: backend/data/vector_db kullanılır. İlk çağrıda cross-encoder yüklenir (~15sn).
"""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from _helpers.bootstrap import setup_backend_path
setup_backend_path()

from _helpers.runner import TestRunner


def main():
    from src.retrieval.retriever import HybridRetriever
    from src.retrieval.retriever_pdf import QUERY_TYPE_HINTS_PDF, get_retriever

    runner = TestRunner("retrieval/test_retriever_pdf")

    retriever = get_retriever()
    runner.check("get_retriever() HybridRetriever instance'ı döner", isinstance(retriever, HybridRetriever))
    runner.check("max_per_source=None (limit yok)", retriever.max_per_source is None)
    runner.check("sibling_expansion açık", retriever.sibling_expansion is True)
    runner.check(
        "hints_map PDF hints ile aynı",
        retriever.hints_map is QUERY_TYPE_HINTS_PDF,
    )

    # --- Gerçek sorgular ---
    soru1 = "2209-A'ya kimler başvurabilir?"
    runner.info(f"Sorgu: {soru1}")
    docs1 = retriever.invoke(soru1)
    runner.check("Sorgu 1 sonuçları var", len(docs1) > 0, f"{len(docs1)} chunk")

    sources1 = [d.metadata.get("source_document") for d in docs1]
    runner.info(f"İlk 5 kaynak: {sources1[:5]}")
    has_basvuru = any(
        "2209-A" in (s or "") or "Başvur" in (s or "") or "Kimler" in (s or "")
        for s in sources1
    )
    runner.check(
        "İlk sonuçlar 2209-A / başvuru belgeleri içeriyor",
        has_basvuru,
    )

    # Sibling expansion kanıtı: aynı source'tan en az 2 chunk dönmeli
    source_counts = {}
    for s in sources1:
        source_counts[s] = source_counts.get(s, 0) + 1
    max_per = max(source_counts.values()) if source_counts else 0
    runner.check(
        "Sibling expansion: aynı kaynaktan ≥ 2 chunk",
        max_per >= 2,
        f"en yoğun kaynak: {max_per}",
    )

    # --- İkinci sorgu: SKA ---
    soru2 = "SKA 13 iklim hedefleri nelerdir?"
    runner.info(f"Sorgu: {soru2}")
    docs2 = retriever.invoke(soru2)
    runner.check("SKA sorgusu sonuçları var", len(docs2) > 0, f"{len(docs2)} chunk")
    sources2 = [d.metadata.get("source_document", "") for d in docs2]
    has_ska = any("SKA" in s or "Sürdürülebilir" in s for s in sources2)
    runner.check("SKA sorgusu ilgili kaynak döndü", has_ska, f"ilk kaynak: {sources2[0] if sources2 else 'YOK'}")

    return runner.summary()


if __name__ == "__main__":
    sys.exit(main())
