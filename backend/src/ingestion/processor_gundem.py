from src.ingestion.processor import (
    _filter_noise,
    _filter_short_chunks,
    _get_splitter_for_doc_type,
)


def process_gundem_documents(raw_documents):
    """
    Gündem (duyuru + haber) dokümanları için basit per-document chunking.
    - Her doküman zaten atomik (tek duyuru veya tek haber) olduğundan
      bölüm-farkındalıklı (section-aware) chunking yapılmaz.
    - Her chunk section_heading = "Genel" etiketiyle işaretlenir.
    """
    cleaned_documents = _filter_noise(raw_documents)

    print("\n[INFO] Aşama 2: Gündem Chunking Başlatıldı.")

    final_chunks = []
    docs_by_type: dict[str, list] = {}

    for doc in cleaned_documents:
        doc_type = doc.metadata.get("document_type", "default")
        docs_by_type.setdefault(doc_type, []).append(doc)

    for doc_type, docs in docs_by_type.items():
        splitter = _get_splitter_for_doc_type(doc_type)
        chunks = splitter.split_documents(docs)
        for chunk in chunks:
            chunk.metadata["section_heading"] = "Genel"
        final_chunks.extend(chunks)
        print(f"  [{doc_type}] {len(docs)} doküman -> {len(chunks)} chunk (size={splitter._chunk_size})")

    enriched_chunks = _filter_short_chunks(final_chunks)
    print(f"[INFO] İşlem tamamlandı. Toplam {len(enriched_chunks)} kaliteli chunk oluşturuldu.")
    return enriched_chunks
