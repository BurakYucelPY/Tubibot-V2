"""
ingestion/test_json_loader.py

json_loader.py duyurular.json + haberler.json'ı okuyup Document listesine
dönüştürüyor mu? HTML temizliği, tarih ayrıştırma ve metadata zenginleştirme
çalışıyor mu?
"""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from _helpers.bootstrap import setup_backend_path
BACKEND_ROOT = setup_backend_path()

from _helpers.runner import TestRunner


def main():
    from src.ingestion.json_loader import (
        _html_to_text,
        _parse_year,
        load_gundem_documents,
        load_json_entries,
    )

    runner = TestRunner("ingestion/test_json_loader")

    # --- _parse_year ---
    runner.check("_parse_year('12 Mart 2025') == '2025'", _parse_year("12 Mart 2025") == "2025")
    runner.check("_parse_year('') boş döner", _parse_year("") == "")
    runner.check("_parse_year(None) boş döner", _parse_year(None) == "")
    runner.check("_parse_year bozuk format boş döner", _parse_year("bugün") == "")

    # --- _html_to_text ---
    plain = _html_to_text("<p>Merhaba <b>dünya</b></p>")
    runner.check(
        "HTML etiketleri temizleniyor",
        "Merhaba" in plain and "dünya" in plain and "<" not in plain,
        repr(plain),
    )
    runner.check("_html_to_text('') boş string döner", _html_to_text("") == "")
    runner.check("_html_to_text(None) boş string döner", _html_to_text(None) == "")

    collapsed = _html_to_text("<p>a</p>\n\n\n\n\n<p>b</p>")
    runner.check(
        "Ardışık boş satırlar daraltılıyor (max 2 newline)",
        "\n\n\n" not in collapsed,
        repr(collapsed),
    )

    # --- load_json_entries: bilinmeyen yol graceful ---
    empty = load_json_entries("/kesinlikle/var/olmayan/dosya.json", "duyuru")
    runner.check("Olmayan JSON için boş liste", isinstance(empty, list) and len(empty) == 0)

    # --- load_gundem_documents: gerçek dosyalar ---
    duyurular_path = os.path.join(BACKEND_ROOT, "duyurular.json")
    haberler_path = os.path.join(BACKEND_ROOT, "haberler.json")

    has_duyurular = os.path.exists(duyurular_path)
    has_haberler = os.path.exists(haberler_path)
    runner.info(f"duyurular.json: {'VAR' if has_duyurular else 'YOK'} | haberler.json: {'VAR' if has_haberler else 'YOK'}")

    docs = load_gundem_documents(BACKEND_ROOT)
    runner.check(
        "load_gundem_documents() bir liste döner",
        isinstance(docs, list),
    )

    if has_duyurular or has_haberler:
        runner.check("Yüklenen doküman sayısı > 0", len(docs) > 0, f"{len(docs)} belge")

        type_counts = {}
        for d in docs:
            t = d.metadata.get("document_type", "?")
            type_counts[t] = type_counts.get(t, 0) + 1
        runner.info(f"document_type dağılımı: {type_counts}")

        allowed_types = {"duyuru", "haber"}
        all_correct_type = all(d.metadata.get("document_type") in allowed_types for d in docs)
        runner.check(
            "Tüm doküman tipleri duyuru/haber",
            all_correct_type,
        )

        # En az bir doküman tam metadata içerir
        has_full_meta = any(
            d.metadata.get("baslik")
            and d.metadata.get("kaynak_url")
            and d.metadata.get("tarih")
            for d in docs
        )
        runner.check(
            "En az bir doküman baslik + kaynak_url + tarih dolu",
            has_full_meta,
        )

        # page_content boş olmamalı
        empty_contents = sum(1 for d in docs if not d.page_content.strip())
        runner.check(
            "Boş içerikli doküman yok",
            empty_contents == 0,
            f"{empty_contents} boş" if empty_contents else "hepsi dolu",
        )

    return runner.summary()


if __name__ == "__main__":
    sys.exit(main())
