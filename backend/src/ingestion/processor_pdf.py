from langchain_core.documents import Document

from src.ingestion.processor import (
    _filter_noise,
    _filter_short_chunks,
    _detect_heading,
    _get_splitter_for_doc_type,
)


def process_pdf_documents(raw_documents):
    """
    PDF dokümanları için bölüm-farkındalıklı (section-aware) chunking.
    - MADDE/BÖLÜM/Amaç gibi başlıkları tespit edip her bölümü bağımsız chunk'lar.
    - oncelikli_alanlar türünde tüm metni tek blokta birleştirip tek geçiş splitter'a verir.
    """
    cleaned_documents = _filter_noise(raw_documents)

    print("\n[INFO] Aşama 2: Bölüm Farkındalıklı Chunking Başlatıldı (PDF).")

    final_chunks = []

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
        for table_doc in doc_groups["tables"]:
            table_doc.metadata["section_heading"] = "Tablo"
            final_chunks.append(table_doc)

        if not doc_groups["texts"]:
            continue

        splitter = _get_splitter_for_doc_type(doc_type)

        docs_by_source = {}
        for doc in doc_groups["texts"]:
            src = doc.metadata.get("source", "unknown")
            if src not in docs_by_source:
                docs_by_source[src] = []
            docs_by_source[src].append(doc)

        type_chunk_count = 0

        skip_section_split = doc_type in ("oncelikli_alanlar",)

        for src, source_docs in docs_by_source.items():
            base_metadata = source_docs[0].metadata.copy()

            if skip_section_split:
                joined_text = "\n".join(doc.page_content for doc in source_docs)
                merged_doc = Document(page_content=joined_text, metadata=base_metadata)
                merged_doc.metadata["section_heading"] = "Genel"

                chunks = splitter.split_documents([merged_doc])
                for chunk in chunks:
                    chunk.metadata["section_heading"] = "Genel"

                final_chunks.extend(chunks)
                type_chunk_count += len(chunks)
                continue

            section_groups = []
            current_heading = "Genel"
            current_texts = []

            for doc in source_docs:
                heading = _detect_heading(doc.page_content)
                if heading:
                    if current_texts:
                        section_groups.append((current_heading, current_texts, base_metadata.copy()))
                    current_heading = heading
                    current_texts = [doc.page_content]
                else:
                    current_texts.append(doc.page_content)

            if current_texts:
                section_groups.append((current_heading, current_texts, base_metadata.copy()))

            for heading, texts, metadata in section_groups:
                joined_text = "\n".join(texts)
                section_doc = Document(page_content=joined_text, metadata=metadata)
                section_doc.metadata["section_heading"] = heading

                chunks = splitter.split_documents([section_doc])

                for chunk in chunks:
                    chunk.metadata["section_heading"] = heading

                final_chunks.extend(chunks)
                type_chunk_count += len(chunks)

        print(f"  [{doc_type}] {len(doc_groups['texts'])} metin parçası -> {type_chunk_count} chunk (size={splitter._chunk_size})")

    enriched_chunks = _filter_short_chunks(final_chunks)
    print(f"[INFO] İşlem tamamlandı. Toplam {len(enriched_chunks)} kaliteli chunk oluşturuldu.")
    return enriched_chunks
