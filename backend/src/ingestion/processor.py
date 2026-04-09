import os
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from src.ingestion.pdf_loader import load_pdfs

# ====================================================================
# Belge türüne göre farklı chunking stratejileri
# ====================================================================
CHUNK_CONFIG = {
    "ska_rehberi": {"chunk_size": 1500, "chunk_overlap": 300},      # SKA hedefleri uzun metinler
    "cagri_duyurusu": {"chunk_size": 800, "chunk_overlap": 200},    # Kısa maddeler
    "basvuru_formu": {"chunk_size": 800, "chunk_overlap": 200},     # Form maddeleri
    "basvuru_kosullari": {"chunk_size": 800, "chunk_overlap": 200}, # Koşul maddeleri
    "oncelikli_alanlar": {"chunk_size": 5000, "chunk_overlap": 200},# Kısa liste — tek chunk
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
    - Bölüm farkındalıklı (section-aware) chunking
    - Başlık tespiti ve metadata ekleme (belge bazında izole)
    - Çok kısa chunk filtreleme
    """
    # ================================================================
    # Aşama 1: Gürültü Filtreleme
    # ================================================================
    cleaned_documents = []

    print("\n[INFO] Aşama 1: Veri Filtreleme (Noise Reduction) Başlatıldı.")
    for doc in raw_documents:
        category = doc.metadata.get("category", "")
        if category in ["Header", "Footer", "PageBreak"]:
            continue
        cleaned_documents.append(doc)

    print(f"[INFO] Filtreleme tamamlandı: {len(raw_documents)} ham belgeden {len(cleaned_documents)} geçerli belge elde edildi.")

    # ================================================================
    # Aşama 2: Bölüm Farkındalıklı (Section-Aware) Chunking
    # Her belge kaynağı bağımsız işlenir — heading sızıntısı önlenir.
    # ================================================================
    print("\n[INFO] Aşama 2: Bölüm Farkındalıklı Chunking Başlatıldı.")

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

    for doc_type, doc_groups in docs_by_type.items():
        # Tablolar: doğrudan ekle (bölme yok)
        for table_doc in doc_groups["tables"]:
            table_doc.metadata["section_heading"] = "Tablo"
            final_chunks.append(table_doc)

        if not doc_groups["texts"]:
            continue

        splitter = _get_splitter_for_doc_type(doc_type)

        # Kaynak dosya bazında grupla
        docs_by_source = {}
        for doc in doc_groups["texts"]:
            src = doc.metadata.get("source", "unknown")
            if src not in docs_by_source:
                docs_by_source[src] = []
            docs_by_source[src].append(doc)

        type_chunk_count = 0

        # Düz liste belgeler (örn: öncelikli alanlar) için section splitting YAPMA
        # Tüm elementleri tek blok olarak birleştir, sonra text splitter'a ver.
        skip_section_split = doc_type in ("oncelikli_alanlar",)

        for src, source_docs in docs_by_source.items():
            base_metadata = source_docs[0].metadata.copy()

            if skip_section_split:
                # Tüm elementleri tek blok olarak birleştir
                joined_text = "\n".join(doc.page_content for doc in source_docs)
                merged_doc = Document(page_content=joined_text, metadata=base_metadata)
                merged_doc.metadata["section_heading"] = "Genel"

                chunks = splitter.split_documents([merged_doc])
                for chunk in chunks:
                    chunk.metadata["section_heading"] = "Genel"

                final_chunks.extend(chunks)
                type_chunk_count += len(chunks)
                continue

            # Diğer belge türleri: bölüm başlıklarına göre grupla
            section_groups = []  # [(heading, [element_texts], base_metadata)]
            current_heading = "Genel"
            current_texts = []

            for doc in source_docs:
                heading = _detect_heading(doc.page_content)
                if heading:
                    # Önceki bölümü kaydet
                    if current_texts:
                        section_groups.append((current_heading, current_texts, base_metadata.copy()))
                    current_heading = heading
                    current_texts = [doc.page_content]
                else:
                    current_texts.append(doc.page_content)

            # Son bölümü kaydet
            if current_texts:
                section_groups.append((current_heading, current_texts, base_metadata.copy()))

            # Her bölüm grubunu bağımsız olarak chunk'la
            for heading, texts, metadata in section_groups:
                joined_text = "\n".join(texts)
                section_doc = Document(page_content=joined_text, metadata=metadata)
                section_doc.metadata["section_heading"] = heading

                chunks = splitter.split_documents([section_doc])

                # Her chunk'a bölüm başlığını ata
                for chunk in chunks:
                    chunk.metadata["section_heading"] = heading

                final_chunks.extend(chunks)
                type_chunk_count += len(chunks)

        print(f"  [{doc_type}] {len(doc_groups['texts'])} metin parçası -> {type_chunk_count} chunk (size={splitter._chunk_size})")

    # ================================================================
    # Aşama 3: Kısa Chunk Filtreleme (gürültü temizliği)
    # page_content'e metadata injection YAPILMAZ — temiz metin kalır.
    # ================================================================
    print("\n[INFO] Aşama 3: Kısa Chunk Filtreleme.")
    enriched_chunks = []

    for chunk in final_chunks:
        doc_type = chunk.metadata.get("document_type", "")
        min_length = 15 if doc_type == "oncelikli_alanlar" else 50

        if len(chunk.page_content.strip()) < min_length:
            continue

        enriched_chunks.append(chunk)

    filtered_count = len(final_chunks) - len(enriched_chunks)
    print(f"[INFO] {filtered_count} kısa/boş chunk filtrelendi.")
    print(f"[INFO] İşlem tamamlandı. Toplam {len(enriched_chunks)} kaliteli chunk oluşturuldu.")

    return enriched_chunks


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    raw_data_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "2209A_pdf")
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
