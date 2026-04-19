"""
retrieval/test_query_type_hints.py

_detect_query_type_hints pure logic testi:
- PDF QUERY_TYPE_HINTS_PDF haritası ile 2209-A başvuru sorusu → basvuru_kosullari
- SKA / iklim soruları → ska_rehberi
- Gündem QUERY_TYPE_HINTS_GUNDEM ile "son duyuru" → duyuru; "ödül haberi" → haber
- Alakasız selamlama → boş küme

Mock/fixture yok — saf string eşleme mantığı.
"""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from _helpers.bootstrap import setup_backend_path
setup_backend_path()

from _helpers.runner import TestRunner


def main():
    from src.retrieval.retriever import _detect_query_type_hints
    from src.retrieval.retriever_pdf import QUERY_TYPE_HINTS_PDF
    from src.retrieval.retriever_gundem import QUERY_TYPE_HINTS_GUNDEM

    runner = TestRunner("retrieval/test_query_type_hints")

    # --- PDF tarafı ---
    cases_pdf = [
        ("2209-A'ya kimler başvurabilir?", "basvuru_kosullari"),
        ("2209-A bütçe limiti ne kadar?", "cagri_duyurusu"),
        ("SKA hedefleri nelerdir?", "ska_rehberi"),
        ("İklim ile ilgili öncelikli alan hangisi?", "oncelikli_alanlar"),
        ("Araştırma önerisi formu nasıl doldurulur?", "basvuru_formu"),
    ]
    for query, expected in cases_pdf:
        hints = _detect_query_type_hints(query, QUERY_TYPE_HINTS_PDF)
        runner.check(
            f"PDF hint: {query!r} → {expected}",
            expected in hints,
            f"bulunan: {hints}",
        )

    # Alakasız selamlama
    empty = _detect_query_type_hints("merhaba", QUERY_TYPE_HINTS_PDF)
    runner.check(
        "Selamlama: hiçbir PDF hint üretmedi",
        len(empty) == 0,
        f"bulunan: {empty}",
    )

    # --- Gündem tarafı ---
    cases_gundem = [
        ("Son çağrı ne zaman açıldı?", "duyuru"),
        ("Teknofest yarışma sonuçları", "haber"),
        ("Yeni başvuru tarihi var mı?", "duyuru"),
        ("Ödül töreni ne zaman?", "haber"),
    ]
    for query, expected in cases_gundem:
        hints = _detect_query_type_hints(query, QUERY_TYPE_HINTS_GUNDEM)
        runner.check(
            f"Gündem hint: {query!r} → {expected}",
            expected in hints,
            f"bulunan: {hints}",
        )

    # Query case-insensitive
    hints_upper = _detect_query_type_hints("ÖDÜL TÖRENİ NE ZAMAN?", QUERY_TYPE_HINTS_GUNDEM)
    runner.check(
        "Büyük harf sorgu da case-insensitive eşleşir",
        "haber" in hints_upper,
        f"bulunan: {hints_upper}",
    )

    return runner.summary()


if __name__ == "__main__":
    sys.exit(main())
