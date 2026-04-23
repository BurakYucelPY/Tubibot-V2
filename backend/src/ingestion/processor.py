import os
import re

from langchain_text_splitters import RecursiveCharacterTextSplitter

# ====================================================================
# Ortak (koordinatör) modül:
# - Paylaşılan sabitler ve yardımcı fonksiyonlar (PDF + Gündem ortak)
# - Dispatcher: process_and_chunk_documents(raw_documents)
# - Re-export: process_pdf_documents, process_gundem_documents
# ====================================================================

# Belge türüne göre farklı chunking stratejileri
CHUNK_CONFIG = {
    # Mevcut (korunur):
    "ska_rehberi": {"chunk_size": 1500, "chunk_overlap": 300},      # SKA hedefleri uzun metinler
    "cagri_duyurusu": {"chunk_size": 800, "chunk_overlap": 200},    # Kısa maddeler
    "basvuru_formu": {"chunk_size": 800, "chunk_overlap": 200},     # Form maddeleri
    "basvuru_kosullari": {"chunk_size": 800, "chunk_overlap": 200}, # Koşul maddeleri
    "oncelikli_alanlar": {"chunk_size": 5000, "chunk_overlap": 200},# Kısa liste — tek chunk
    "duyuru": {"chunk_size": 1000, "chunk_overlap": 200},           # Scrape edilen duyurular
    "haber": {"chunk_size": 1000, "chunk_overlap": 200},            # Scrape edilen haberler
    # YENİ (TübitakBilgi_pdf genişletmesi):
    "ardeb_1001_basvuru":       {"chunk_size": 800,  "chunk_overlap": 200},
    "ardeb_1002_basvuru":       {"chunk_size": 1200, "chunk_overlap": 250},
    "ardeb_proje_yonetmeligi":  {"chunk_size": 1500, "chunk_overlap": 250},
    "bideb_burs_2211a":         {"chunk_size": 800,  "chunk_overlap": 200},
    "bideb_burs_2219":          {"chunk_size": 800,  "chunk_overlap": 200},
    "2209b_rehberi":            {"chunk_size": 800,  "chunk_overlap": 200},
    "teydeb_uygulama_esaslari": {"chunk_size": 1000, "chunk_overlap": 200},
    "teydeb_yonetmeligi":       {"chunk_size": 1000, "chunk_overlap": 200},
    "mali_esaslar":             {"chunk_size": 1000, "chunk_overlap": 200},
    "mali_rapor_kilavuzu":      {"chunk_size": 1200, "chunk_overlap": 250},
    "fikri_haklar":             {"chunk_size": 1000, "chunk_overlap": 200},
    "yazim_rehberi":            {"chunk_size": 800,  "chunk_overlap": 200},
    "stratejik_plan":           {"chunk_size": 1200, "chunk_overlap": 300},
    "faaliyet_raporu":          {"chunk_size": 1200, "chunk_overlap": 300},
    "default": {"chunk_size": 1000, "chunk_overlap": 200},          # Fallback
}

# Başlık tespiti için basit regex desenleri (PDF-odaklı; gündem metninde nadiren tutar)
HEADING_PATTERNS = [
    r"^(?:MADDE|Madde)\s+\d+",                  # MADDE 1, Madde 2
    r"^(?:BÖLÜM|Bölüm)\s+\d+",                  # BÖLÜM 1
    r"^\d+\.\s+[A-ZÇĞİÖŞÜ]",                    # 1. Başlık
    r"^(?:Amaç|AMAÇ)\s+\d+",                    # Amaç 1 (SKA)
    r"^(?:Hedef|HEDEF)\s+\d+",                  # Hedef 1
    r"^(?:Gösterge|GÖSTERGE)\s+\d+",            # Gösterge 1
    r"^[A-ZÇĞİÖŞÜ][A-ZÇĞİÖŞÜ\s]{5,}$",         # TAMAMI BÜYÜK HARF BAŞLIK
]

# Dispatcher için gündem doküman türleri
_GUNDEM_DOC_TYPES = {"duyuru", "haber"}


