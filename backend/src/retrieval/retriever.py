import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from TurkishStemmer import TurkishStemmer
from sentence_transformers import CrossEncoder
from src.database.vector_store import E5Embeddings

# ====================================================================
# Gelişmiş Retriever Pipeline:
# 1. Semantic Search (ChromaDB) — anlamsal benzerlik
# 2. BM25 Keyword Search — terim eşleşmesi + Türkçe stopword
# 3. Reciprocal Rank Fusion (RRF) — birleştirme + deduplication
# ====================================================================

# Türkçe stopword listesi — BM25 skorlamasını anlamsız kelimelerin domine etmesini önler
TURKISH_STOPWORDS = {
    "bir", "ve", "ile", "için", "bu", "da", "de", "den", "dan", "ne", "olan",
    "var", "yok", "daha", "çok", "en", "o", "her", "ise", "gibi", "kadar",
    "sonra", "önce", "aynı", "ancak", "ama", "fakat", "veya", "ya", "hem",
    "ki", "mi", "mu", "mı", "mü", "dir", "dır", "dur", "dür", "tir", "tır",
    "tur", "tür", "ler", "lar", "nin", "nın", "nun", "nün", "den", "dan",
    "ten", "tan", "ini", "ını", "unu", "ünü", "ye", "ya", "ta", "te",
    "olan", "olarak", "olup", "olan", "üzere", "dolayı", "göre", "karşı",
    "arasında", "içinde", "dışında", "hakkında", "ilgili", "bağlı",
    "şekilde", "olarak", "tarafından", "birlikte", "beraber",
    "ben", "sen", "biz", "siz", "onlar", "bunlar", "şunlar",
    "nasıl", "neden", "nerede", "hangi", "kendi", "bütün", "tüm",
    "bazı", "birçok", "hiçbir", "hiç", "bile", "sadece", "yalnız",
    "ise", "iken", "olduğu", "olduğunu", "edilir", "edilmiş", "yapılır",
    "yapılan", "yapılacak", "edilen", "edecek", "olacak", "olması",
}


def _load_vector_db_and_docs():
    """ChromaDB'den vektör DB ve tüm dokümanları yükle."""
    model_name = "intfloat/multilingual-e5-large"
    embeddings = E5Embeddings(model_name=model_name)
    persist_directory = "backend/data/vector_db"

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


def _merge_results(vector_docs, bm25_docs):
    """
    İki retriever'ın sonuçlarını birleştir ve deduplicate et.
    Reciprocal Rank Fusion (RRF) (k=60) ile adil skor birleştirme.
    """
    doc_scores = {}  # page_content hash -> (score, doc)
    K = 60

    # Vektör sonuçları (sıralamaya göre RRF)
    for rank, doc in enumerate(vector_docs):
        key = hash(doc.page_content)
        score = 1.0 / (K + rank)
        if key in doc_scores:
            doc_scores[key] = (doc_scores[key][0] + score, doc)
        else:
            doc_scores[key] = (score, doc)

    # BM25 sonuçları (sıralamaya göre RRF)
    for rank, doc in enumerate(bm25_docs):
        key = hash(doc.page_content)
        score = 1.0 / (K + rank)
        if key in doc_scores:
            doc_scores[key] = (doc_scores[key][0] + score, doc)
        else:
            doc_scores[key] = (score, doc)

    # Skorlara göre sırala
    sorted_docs = sorted(doc_scores.values(), key=lambda x: x[0], reverse=True)
    return [doc for _, doc in sorted_docs]


# Sorgu anahtar kelimelerine göre belge türü eşleme
# Eşleşme varsa, o türdeki chunk'lar RRF skorunda boost alır.
QUERY_TYPE_HINTS = {
    "basvuru_kosullari": ["başvur", "kimler", "kimler başvurabilir", "şart", "koşul", "uygunluk", "hak kazan"],
    "cagri_duyurusu": ["bütçe", "limit", "süre", "takvim", "son tarih", "çağrı", "duyuru", "destek"],
    "ska_rehberi": ["ska", "sürdürülebilir", "kalkınma", "hedef", "amaç", "gösterge"],
    "oncelikli_alanlar": ["öncelikli", "alan", "öncelikli alan", "tema"],
    "basvuru_formu": ["form", "öner", "araştırma önerisi", "yazım"],
}


