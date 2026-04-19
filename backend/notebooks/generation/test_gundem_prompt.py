"""
generation/test_gundem_prompt.py

api/formatters.py::format_gundem_docs + api/prompts.py::GUNDEM_PROMPT:
- Çıktı [DUYURU/HABER] etiketi + tarih + URL içeriyor mu?
- Birden fazla chunk "---" ayırıcı ile ayrılıyor mu?
- GUNDEM_SYSTEM_PROMPT halüsinasyon koruması içeriyor mu?
- "kaynaklar" listesi çıktı için teşvik ediliyor mu?
"""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from _helpers.bootstrap import setup_backend_path
setup_backend_path()

from _helpers.runner import TestRunner
from langchain_core.documents import Document


def main():
    from api.formatters import format_gundem_docs
    from api.prompts import GUNDEM_PROMPT, GUNDEM_SYSTEM_PROMPT

    runner = TestRunner("generation/test_gundem_prompt")

    duyuru_doc = Document(
        page_content="2209-A 2025 yılı başvuruları 1 Aralık'ta açılıyor.",
        metadata={
            "source_document": "2209-A 2025 Çağrı Açıldı",
            "document_type": "duyuru",
            "tarih": "10 Kasım 2025",
            "kaynak_url": "https://tubitak.gov.tr/duyuru/2209a-2025",
            "section_heading": "Genel",
        },
    )
    haber_doc = Document(
        page_content="TÜBİTAK Teknofest ödülleri sahiplerini buldu.",
        metadata={
            "source_document": "Teknofest Ödül Töreni",
            "document_type": "haber",
            "tarih": "25 Eylül 2025",
            "kaynak_url": "https://tubitak.gov.tr/haber/teknofest-2025",
            "section_heading": "Genel",
        },
    )

    formatted = format_gundem_docs([duyuru_doc, haber_doc])
    runner.info(f"Format uzunluğu: {len(formatted)} karakter")

    runner.check("DUYURU etiketi var", "[DUYURU" in formatted)
    runner.check("HABER etiketi var", "[HABER" in formatted)
    runner.check("Tarih1 ('Kasım') görünür", "Kasım" in formatted)
    runner.check("Tarih2 ('Eylül') görünür", "Eylül" in formatted)
    runner.check("URL1 var", "tubitak.gov.tr/duyuru" in formatted)
    runner.check("URL2 var", "tubitak.gov.tr/haber" in formatted)
    runner.check("Chunk'lar '---' ile ayrılmış", "---" in formatted)
    runner.check("İçerik1 korunmuş", "1 Aralık" in formatted)
    runner.check("İçerik2 korunmuş", "Teknofest" in formatted)

    # --- GUNDEM_PROMPT içeriği ---
    sys_lower = GUNDEM_SYSTEM_PROMPT.lower()
    runner.check("Prompt halüsinasyon koruması ('uydurma')", "uydurma" in sys_lower)
    runner.check("Prompt 'bilgi yoksa açıkça de' içerir", "yoksa" in sys_lower)
    runner.check("Prompt 'Kaynaklar' başlığını teşvik ediyor", "kaynak" in sys_lower)
    runner.check("Prompt {context} placeholder'ı var", "{context}" in GUNDEM_SYSTEM_PROMPT)

    # GUNDEM_PROMPT rendering smoke
    rendered = GUNDEM_PROMPT.format(context=formatted, question="Son duyurular nedir?")
    runner.check(
        "GUNDEM_PROMPT render edildi",
        "{context}" not in rendered and "{question}" not in rendered,
    )
    runner.check(
        "Render edilen prompt bağlam metnini içeriyor",
        "Teknofest" in rendered,
    )

    return runner.summary()


if __name__ == "__main__":
    sys.exit(main())
