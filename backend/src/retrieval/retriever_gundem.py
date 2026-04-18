import os

from src.retrieval.retriever import _build_retriever

# Sorgu anahtar kelimelerine göre belge türü eşleme — gündem DB için.
QUERY_TYPE_HINTS_GUNDEM = {
    "duyuru": [
        "güncel", "yeni", "son çağrı", "açıldı", "hibe", "destek programı",
        "son başvuru", "başvuru tarihi", "teknofest", "yarışma", "program",
    ],
    "haber": [
        "etkinlik", "sonuç", "açıklandı", "duyuruldu", "haberi", "sonuçlar",
        "ödül", "tören", "ziyaret", "açıklama",
    ],
}


def get_gundem_retriever():
    """Gündem DB için hybrid retriever — scrape edilen duyuru + haber içerik.

    Çok sayıda kısa belge olduğundan kaynak çeşitliliği kritik:
    - max_per_source=2: her duyuru/haberden en fazla 2 chunk
    - sibling_expansion=False: tek duyuruya kilitlenmeyi önle
    - vector_k/bm25_k=20: daha geniş aday havuzu
    """
    _backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    persist_directory = os.path.join(_backend_root, "data", "gundem_vector_db")
    return _build_retriever(
        persist_directory,
        QUERY_TYPE_HINTS_GUNDEM,
        top_k=8,
        bm25_k=20,
        vector_k=20,
        max_per_source=2,
        sibling_expansion=False,
    )
