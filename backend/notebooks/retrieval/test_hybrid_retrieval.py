"""
TEST 4: Hybrid Retrieval (BM25 + Vektör)
BM25 ve Vektör arama sonuçlarının hybrid olarak birleştirilmesini test eder.
"""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from _helpers.bootstrap import setup_backend_path
BACKEND_ROOT = setup_backend_path()

PASS = "✅ GEÇTI"
FAIL = "❌ BASARISIZ"


def test_hybrid_retrieval():
    """BM25 + Vektör hybrid arama gerçekten farklı sonuç getiriyor mu?"""
    print("\n" + "="*60)
    print("TEST 4: Hybrid Retrieval (BM25 + Vektör)")
    print("="*60)
    from src.retrieval.retriever import _load_vector_db_and_docs, _merge_results

    persist_dir = os.path.join(BACKEND_ROOT, "data", "vector_db")
    vector_db, embeddings, all_docs = _load_vector_db_and_docs(persist_dir)
    
    print(f"  BM25 indeksi için yüklenen doküman sayısı: {len(all_docs)}")
    docs_ok = len(all_docs) > 0
    print(f"  {PASS if docs_ok else FAIL} Dokümanlar yüklendi")
    
    # Vektör ve BM25'i ayrı çalıştır, sonuçları karşılaştır
    vector_retriever = vector_db.as_retriever(search_kwargs={"k": 5})
    
    from langchain_community.retrievers import BM25Retriever
    bm25_retriever = BM25Retriever.from_documents(all_docs, k=5)
    
    soru = "2209-A bütçe limiti"
    vec_results = vector_retriever.invoke(soru)
    bm25_results = bm25_retriever.invoke(soru)
    
    vec_contents = set(hash(d.page_content) for d in vec_results)
    bm25_contents = set(hash(d.page_content) for d in bm25_results)
    
    overlap = vec_contents & bm25_contents
    unique_bm25 = bm25_contents - vec_contents
    unique_vec = vec_contents - bm25_contents
    
    print(f"  Vektör sonuçları: {len(vec_results)}, BM25 sonuçları: {len(bm25_results)}")
    print(f"  Ortak: {len(overlap)}, Sadece BM25: {len(unique_bm25)}, Sadece Vektör: {len(unique_vec)}")
    
    # Merge testi
    merged = _merge_results(vec_results, bm25_results)
    merge_ok = len(merged) >= max(len(vec_results), len(bm25_results))
    print(f"  {PASS if merge_ok else FAIL} RRF merge doğru çalışıyor (merge sonucu: {len(merged)} unique chunk)")
    
    # Her iki kaynaktan farklı sonuçlar geliyorsa hybrid gerçekten işe yarıyor
    hybrid_useful = len(unique_bm25) > 0 or len(unique_vec) > 0
    print(f"  {PASS if hybrid_useful else '⚠️ BİLGİ'} BM25 ve Vektör farklı sonuçlar getiriyor (hybrid avantajı)")
    
    result = docs_ok and merge_ok
    print(f"\n  {'🎉 TEST BAŞARILI!' if result else '⚠️ TEST BAŞARISIZ!'}")
    return result


if __name__ == "__main__":
    test_hybrid_retrieval()
