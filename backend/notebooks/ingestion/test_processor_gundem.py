"""
ingestion/test_processor_gundem.py

processor_gundem.py basit per-doküman chunking:
- Her chunk'ın section_heading = "Genel" (section-aware chunking kapalı).
- Kısa chunk filtresi (>= 50 char).
- document_type (duyuru/haber) chunk metadata'sına aktarılıyor mu?
- Dispatcher (processor.process_and_chunk_documents) duyuru/haber tipini
  doğru modüle yönlendiriyor mu?
"""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from _helpers.bootstrap import setup_backend_path
setup_backend_path()

from _helpers.runner import TestRunner
from langchain_core.documents import Document


def _make_entry(doc_type, baslik, uzun_icerik):
    return Document(
        page_content=f"{baslik}\n\n{uzun_icerik}",
        metadata={
            "source": f"{doc_type}:{baslik}",
            "source_document": baslik,
            "document_type": doc_type,
            "tarih": "12 Mart 2025",
            "kaynak_url": f"https://example.com/{baslik}",
            "baslik": baslik,
            "category": "Announcement",
        },
    )


def main():
    from src.ingestion.processor import process_and_chunk_documents
    from src.ingestion.processor_gundem import process_gundem_documents

    runner = TestRunner("ingestion/test_processor_gundem")

    # --- Fixture: 3 duyuru + 2 haber ---
    icerik_uzun = "Bu duyurunun detaylı açıklaması. " * 20
    raw = [
        _make_entry("duyuru", "2209-A Son Çağrı", icerik_uzun),
        _make_entry("duyuru", "TÜBİTAK Yeni Destek", icerik_uzun),
        _make_entry("duyuru", "2210 Başvuruları", icerik_uzun),
        _make_entry("haber", "TÜBİTAK Ödül Töreni", icerik_uzun),
        _make_entry("haber", "Başkan Açıklaması", icerik_uzun),
    ]

    chunks = process_gundem_documents(raw)
    runner.check("Chunk üretildi", len(chunks) >= 5, f"{len(chunks)} chunk")

    all_genel = all(c.metadata.get("section_heading") == "Genel" for c in chunks)
    runner.check(
        "Tüm chunk'ların section_heading='Genel' (section-aware kapalı)",
        all_genel,
    )

    all_long = all(len(c.page_content.strip()) >= 50 for c in chunks)
    runner.check("Tüm chunk'lar >= 50 char", all_long)

    # document_type korundu mu?
    type_counts = {}
    for c in chunks:
        t = c.metadata.get("document_type", "?")
        type_counts[t] = type_counts.get(t, 0) + 1
    runner.info(f"Chunk document_type dağılımı: {type_counts}")
    runner.check(
        "duyuru + haber türleri korunmuş",
        type_counts.get("duyuru", 0) > 0 and type_counts.get("haber", 0) > 0,
    )

    # Metadata alanları chunk'a aktarıldı mı?
    first = chunks[0]
    has_url = bool(first.metadata.get("kaynak_url"))
    has_tarih = bool(first.metadata.get("tarih"))
    runner.check(
        "kaynak_url ve tarih chunk metadata'sına aktarıldı",
        has_url and has_tarih,
    )

    # --- Dispatcher testi ---
    dispatched = process_and_chunk_documents(raw)
    runner.check(
        "Dispatcher duyuru/haber'i gündem işleyicisine yönlendirdi",
        len(dispatched) == len(chunks),
        f"dispatcher={len(dispatched)}, gundem={len(chunks)}",
    )
    all_dispatched_genel = all(c.metadata.get("section_heading") == "Genel" for c in dispatched)
    runner.check(
        "Dispatcher çıktısı da hepsi 'Genel' heading",
        all_dispatched_genel,
    )

    # --- Boş giriş ---
    empty = process_gundem_documents([])
    runner.check("Boş giriş boş liste döner", empty == [])

    # --- Boş dispatcher ---
    runner.check("Dispatcher boş giriş için boş döner", process_and_chunk_documents([]) == [])

    return runner.summary()


if __name__ == "__main__":
    sys.exit(main())
