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
    "ska_rehberi": {"chunk_size": 1500, "chunk_overlap": 300},      # SKA hedefleri uzun metinler
    "cagri_duyurusu": {"chunk_size": 800, "chunk_overlap": 200},    # Kısa maddeler
    "basvuru_formu": {"chunk_size": 800, "chunk_overlap": 200},     # Form maddeleri
    "basvuru_kosullari": {"chunk_size": 800, "chunk_overlap": 200}, # Koşul maddeleri
    "oncelikli_alanlar": {"chunk_size": 5000, "chunk_overlap": 200},# Kısa liste — tek chunk
    "duyuru": {"chunk_size": 1000, "chunk_overlap": 200},           # Scrape edilen duyurular
    "haber": {"chunk_size": 1000, "chunk_overlap": 200},            # Scrape edilen haberler
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
    """Aşama 3: Çok kısa chunk'ları at. oncelikli_alanlar için 15, diğerleri için 50 char alt sınır."""
    print("\n[INFO] Aşama 3: Kısa Chunk Filtreleme.")
    kept = []
    for chunk in chunks:
        doc_type = chunk.metadata.get("document_type", "")
        min_length = 15 if doc_type == "oncelikli_alanlar" else 50
        if len(chunk.page_content.strip()) < min_length:
            continue
        kept.append(chunk)
    print(f"[INFO] {len(chunks) - len(kept)} kısa/boş chunk filtrelendi.")
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
