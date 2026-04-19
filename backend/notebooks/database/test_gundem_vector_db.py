"""
database/test_gundem_vector_db.py

Gündem Chroma DB (backend/data/gundem_vector_db) sağlık kontrolleri:
- Vektör sayısı > 0
- Her vektörde source_document, document_type dolu
- document_type ∈ {duyuru, haber}
- En az bir vektörde tarih + kaynak_url dolu
- section_heading = "Genel" baskın (gündem için her zaman)
"""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from _helpers.bootstrap import setup_backend_path
BACKEND_ROOT = setup_backend_path()

from _helpers.runner import TestRunner


def main():
    from langchain_chroma import Chroma
    from src.database.vector_store import E5Embeddings

    runner = TestRunner("database/test_gundem_vector_db")

    persist_dir = os.path.join(BACKEND_ROOT, "data", "gundem_vector_db")
    runner.check("gundem_vector_db dizini mevcut", os.path.isdir(persist_dir), persist_dir)

    if not os.path.isdir(persist_dir):
        runner.info("DB bulunamadı — önce build_gundem_vector_database() çalıştırın.")
        return runner.summary()

    embeddings = E5Embeddings(model_name="intfloat/multilingual-e5-large")
    db = Chroma(persist_directory=persist_dir, embedding_function=embeddings)

    total = db._collection.count()
    runner.info(f"Toplam vektör sayısı: {total}")
    runner.check("Vektör sayısı > 0", total > 0, f"{total} vektör")

    if total == 0:
        return runner.summary()

    # Tüm metadata'ları al
    all_data = db.get(include=["metadatas"])
    metas = all_data["metadatas"]

    # source_document ve document_type
    all_have_source = all(m.get("source_document") for m in metas)
    all_have_type = all(m.get("document_type") for m in metas)
    runner.check("Tüm vektörlerde source_document dolu", all_have_source)
    runner.check("Tüm vektörlerde document_type dolu", all_have_type)

    # document_type dağılımı
    type_counts = {}
    for m in metas:
        t = m.get("document_type", "?")
        type_counts[t] = type_counts.get(t, 0) + 1
    runner.info(f"document_type dağılımı: {type_counts}")

    allowed = {"duyuru", "haber"}
    only_expected = all(m.get("document_type") in allowed for m in metas)
    runner.check("Tüm doküman tipleri ∈ {duyuru, haber}", only_expected)

    # En az bir vektör tam metadata (tarih + kaynak_url)
    has_full = any(m.get("tarih") and m.get("kaynak_url") for m in metas)
    runner.check("En az bir vektörde tarih + kaynak_url dolu", has_full)

    # section_heading
    genel_count = sum(1 for m in metas if m.get("section_heading") == "Genel")
    runner.check(
        "section_heading='Genel' baskın (>%90)",
        genel_count / total > 0.9,
        f"{genel_count}/{total} = {genel_count*100//total}%",
    )

    # Retrieval sanity: basit bir sorgu çalışır mı?
    sample_results = db.similarity_search("son duyurular", k=3)
    runner.check(
        "similarity_search('son duyurular') sonuç döner",
        len(sample_results) > 0,
        f"{len(sample_results)} sonuç",
    )

    return runner.summary()


if __name__ == "__main__":
    sys.exit(main())