def _detect_heading(text):
    """Metin bir başlık mı? Evetse başlık metnini döndür."""
    first_line = text.strip().split("\n")[0].strip()
    for pattern in HEADING_PATTERNS:
        if re.match(pattern, first_line):
            return first_line
    return None


def _get_splitter_for_doc_type(doc_type):
    """Belge türüne göre uygun text splitter döndür."""
    config = CHUNK_CONFIG.get(doc_type, CHUNK_CONFIG["default"])
    return RecursiveCharacterTextSplitter(
        chunk_size=config["chunk_size"],
        chunk_overlap=config["chunk_overlap"],
        separators=["\n\n", "\n", ". ", " ", ""],
    )


def _filter_noise(raw_documents):
    """Aşama 1: Header/Footer/PageBreak gibi gürültü kategorilerini at."""
    print("\n[INFO] Aşama 1: Veri Filtreleme (Noise Reduction) Başlatıldı.")
    cleaned = [
        doc for doc in raw_documents
        if doc.metadata.get("category", "") not in ("Header", "Footer", "PageBreak")
    ]
    print(f"[INFO] Filtreleme tamamlandı: {len(raw_documents)} ham belgeden {len(cleaned)} geçerli belge elde edildi.")
    return cleaned


def _filter_short_chunks(chunks):
    """Aşama 3: Yalnızca tamamen boş chunk'ları at (bilgi kaybını önlemek için).

    Eski davranışta 50 char (oncelikli_alanlar için 15 char) alt sınır vardı;
    tek satırlık madde numaraları veya kısa başlıklar kaybolabiliyordu.
    Şimdi: strip() sonrası uzunluk > 0 olan her chunk korunur.
    """
    print("\n[INFO] Aşama 3: Kısa Chunk Filtreleme (yalnız boş olanlar atılır).")
    kept = [c for c in chunks if len(c.page_content.strip()) > 0]
    print(f"[INFO] {len(chunks) - len(kept)} boş chunk filtrelendi.")
    return kept


def process_and_chunk_documents(raw_documents):
    """
    Dispatcher: dokümanların document_type'ına bakıp PDF veya gündem işleyicisine yönlendirir.
    - duyuru/haber → process_gundem_documents
    - diğer (ska_rehberi, cagri_duyurusu, ...) → process_pdf_documents
    """
    if not raw_documents:
        return []

    first_type = raw_documents[0].metadata.get("document_type", "")
    if first_type in _GUNDEM_DOC_TYPES:
        return process_gundem_documents(raw_documents)
    return process_pdf_documents(raw_documents)


# Aşağıdaki re-export'lar DOSYANIN SONUNDA olmalı — circular import için kritik.
# processor_pdf / processor_gundem modülleri yukarıdaki helper'ları import ediyor;
# onları buradan re-export etmek için ortak helper'ların TANIMI tamamlanmış olmalı.
from src.ingestion.processor_pdf import process_pdf_documents  # noqa: E402, F401
from src.ingestion.processor_gundem import process_gundem_documents  # noqa: E402, F401


if __name__ == "__main__":
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from src.ingestion.pdf_loader import load_pdfs

    raw_data_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "2209A_pdf")
    print("[INFO] PDF yükleme işlemi başlatılıyor...")
    raw_docs = load_pdfs(raw_data_path)

    processed_chunks = process_and_chunk_documents(raw_docs)

    print("\n[DEBUG] Örnek Chunk'lar:")
    print("-" * 50)
    for i in range(min(3, len(processed_chunks))):
        chunk = processed_chunks[i]
        print(f"\n[Chunk {i}]")
        print(f"  source: {chunk.metadata.get('source_document', 'N/A')}")
        print(f"  type: {chunk.metadata.get('document_type', 'N/A')}")
        print(f"  section: {chunk.metadata.get('section_heading', 'N/A')}")
        print(f"  length: {len(chunk.page_content)} chars")
        print(f"  content: {chunk.page_content[:150]}...")
    print("-" * 50)
