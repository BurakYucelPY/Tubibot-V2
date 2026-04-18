import json
import os
import re

from bs4 import BeautifulSoup
from langchain_core.documents import Document


TR_MONTHS = {
    "Oca": "01", "Şub": "02", "Mar": "03", "Nis": "04",
    "May": "05", "Haz": "06", "Tem": "07", "Ağu": "08",
    "Eyl": "09", "Eki": "10", "Kas": "11", "Ara": "12",
}


def _parse_year(tarih):
    parts = (tarih or "").strip().split(" ")
    if len(parts) == 3 and parts[2].isdigit():
        return parts[2]
    return ""


def _html_to_text(html):
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_json_entries(json_path, doc_type):
    """Bir JSON dosyasındaki her kaydı bir Document'a çevirir."""
    if not os.path.exists(json_path):
        print(f"[WARN] JSON bulunamadı: {json_path}")
        return []

    with open(json_path, "r", encoding="utf-8") as f:
        entries = json.load(f)

    documents = []
    for entry in entries:
        baslik = (entry.get("baslik") or "").strip()
        ozet = (entry.get("ozet") or "").strip()
        tam_icerik = _html_to_text(entry.get("tam_icerik") or "")

        if not baslik and not tam_icerik:
            continue

        parts = [baslik, ozet, tam_icerik]
        page_content = "\n\n".join(p for p in parts if p)

        metadata = {
            # processor.py kaynak bazlı gruplama için "source" field'ına bakar.
            # Her entry unique bir source ile etiketlenmeli — yoksa hepsi tek
            # grupta birleşip ilk belgenin metadata'sını miras alır.
            "source": entry.get("kaynak_url") or f"{doc_type}:{baslik}",
            "source_document": baslik or entry.get("kaynak_url", "Bilinmeyen"),
            "document_type": doc_type,
            "kaynak_url": entry.get("kaynak_url", ""),
            "tarih": entry.get("tarih", ""),
            "year": _parse_year(entry.get("tarih", "")),
            "baslik": baslik,
            # Nötr kategori — processor.py'daki Header/Footer/PageBreak
            # filtresine takılmasın.
            "category": "Announcement",
        }

        documents.append(Document(page_content=page_content, metadata=metadata))

    print(f"[INFO] {os.path.basename(json_path)}: {len(documents)} {doc_type} kaydı yüklendi.")
    return documents


def load_gundem_documents(backend_root):
    """duyurular.json + haberler.json dosyalarından tüm Document'ları döndürür."""
    duyurular_path = os.path.join(backend_root, "duyurular.json")
    haberler_path = os.path.join(backend_root, "haberler.json")

    docs = []
    docs.extend(load_json_entries(duyurular_path, "duyuru"))
    docs.extend(load_json_entries(haberler_path, "haber"))
    return docs


if __name__ == "__main__":
    _backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    all_docs = load_gundem_documents(_backend_root)

    print(f"\n[SUMMARY] Toplam {len(all_docs)} gündem belgesi üretildi.")
    print("\n[DEBUG] İlk 2 belgenin örnek içeriği:")
    for i, doc in enumerate(all_docs[:2]):
        print(f"\n--- [{i}] ---")
        print(f"  source_document: {doc.metadata.get('source_document')[:80]}")
        print(f"  document_type:   {doc.metadata.get('document_type')}")
        print(f"  tarih:           {doc.metadata.get('tarih')}")
        print(f"  year:            {doc.metadata.get('year')}")
        print(f"  kaynak_url:      {doc.metadata.get('kaynak_url')[:80]}")
        print(f"  content length:  {len(doc.page_content)} chars")
        print(f"  content preview: {doc.page_content[:150]}...")
