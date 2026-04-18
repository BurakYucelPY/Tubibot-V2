import os

from src.retrieval.retriever import _build_retriever

# Sorgu anahtar kelimelerine göre belge türü eşleme — ana PDF DB için.
QUERY_TYPE_HINTS_PDF = {
    "basvuru_kosullari": ["başvur", "kimler", "kimler başvurabilir", "şart", "koşul", "uygunluk", "hak kazan"],
    "cagri_duyurusu": ["bütçe", "limit", "süre", "takvim", "son tarih", "çağrı", "duyuru", "destek"],
    "ska_rehberi": ["ska", "sürdürülebilir", "kalkınma", "hedef", "amaç", "gösterge"],
    "oncelikli_alanlar": ["öncelikli", "alan", "öncelikli alan", "tema"],
    "basvuru_formu": ["form", "öner", "araştırma önerisi", "yazım"],
}


def get_retriever():
    """Ana PDF DB için hybrid retriever — 2209-A/SKA içerik.

    Varsayılan davranış: sibling expansion açık, kaynak başına limit yok.
    """
    _backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    persist_directory = os.path.join(_backend_root, "data", "vector_db")
    return _build_retriever(persist_directory, QUERY_TYPE_HINTS_PDF)
