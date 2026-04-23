def format_docs_plain(docs):
    formatted_parts = []
    for doc in docs:
        source = doc.metadata.get("source_document", "Bilinmeyen Belge")
        section = doc.metadata.get("section_heading", "Genel")
        program = doc.metadata.get("program", "")
        program_str = f" | Program: {program}" if program else ""
        header = f"[Kaynak: {source}{program_str} | Bölüm: {section}]"
        formatted_parts.append(f"{header}\n{doc.page_content}")
    return "\n\n---\n\n".join(formatted_parts)


def format_gundem_docs(docs):
    """Gündem chunk'larını başlık + tarih + URL ile birlikte LLM bağlamına ver."""
    formatted_parts = []
    for doc in docs:
        source = doc.metadata.get("source_document", "Bilinmeyen")
        tur = doc.metadata.get("document_type", "")
        tarih = doc.metadata.get("tarih", "")
        url = doc.metadata.get("kaynak_url", "")
        header = f"[{tur.upper()} | {source} | Tarih: {tarih} | URL: {url}]"
        formatted_parts.append(f"{header}\n{doc.page_content}")
    return "\n\n---\n\n".join(formatted_parts)
