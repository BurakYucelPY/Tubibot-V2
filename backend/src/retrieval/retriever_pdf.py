import os

from src.retrieval.retriever import _build_retriever

# Sorgu anahtar kelimelerine göre belge türü eşleme — ana PDF DB için.
QUERY_TYPE_HINTS_PDF = {
    # Mevcut (korunur):
    "basvuru_kosullari": ["başvur", "kimler", "kimler başvurabilir", "şart", "koşul", "uygunluk", "hak kazan", "eş zamanlı"],
    "cagri_duyurusu":    ["bütçe", "limit", "süre", "takvim", "son tarih", "çağrı", "duyuru", "destek"],
    "ska_rehberi":       ["ska", "sürdürülebilir", "kalkınma", "hedef", "amaç", "gösterge"],
    "oncelikli_alanlar": ["öncelikli", "alan", "öncelikli alan", "tema"],
    "basvuru_formu":     ["form", "öner", "araştırma önerisi", "yazım"],
    # YENİ (TübitakBilgi_pdf genişletmesi):
    "ardeb_1001_basvuru":       ["1001", "ardeb", "araştırma projesi", "temel bilim"],
    "ardeb_1002_basvuru":       ["1002", "hızlı destek", "acil destek", "hızlı modül"],
    "ardeb_proje_yonetmeligi":  ["görev limit", "proje yürütücü", "ardeb proje", "yönetmelik"],
    "bideb_burs_2211a":         ["2211", "doktora burs", "yurt içi burs", "doktora bursu"],
    "bideb_burs_2219":          ["2219", "doktora sonrası", "yurt dışı doktora", "post-doc"],
    "2209b_rehberi":            ["2209-b", "2209b", "üniversite sanayi", "sanayiye yönelik"],
    "teydeb_uygulama_esaslari": ["1501", "1507", "sanayi ar-ge", "kobi ar-ge", "uygulama esasları"],
    "teydeb_yonetmeligi":       ["teydeb", "teknoloji yenilik", "destek programları yönetmelik"],
    "mali_esaslar":             ["mali esas", "idari esas", "mali ve idari"],
    "mali_rapor_kilavuzu":      ["mali rapor", "rapor hazırlama", "gider formu", "mali müşavir"],
    "fikri_haklar":             ["fikri hak", "patent", "telif", "buluş"],
    "yazim_rehberi":            ["özgün değer", "konunun önemi", "nasıl yazılır", "yazım rehberi"],
    "stratejik_plan":           ["stratejik plan", "2024-2028", "stratejik amaç", "stratejik hedef"],
    "faaliyet_raporu":          ["faaliyet raporu", "2025 faaliyet", "yıllık rapor"],
}


def get_retriever():
    """Ana PDF DB için hybrid retriever — 31 PDF kapsamı (2209A_pdf + TübitakBilgi_pdf).

    max_per_source=3: 241 sayfalık Faaliyet Raporu veya 202 sayfalık Stratejik Plan
    gibi büyük dosyaların tek bir sorguda top_k'nın tamamını ele geçirmesini önler.
    sibling_expansion=True: liste/tablo bütünlüğünü korumak için aynı kaynaktan
    ek chunk'ları ekler.
    """
    _backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    persist_directory = os.path.join(_backend_root, "data", "vector_db")
    return _build_retriever(
        persist_directory,
        QUERY_TYPE_HINTS_PDF,
        max_per_source=3,
        sibling_expansion=True,
    )
