import os
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.ingestion.pdf_loader import load_pdfs

# ====================================================================
# Belge türüne göre farklı chunking stratejileri
# ====================================================================
CHUNK_CONFIG = {
    "ska_rehberi": {"chunk_size": 1500, "chunk_overlap": 300},      # SKA hedefleri uzun metinler
    "cagri_duyurusu": {"chunk_size": 800, "chunk_overlap": 200},    # Kısa maddeler
    "basvuru_formu": {"chunk_size": 800, "chunk_overlap": 200},     # Form maddeleri
    "basvuru_kosullari": {"chunk_size": 800, "chunk_overlap": 200}, # Koşul maddeleri
    "oncelikli_alanlar": {"chunk_size": 1000, "chunk_overlap": 200},# Orta uzunluk
    "default": {"chunk_size": 1000, "chunk_overlap": 200},          # Fallback
}

# Başlık tespiti için basit regex desenleri
HEADING_PATTERNS = [
    r"^(?:MADDE|Madde)\s+\d+",                  # MADDE 1, Madde 2
    r"^(?:BÖLÜM|Bölüm)\s+\d+",                  # BÖLÜM 1
    r"^\d+\.\s+[A-ZÇĞİÖŞÜ]",                   # 1. Başlık
    r"^(?:Amaç|AMAÇ)\s+\d+",                    # Amaç 1 (SKA)
    r"^(?:Hedef|HEDEF)\s+\d+",                   # Hedef 1
    r"^(?:Gösterge|GÖSTERGE)\s+\d+",             # Gösterge 1
    r"^[A-ZÇĞİÖŞÜ][A-ZÇĞİÖŞÜ\s]{5,}$",        # TAMAMI BÜYÜK HARF BAŞLIK
]


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
        separators=["\n\n", "\n", ". ", " ", ""]
    )


def process_and_chunk_documents(raw_documents):
    """
    Ham belgeleri filtreler ve RAG sistemi için chunk'lara böler.
    - Gürültü filtreleme
    - Belge türüne göre farklı chunk boyutları
    - Başlık tespiti ve metadata ekleme
    - Çok kısa chunk filtreleme
    """
    cleaned_documents = []
    
    print("\n[INFO] Aşama 1: Veri Filtreleme (Noise Reduction) Başlatıldı.")
    for doc in raw_documents:
        category = doc.metadata.get("category", "")
        if category in ["Header", "Footer", "PageBreak", "UncategorizedText"]:
            continue
        cleaned_documents.append(doc)
        
    print(f"[INFO] Filtreleme tamamlandı: {len(raw_documents)} ham belgeden {len(cleaned_documents)} geçerli belge elde edildi.")

    print("\n[INFO] Aşama 2: Metin Parçalama (Akıllı Chunking) Başlatıldı.")
    
    final_chunks = []
    
    # Belge türüne göre grupla
    docs_by_type = {}
    for doc in cleaned_documents:
        doc_type = doc.metadata.get("document_type", "default")
        if doc_type not in docs_by_type:
            docs_by_type[doc_type] = {"tables": [], "texts": []}
        
        if doc.metadata.get("category") == "Table":
            docs_by_type[doc_type]["tables"].append(doc)
        else:
            docs_by_type[doc_type]["texts"].append(doc)
    
    # Her belge türü için farklı splitter ile chunk'la
    for doc_type, doc_groups in docs_by_type.items():
        # Tablolar: doğrudan ekle (bölme yok)
        final_chunks.extend(doc_groups["tables"])
        
        # Metinler: uygun splitter ile böl
        if doc_groups["texts"]:
            splitter = _get_splitter_for_doc_type(doc_type)
            split_texts = splitter.split_documents(doc_groups["texts"])
            
            print(f"  [{doc_type}] {len(doc_groups['texts'])} metin → {len(split_texts)} chunk (size={splitter._chunk_size})")
            final_chunks.extend(split_texts)
    
    # Aşama 3: Başlık bilgisi ekleme & kısa chunk filtreleme
    print("\n[INFO] Aşama 3: Başlık Tespiti ve Kısa Chunk Filtreleme.")
    enriched_chunks = []
    current_heading = "Genel"
    
    for chunk in final_chunks:
        # Çok kısa chunk'ları filtrele (noise)
        if len(chunk.page_content.strip()) < 50:
            continue
        
        # Başlık tespiti
        heading = _detect_heading(chunk.page_content)
        if heading:
            current_heading = heading
        
        # Başlık bilgisini metadata'ya ekle
        chunk.metadata["section_heading"] = current_heading
        enriched_chunks.append(chunk)
    
    filtered_count = len(final_chunks) - len(enriched_chunks)
    print(f"[INFO] {filtered_count} kısa/boş chunk filtrelendi.")
    print(f"[INFO] İşlem tamamlandı. Toplam {len(enriched_chunks)} kaliteli chunk oluşturuldu.")
    
    return enriched_chunks


if __name__ == "__main__":
    raw_data_path = "data/raw_pdf"
    print("[INFO] PDF yükleme işlemi başlatılıyor...")
    raw_docs = load_pdfs(raw_data_path)
    
    processed_chunks = process_and_chunk_documents(raw_docs)
    
    # Doğrulama
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