def _detect_query_type_hints(query):
    """Sorgu metnindeki anahtar kelimelere göre ilgili belge türlerini tespit et."""
    query_lower = query.lower()
    matched_types = set()
    for doc_type, keywords in QUERY_TYPE_HINTS.items():
        for keyword in keywords:
            if keyword in query_lower:
                matched_types.add(doc_type)
                break
    return matched_types


def get_retriever():
    """
    Hybrid retriever döndürür: BM25 + Vektör (Reciprocal Rank Fusion).
    Metadata bazlı boost ile ilgili belge türleri öne çıkarılır.
    """
    vector_db, embeddings, all_documents = _load_vector_db_and_docs()

    # 1. Vektör (Semantic) Retriever
    vector_retriever = vector_db.as_retriever(search_kwargs={"k": 10})

    # Türkçe Kök Bulma + Stopword Kaldırma Ön İşlemcisi
    stemmer = TurkishStemmer()

    def turkish_preprocessor(text):
        tokens = text.lower().split()
        return [stemmer.stem(t) for t in tokens if t not in TURKISH_STOPWORDS]

    # 2. BM25 (Keyword) Retriever
    bm25_retriever = BM25Retriever.from_documents(
        all_documents,
        k=10,
        preprocess_func=turkish_preprocessor
    )

    # 3. Cross-Encoder Reranker
    print("[INFO] Cross-encoder reranker yükleniyor...")
    reranker = CrossEncoder("BAAI/bge-reranker-v2-m3")

    class HybridRetriever:
        """BM25 + Vektör (RRF) + metadata boost + cross-encoder reranking + sibling expansion."""

        def __init__(self, vector_ret, bm25_ret, reranker_model, all_docs, top_k=8):
            self.vector_ret = vector_ret
            self.bm25_ret = bm25_ret
            self.reranker = reranker_model
            self.all_docs = all_docs
            self.top_k = top_k

        def _expand_siblings(self, results, max_total=12):
            """
            Sonuçlardaki belgelerin kardeş chunk'larını dahil et.
            Bir belgenin bir chunk'ı bulunduysa, aynı source_document'tan
            diğer chunk'ları da ekle — liste/tablo bütünlüğünü sağlar.
            """
            existing_keys = {hash(d.page_content) for d in results}
            sources_in_results = {d.metadata.get("source_document") for d in results}

            siblings = []
            for doc in self.all_docs:
                src = doc.metadata.get("source_document")
                key = hash(doc.page_content)
                if src in sources_in_results and key not in existing_keys:
                    siblings.append(doc)
                    existing_keys.add(key)

            return (results + siblings)[:max_total]

        def invoke(self, query, config=None):
            # E5Embeddings "query: " prefix'ini otomatik ekler
            vector_results = self.vector_ret.invoke(query)
            bm25_results = self.bm25_ret.invoke(query)
            merged = _merge_results(vector_results, bm25_results)

            # Metadata bazlı boost: sorguyla ilgili belge türlerini öne çıkar
            type_hints = _detect_query_type_hints(query)
            if type_hints:
                boosted = []
                rest = []
                for doc in merged:
                    if doc.metadata.get("document_type") in type_hints:
                        boosted.append(doc)
                    else:
                        rest.append(doc)
                merged = boosted + rest

            # Cross-encoder ile nihai yeniden sıralama (top_k * 2 aday üzerinde)
            candidates = merged[:self.top_k * 2]
            if candidates:
                pairs = [[query, doc.page_content] for doc in candidates]
                scores = self.reranker.predict(pairs)
                scored_docs = sorted(zip(scores, candidates), key=lambda x: x[0], reverse=True)
                results = [doc for _, doc in scored_docs[:self.top_k]]
            else:
                results = merged[:self.top_k]

            # Sibling expansion: aynı belgeden eksik chunk'ları dahil et
            results = self._expand_siblings(results)
            return results

        def get_relevant_documents(self, query):
            return self.invoke(query)

    return HybridRetriever(vector_retriever, bm25_retriever, reranker, all_documents, top_k=8)


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
