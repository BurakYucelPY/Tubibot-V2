"""
ingestion/test_processor_pdf.py

processor_pdf.py section-aware chunking davranışı:
- MADDE/BÖLÜM başlıkları tespit edilip ayrı bölümler oluşturuluyor mu?
- oncelikli_alanlar için bölüm bölünmesi KAPALI (skip_section_split)
- Header/Footer/PageBreak kategorisi filtreleniyor mu?
- Kısa chunk'lar (< 50 char) filtrelenmiş mi?

Fixture: in-memory Document objeleri. Gerçek PDF okuma yok — salt işlem mantığı.
"""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from _helpers.bootstrap import setup_backend_path
setup_backend_path()

from _helpers.runner import TestRunner
from langchain_core.documents import Document


def _make_doc(text, doc_type="cagri_duyurusu", category="NarrativeText", source="fixture.pdf"):
    return Document(
        page_content=text,
        metadata={
            "source": source,
            "source_document": "Fixture Belge",
            "document_type": doc_type,
            "category": category,
        },
    )


def main():
    from src.ingestion.processor_pdf import process_pdf_documents

    runner = TestRunner("ingestion/test_processor_pdf")

    # --- Senaryo 1: MADDE başlıkları tespit edilip ayrı bölümlere ayrılmalı ---
    raw1 = [
        _make_doc("MADDE 1 - Amaç\nBu çağrının amacı araştırmayı desteklemektir. " * 5),
        _make_doc("MADDE 2 - Kapsam\nBu çağrı lisans öğrencilerini kapsar. " * 5),
        _make_doc("MADDE 3 - Başvuru\nBaşvurular online yapılır. " * 5),
    ]
    chunks1 = process_pdf_documents(raw1)
    headings1 = {c.metadata.get("section_heading") for c in chunks1}
    runner.check(
        "3 farklı MADDE başlığı tespit edildi",
        sum(1 for h in headings1 if h and h.startswith("MADDE")) >= 3,
        f"bulunan: {headings1}",
    )

    # --- Senaryo 2: Header/Footer/PageBreak kategorisi elenir ---
    raw2 = [
        _make_doc("Sayfa 1 başlık" * 10, category="Header"),
        _make_doc("Sayfa numarası 1", category="Footer"),
        _make_doc("---", category="PageBreak"),
        _make_doc("Gerçek içerik burada. " * 20, category="NarrativeText"),
    ]
    chunks2 = process_pdf_documents(raw2)
    runner.check(
        "Header/Footer/PageBreak filtrelendi — sadece narrative kaldı",
        all("Sayfa" not in c.page_content or "Gerçek" in c.page_content for c in chunks2),
        f"chunk sayısı: {len(chunks2)}",
    )
    runner.check(
        "Filtreden sonra en az 1 chunk var",
        len(chunks2) >= 1,
    )

    # --- Senaryo 3: oncelikli_alanlar'da section split kapalı (hepsi "Genel") ---
    raw3 = [
        _make_doc("MADDE 1 - Bu normalde bölüm olurdu. " * 20, doc_type="oncelikli_alanlar"),
        _make_doc("MADDE 2 - Bu da ayrı bölüm olurdu. " * 20, doc_type="oncelikli_alanlar"),
    ]
    chunks3 = process_pdf_documents(raw3)
    all_genel = all(c.metadata.get("section_heading") == "Genel" for c in chunks3)
    runner.check(
        "oncelikli_alanlar: tüm chunk'ların section_heading='Genel'",
        all_genel and len(chunks3) > 0,
        f"chunk sayısı: {len(chunks3)}",
    )

    # --- Senaryo 4: Kısa chunk filtresi (< 50 char tutulmaz) ---
    raw4 = [
        _make_doc("ABC"),                    # çok kısa, elenmeli
        _make_doc("Uzun içerik " * 30),       # kalır
    ]
    chunks4 = process_pdf_documents(raw4)
    all_long = all(len(c.page_content.strip()) >= 50 for c in chunks4)
    runner.check(
        "Filtreleme sonrası tüm chunk'lar >= 50 char",
        all_long,
        f"{len(chunks4)} chunk",
    )

    # --- Senaryo 5: Boş giriş → boş çıktı ---
    chunks5 = process_pdf_documents([])
    runner.check("Boş giriş boş liste döner", chunks5 == [])

    # --- Senaryo 6: Table kategorisi section_heading='Tablo' ---
    raw6 = [
        _make_doc("Tablo içeriği: sütun1 sütun2 sütun3 satır1 satır2 satır3" * 5, category="Table"),
    ]
    chunks6 = process_pdf_documents(raw6)
    has_tablo = any(c.metadata.get("section_heading") == "Tablo" for c in chunks6)
    runner.check("Table kategorisi 'Tablo' etiketini alıyor", has_tablo)

    return runner.summary()


if __name__ == "__main__":
    sys.exit(main())
