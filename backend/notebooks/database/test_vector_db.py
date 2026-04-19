"""
TEST 3: Vektör DB Metadata Kontrolü
Vektör veritabanındaki chunk'larda metadata bilgisinin doğru şekilde bulunup bulunmadığını test eder.
"""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from _helpers.bootstrap import setup_backend_path
BACKEND_ROOT = setup_backend_path()

PASS = "✅ GEÇTI"
FAIL = "❌ BASARISIZ"


def test_vector_db_metadata():
    """Vektör DB'deki chunk'larda metadata var mı?"""
    print("\n" + "="*60)
    print("TEST 3: Vektör DB Metadata Kontrolü")
    print("="*60)
    from langchain_chroma import Chroma
    from src.database.vector_store import E5Embeddings

    embeddings = E5Embeddings(model_name="intfloat/multilingual-e5-large")
    vector_db = Chroma(persist_directory=os.path.join(BACKEND_ROOT, "data", "vector_db"), embedding_function=embeddings)
    
    sample = vector_db.get(limit=10, include=["metadatas"])
    
    total = vector_db._collection.count()
    print(f"  Toplam chunk sayısı: {total}")
    
    # Her chunk'ta source_document ve document_type olmalı
    meta_ok = True
    types_found = set()
    for m in sample["metadatas"]:
        if "source_document" not in m or "document_type" not in m:
            meta_ok = False
        types_found.add(m.get("document_type", ""))
    
    print(f"  {PASS if meta_ok else FAIL} Tüm chunk'larda source_document ve document_type var")
    print(f"  Bulunan belge türleri: {types_found}")
    
    # section_heading kontrolü
    has_heading = any("section_heading" in m for m in sample["metadatas"])
    print(f"  {PASS if has_heading else FAIL} Chunk'larda section_heading metadata'sı var")
    
    result = meta_ok and has_heading
    print(f"\n  {'🎉 TEST BAŞARILI!' if result else '⚠️ TEST BAŞARISIZ!'}")
    return result


if __name__ == "__main__":
    test_vector_db_metadata()
