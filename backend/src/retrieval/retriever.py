import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from TurkishStemmer import TurkishStemmer
from sentence_transformers import CrossEncoder

from src.database.vector_store import E5Embeddings

# ====================================================================
# Ortak (koordinatör) retriever modülü:
# 1. Semantic Search (ChromaDB) — anlamsal benzerlik
# 2. BM25 Keyword Search — terim eşleşmesi + Türkçe stopword
# 3. Reciprocal Rank Fusion (RRF) — birleştirme + deduplication
# 4. Cross-encoder reranker ile nihai yeniden sıralama
#
# Domain factory'leri ayrı dosyalarda:
# - retriever_pdf.py     → get_retriever()
# - retriever_gundem.py  → get_gundem_retriever()
#
# Dışarıya yönelik import sözleşmesi korunur (re-export dosya sonunda).
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


def _load_vector_db_and_docs(persist_directory):
    """Verilen Chroma persist dizininden vektör DB'yi + tüm Document'ları yükler."""
    model_name = "intfloat/multilingual-e5-large"
    embeddings = E5Embeddings(model_name=model_name)

    vector_db = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
    )

    all_data = vector_db.get(include=["documents", "metadatas"])

    documents = []
    for i in range(len(all_data["documents"])):
        doc = Document(
            page_content=all_data["documents"][i],
            metadata=all_data["metadatas"][i] if all_data["metadatas"] else {},
        )
        documents.append(doc)

    return vector_db, embeddings, documents


def _merge_results(vector_docs, bm25_docs):
    """İki retriever sonucunu RRF (k=60) ile birleştir ve deduplicate et."""
    doc_scores = {}
    K = 60

    for rank, doc in enumerate(vector_docs):
        key = hash(doc.page_content)
        score = 1.0 / (K + rank)
        if key in doc_scores:
            doc_scores[key] = (doc_scores[key][0] + score, doc)
        else:
            doc_scores[key] = (score, doc)

    for rank, doc in enumerate(bm25_docs):
        key = hash(doc.page_content)
        score = 1.0 / (K + rank)
        if key in doc_scores:
            doc_scores[key] = (doc_scores[key][0] + score, doc)
        else:
            doc_scores[key] = (score, doc)

    sorted_docs = sorted(doc_scores.values(), key=lambda x: x[0], reverse=True)
    return [doc for _, doc in sorted_docs]


def _detect_query_type_hints(query, hints_map):
    """Sorgu metnindeki anahtar kelimelere göre ilgili belge türlerini tespit et."""
    query_lower = query.lower()
    matched_types = set()
    for doc_type, keywords in hints_map.items():
        for keyword in keywords:
            if keyword in query_lower:
                matched_types.add(doc_type)
                break
    return matched_types


# Cross-encoder reranker'ı modül seviyesinde cache'le — iki factory paylaşsın
_reranker_cache = None


def _get_reranker():
    global _reranker_cache
    if _reranker_cache is None:
        print("[INFO] Cross-encoder reranker yükleniyor...")
        _reranker_cache = CrossEncoder("BAAI/bge-reranker-v2-m3")
    return _reranker_cache


class HybridRetriever:
    """BM25 + Vektör (RRF) + metadata boost + cross-encoder reranking + sibling expansion."""

    def __init__(
        self,
        vector_ret,
        bm25_ret,
        reranker_model,
        all_docs,
        hints_map,
        top_k=8,
        max_per_source=None,
        sibling_expansion=True,
    ):
        self.vector_ret = vector_ret
        self.bm25_ret = bm25_ret
        self.reranker = reranker_model
        self.all_docs = all_docs
        self.hints_map = hints_map
        self.top_k = top_k
        self.max_per_source = max_per_source
        self.sibling_expansion = sibling_expansion

    def _apply_per_source_cap(self, ranked_docs):
        """Aynı source_document'tan en fazla max_per_source chunk al."""
        if self.max_per_source is None:
            return ranked_docs
        counts = {}
        out = []
        for doc in ranked_docs:
            src = doc.metadata.get("source_document", "__unknown__")
            if counts.get(src, 0) >= self.max_per_source:
                continue
            counts[src] = counts.get(src, 0) + 1
            out.append(doc)
        return out

    def _expand_siblings(self, results, max_total=12):
        """Aynı source_document'ten diğer chunk'ları ekle — liste/tablo bütünlüğü."""
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
        vector_results = self.vector_ret.invoke(query)
        bm25_results = self.bm25_ret.invoke(query)
        merged = _merge_results(vector_results, bm25_results)

        type_hints = _detect_query_type_hints(query, self.hints_map)
        if type_hints:
            boosted = []
            rest = []
            for doc in merged:
                if doc.metadata.get("document_type") in type_hints:
                    boosted.append(doc)
                else:
                    rest.append(doc)
            merged = boosted + rest

        candidate_pool = self.top_k * 4 if self.max_per_source else self.top_k * 2
        candidates = merged[:candidate_pool]
        if candidates:
            pairs = [[query, doc.page_content] for doc in candidates]
            scores = self.reranker.predict(pairs)
            scored_docs = sorted(zip(scores, candidates), key=lambda x: x[0], reverse=True)
            ranked = [doc for _, doc in scored_docs]
        else:
            ranked = merged

        ranked = self._apply_per_source_cap(ranked)
        results = ranked[:self.top_k]

        if self.sibling_expansion:
            results = self._expand_siblings(results)
        return results

    def get_relevant_documents(self, query):
        return self.invoke(query)


def _build_retriever(
    persist_directory,
    hints_map,
    top_k=8,
    bm25_k=10,
    vector_k=10,
    max_per_source=None,
    sibling_expansion=True,
):
    """Ortak factory: verilen Chroma DB + hint'ler için HybridRetriever kurar."""
    vector_db, _embeddings, all_documents = _load_vector_db_and_docs(persist_directory)

    vector_retriever = vector_db.as_retriever(search_kwargs={"k": vector_k})

    stemmer = TurkishStemmer()

    def turkish_preprocessor(text):
        tokens = text.lower().split()
        return [stemmer.stem(t) for t in tokens if t not in TURKISH_STOPWORDS]

    bm25_retriever = BM25Retriever.from_documents(
        all_documents,
        k=bm25_k,
        preprocess_func=turkish_preprocessor,
    )

    reranker = _get_reranker()

    return HybridRetriever(
        vector_ret=vector_retriever,
        bm25_ret=bm25_retriever,
        reranker_model=reranker,
        all_docs=all_documents,
        hints_map=hints_map,
        top_k=top_k,
        max_per_source=max_per_source,
        sibling_expansion=sibling_expansion,
    )


# Aşağıdaki re-export'lar DOSYANIN SONUNDA olmalı — circular import için kritik.
# retriever_pdf / retriever_gundem modülleri yukarıdaki _build_retriever'ı import ediyor;
# onu buradan re-export etmek için tanımın tamamlanmış olması gerekir.
from src.retrieval.retriever_pdf import get_retriever  # noqa: E402, F401
from src.retrieval.retriever_gundem import get_gundem_retriever  # noqa: E402, F401


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
