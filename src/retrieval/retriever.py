import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

# ====================================================================
# Gelişmiş Retriever Pipeline:
# 1. Semantic Search (ChromaDB) — anlamsal benzerlik
# 2. BM25 Keyword Search — terim eşleşmesi
# 3. Reciprocal Rank Fusion (RRF) — birleştirme + deduplication
# ====================================================================

def _load_vector_db_and_docs():
    """ChromaDB'den vektör DB ve tüm dokümanları yükle."""
    # Türkçe başarısı çok daha yüksek olan modele geçiş (Plan Adım 2)
    model_name = "intfloat/multilingual-e5-large"
    embeddings = HuggingFaceEmbeddings(model_name=model_name)
    persist_directory = "data/vector_db"
    
    vector_db = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )
    
    # BM25 indeksi için tüm dokümanları al
    all_data = vector_db.get(include=["documents", "metadatas"])
    
    documents = []
    for i in range(len(all_data["documents"])):
        doc = Document(
            page_content=all_data["documents"][i],
            metadata=all_data["metadatas"][i] if all_data["metadatas"] else {}
        )
        documents.append(doc)
    
    return vector_db, embeddings, documents


def _merge_results(vector_docs, bm25_docs, vector_weight=0.6, bm25_weight=0.4):
    """
    İki retriever'ın sonuçlarını birleştir ve deduplicate et.
    Reciprocal Rank Fusion (RRF) benzeri basit bir skor birleştirme.
    """
    doc_scores = {}  # page_content hash -> (score, doc)
    
    # Vektör sonuçları (sıralamaya göre skor ver)
    for rank, doc in enumerate(vector_docs):
        key = hash(doc.page_content)
        score = vector_weight * (1.0 / (rank + 1))
        if key in doc_scores:
            doc_scores[key] = (doc_scores[key][0] + score, doc)
        else:
            doc_scores[key] = (score, doc)
    
    # BM25 sonuçları (sıralamaya göre skor ver)
    for rank, doc in enumerate(bm25_docs):
        key = hash(doc.page_content)
        score = bm25_weight * (1.0 / (rank + 1))
        if key in doc_scores:
            doc_scores[key] = (doc_scores[key][0] + score, doc)
        else:
            doc_scores[key] = (score, doc)
    
    # Skorlara göre sırala
    sorted_docs = sorted(doc_scores.values(), key=lambda x: x[0], reverse=True)
    return [doc for _, doc in sorted_docs]


def get_retriever():
    """
    Hybrid retriever döndürür: BM25 + Vektör (Reciprocal Rank Fusion).
    """
    vector_db, embeddings, all_documents = _load_vector_db_and_docs()
    
    # 1. Vektör (Semantic) Retriever
    vector_retriever = vector_db.as_retriever(search_kwargs={"k": 10})
    
    # 2. BM25 (Keyword) Retriever
    bm25_retriever = BM25Retriever.from_documents(all_documents, k=10)
    
    class HybridRetriever:
        """BM25 + Vektör arama birleşimi (RRF)."""
        
        def __init__(self, vector_ret, bm25_ret, top_k=5):
            self.vector_ret = vector_ret
            self.bm25_ret = bm25_ret
            self.top_k = top_k
        
        def invoke(self, query, config=None):
            vector_results = self.vector_ret.invoke(query)
            bm25_results = self.bm25_ret.invoke(query)
            merged = _merge_results(vector_results, bm25_results)
            return merged[:self.top_k]
        
        def get_relevant_documents(self, query):
            return self.invoke(query)
    
    return HybridRetriever(vector_retriever, bm25_retriever, top_k=5)


if __name__ == "__main__":
    print("\n[INFO] Gelişmiş Hybrid Retriever test ediliyor...")
    
    arama_motoru = get_retriever()
    
    soru = "2209-A projesine kimler başvuru yapabilir? Hangi bölüm veya sınıf öğrencileri başvurmaya hak kazanır?"
    print(f"\n[SORU] {soru}")
    print("=" * 60)
    
    bulunan_belgeler = arama_motoru.invoke(soru)
    
    for i, belge in enumerate(bulunan_belgeler, 1):
        source = belge.metadata.get("source_document", "Bilinmeyen")
        section = belge.metadata.get("section_heading", "")
        print(f"\n[KAYNAK {i}] ({source} | {section})")
        print(belge.page_content[:200])
        print("-" * 60)