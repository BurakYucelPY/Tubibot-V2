import os
import unicodedata

import fitz  # PyMuPDF
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_core.documents import Document

# ====================================================================
# METADATA MAPPING: Her PDF dosyasına anlamlı metadata ekliyoruz.
# Bu sayede chunk'lar hangi belgeden/türden/hangi programdan geldiğini bilecek.
# ====================================================================
PDF_METADATA_MAP = {
    # ---------------- data/2209A_pdf/ (mevcut 5, korunur) ----------------
    "2209-A_2025_Cagri_Duyurusu.pdf": {
        "source_document": "2209-A 2025 Yılı Çağrı Duyurusu",
        "document_type": "cagri_duyurusu",
        "program": "2209-A BİDEB",
        "year": "2025",
    },
    "tubitak_2209a_form.pdf": {
        "source_document": "2209-A Araştırma Önerisi Formu",
        "document_type": "basvuru_formu",
        "program": "2209-A BİDEB",
        "year": "2025",
    },
    "Öncelikli Alanlar.pdf": {
        "source_document": "2025 Öncelikli Alanlar Listesi",
        "document_type": "oncelikli_alanlar",
        "program": "2209-A BİDEB",
        "year": "2025",
    },
    "SKA_Surdurulebilir_Kalkinma.pdf": {
        "source_document": "Sürdürülebilir Kalkınma Amaçları Kapsamı ve Göstergeleri",
        "document_type": "ska_rehberi",
        "program": "SKA",
        "year": "",
    },
    "kimlerbasvurur.pdf": {
        "source_document": "2209-A Kimler Başvurabilir",
        "document_type": "basvuru_kosullari",
        "program": "2209-A BİDEB",
        "year": "2025",
    },
    # ---------------- data/TübitakBilgi_pdf/ (yeni 26) ----------------
    "2209-A_2025_Yili_Cagri_Duyurusu_09102025.pdf": {
        "source_document": "2209-A 2025 Yılı Çağrı Duyurusu (09.10.2025 güncel)",
        "document_type": "cagri_duyurusu",
        "program": "2209-A BİDEB",
        "year": "2025",
    },
    "Tubitak_oncelikli_alanlar.pdf": {
        "source_document": "TÜBİTAK Öncelikli Alanlar (Güncel)",
        "document_type": "oncelikli_alanlar",
        "program": "2209-A BİDEB",
        "year": "2025",
    },
    "SKA_Kapsamı_ve_Göstergeleri.pdf": {
        "source_document": "SKA Kapsamı ve Göstergeleri (Güncel)",
        "document_type": "ska_rehberi",
        "program": "SKA",
        "year": "2020",
    },
    "1. Özgün Değer- Konunun Önemi Nasıl Yazılır.pdf": {
        "source_document": "Özgün Değer ve Konunun Önemi Nasıl Yazılır",
        "document_type": "yazim_rehberi",
        "program": "2209-A BİDEB",
        "year": "2025",
    },
    "2209B_Universite_Sanayi_Arastirma_Projeleri.pdf": {
        "source_document": "2209-B Üniversite Sanayi İş Birliği Araştırma Projeleri",
        "document_type": "2209b_rehberi",
        "program": "2209-B BİDEB",
        "year": "2025",
    },
    "2211A_Yurt_Ici_Genel_Doktora_Burs_Programi.pdf": {
        "source_document": "2211-A Yurt İçi Genel Doktora Burs Programı",
        "document_type": "bideb_burs_2211a",
        "program": "2211-A BİDEB",
        "year": "2025",
    },
    "2219_Yurt_Disi_Doktora_Sonrasi_Burs_Programi.pdf": {
        "source_document": "2219 Yurt Dışı Doktora Sonrası Burs Programı",
        "document_type": "bideb_burs_2219",
        "program": "2219 BİDEB",
        "year": "2025",
    },
    "2219_Yurt_Disi_Doktora_Sonrasi_Kurallari.pdf": {
        "source_document": "2219 Yurt Dışı Doktora Sonrası Kurallar",
        "document_type": "bideb_burs_2219",
        "program": "2219 BİDEB",
        "year": "2025",
    },
    "1001_ARDEB_basvurudan_once.pdf": {
        "source_document": "1001 ARDEB - Başvurudan Önce",
        "document_type": "ardeb_1001_basvuru",
        "program": "1001 ARDEB",
        "year": "2025",
    },
    "1001_ARDEB_basvuru_sirasinda.pdf": {
        "source_document": "1001 ARDEB - Başvuru Sırasında",
        "document_type": "ardeb_1001_basvuru",
        "program": "1001 ARDEB",
        "year": "2025",
    },
    "1001_ARDEB_basvurudan_sonra.pdf": {
        "source_document": "1001 ARDEB - Başvurudan Sonra",
        "document_type": "ardeb_1001_basvuru",
        "program": "1001 ARDEB",
        "year": "2025",
    },
    "Ardeb_1001_basvuru_rehberi.pdf": {
        "source_document": "1001 ARDEB Başvuru Rehberi",
        "document_type": "ardeb_1001_basvuru",
        "program": "1001 ARDEB",
        "year": "2025",
    },
    "ARDEB_1002_a_programi_basvuru_rehberi.pdf": {
        "source_document": "1002-A ARDEB Başvuru Rehberi",
        "document_type": "ardeb_1002_basvuru",
        "program": "1002 ARDEB",
        "year": "2025",
    },
    "ARDEB_1002_b_programi_basvuru_rehberi.pdf": {
        "source_document": "1002-B ARDEB Başvuru Rehberi",
        "document_type": "ardeb_1002_basvuru",
        "program": "1002 ARDEB",
        "year": "2025",
    },
    "ARDEB_BIDEB_Es_Zamanli_Basvuru_Kosullari.pdf": {
        "source_document": "ARDEB-BİDEB Eş Zamanlı Başvuru Koşulları",
        "document_type": "basvuru_kosullari",
        "program": "ARDEB-BİDEB",
        "year": "2025",
    },
    "ARDEB_Proje_Gorev_Limitleri.pdf": {
        "source_document": "ARDEB Proje Görev Limitleri",
        "document_type": "ardeb_proje_yonetmeligi",
        "program": "ARDEB",
        "year": "2025",
    },
    "1501_2026_1_Cagri_Duyurusu.pdf.pdf": {
        "source_document": "1501 Sanayi Ar-Ge 2026/1 Çağrı Duyurusu",
        "document_type": "cagri_duyurusu",
        "program": "1501 TEYDEB",
        "year": "2026",
    },
    "1501_Sanayi_ArGe_Uygulama_Esaslari.pdf": {
        "source_document": "1501 Sanayi Ar-Ge Uygulama Esasları",
        "document_type": "teydeb_uygulama_esaslari",
        "program": "1501 TEYDEB",
        "year": "2025",
    },
    "1507_KOBI_ArGe_2026_1_Cagri_Duyurusu.pdf": {
        "source_document": "1507 KOBİ Ar-Ge 2026/1 Çağrı Duyurusu",
        "document_type": "cagri_duyurusu",
        "program": "1507 TEYDEB",
        "year": "2026",
    },
    "1507_KOBI_ArGe_Uygulama_Esaslari.pdf": {
        "source_document": "1507 KOBİ Ar-Ge Uygulama Esasları",
        "document_type": "teydeb_uygulama_esaslari",
        "program": "1507 TEYDEB",
        "year": "2025",
    },
    "TEYDEB_Destek_Programlari_Yonetmeligi.pdf": {
        "source_document": "TEYDEB Destek Programları Yönetmeliği",
        "document_type": "teydeb_yonetmeligi",
        "program": "TEYDEB",
        "year": "2025",
    },
    "Arastirma_Projeleri_Idari_Mali_Esaslar.pdf": {
        "source_document": "Araştırma Projeleri İdari ve Mali Esaslar",
        "document_type": "mali_esaslar",
        "program": "TÜBİTAK",
        "year": "2025",
    },
    "Mali_Rapor_Hazirlama_Kilavuzu.pdf": {
        "source_document": "Mali Rapor Hazırlama Kılavuzu",
        "document_type": "mali_rapor_kilavuzu",
        "program": "TEYDEB",
        "year": "2026",
    },
    "Proje_Fikri_Haklar_Esaslari.pdf": {
        "source_document": "Proje Fikri Haklar Esasları",
        "document_type": "fikri_haklar",
        "program": "TÜBİTAK",
        "year": "2025",
    },
    "TUBITAK_2025_Yili_Faaliyet_Raporu.pdf": {
        "source_document": "TÜBİTAK 2025 Yılı Faaliyet Raporu",
        "document_type": "faaliyet_raporu",
        "program": "TÜBİTAK",
        "year": "2025",
    },
    "tubitak_2024-2028_stratejik_plani.pdf": {
        "source_document": "TÜBİTAK 2024-2028 Stratejik Planı",
        "document_type": "stratejik_plan",
        "program": "TÜBİTAK",
        "year": "2024",
    },
}


# ====================================================================
# Varsayılan: tüm PDF'ler PyMuPDF ile okunur.
# Kalite sorunu çıkan dosyalar buraya eklenir → o dosya Unstructured kullanır.
# (Hibrit fallback — plan bölüm "Hibrit fallback — per-PDF loader override")
# ====================================================================
UNSTRUCTURED_OVERRIDES: set[str] = set()


def _get_metadata_for_file(filename):
    """Dosya adına göre metadata mapping'den bilgi döndür.

    Unicode normalization farklarına (NFC/NFD) karşı dayanıklı:
    bazı dosya adları (özellikle macOS'tan kopyalananlar) NFD biçiminde
    olabilir; PDF_METADATA_MAP anahtarları ise NFC. Lookup hem orijinal
    hem normalize edilmiş biçimle yapılır.
    """
    if filename in PDF_METADATA_MAP:
        return PDF_METADATA_MAP[filename]

    fn_nfc = unicodedata.normalize("NFC", filename)
    if fn_nfc in PDF_METADATA_MAP:
        return PDF_METADATA_MAP[fn_nfc]

    fn_nfd = unicodedata.normalize("NFD", filename)
    for key, value in PDF_METADATA_MAP.items():
        if unicodedata.normalize("NFD", key) == fn_nfd:
            return value

    print(f"[WARN] PDF_METADATA_MAP'te tanımlı değil: {filename} (fallback 'diger' kullanılacak)")
    return {
        "source_document": filename,
        "document_type": "diger",
        "program": "",
        "year": "",
    }


def _bbox_iou_coverage(a, b):
    """
    a bbox'ının b bbox'ı tarafından ne oranda kapsandığını döndürür (0.0-1.0).
    Metin blokları tablo bölgesine düşüyorsa duplicate'i önlemek için kullanılır.
    """
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    if ix1 <= ix0 or iy1 <= iy0:
        return 0.0
    inter = (ix1 - ix0) * (iy1 - iy0)
    a_area = max(1.0, (ax1 - ax0) * (ay1 - ay0))
    return inter / a_area


def _load_with_pymupdf(file_path, extra_metadata):
    """PyMuPDF (fitz) ile blok-bazlı okuma + tablo algılama.

    Her metin bloğu ayrı bir Document; her tablo markdown olarak ayrı Document.
    `category` etiketi sadece iki değer alır: "Table" veya "NarrativeText".
    UncategorizedText üretilmez (PyMuPDF taksonomisinde yok).
    """
    filename = os.path.basename(file_path)
    documents = []
    n_tables = 0
    n_blocks = 0
    n_pages = 0

    with fitz.open(file_path) as pdf:
        n_pages = pdf.page_count
        for page_num, page in enumerate(pdf, start=1):
            # 1) Tabloları bağımsız Document olarak çıkar (markdown formatında)
            table_bboxes = []
            try:
                tf = page.find_tables()
                tables = list(tf.tables) if tf is not None else []
            except Exception as exc:
                print(f"  [WARN] {filename} s.{page_num}: tablo dedeksiyonu hata: {exc}")
                tables = []

            for tbl in tables:
                try:
                    rows = tbl.extract()  # list[list[str|None]]
                except Exception:
                    rows = None
                if not rows:
                    continue
                md_lines = []
                for r in rows:
                    cells = [(c or "").replace("\n", " ").strip() for c in r]
                    md_lines.append("| " + " | ".join(cells) + " |")
                table_md = "\n".join(md_lines).strip()
                if table_md:
                    documents.append(Document(
                        page_content=table_md,
                        metadata={**extra_metadata, "source": file_path, "page": page_num, "category": "Table"},
                    ))
                    try:
                        table_bboxes.append(tuple(tbl.bbox))
                    except Exception:
                        pass
                    n_tables += 1

            # 2) Gövde metnini blok-bazlı oku, tablo bölgelerini hariç tut
            blocks = page.get_text("blocks", sort=True)
            for b in blocks:
                if len(b) < 7:
                    continue
                x0, y0, x1, y1, text, _block_no, block_type = b[:7]
                if block_type != 0:  # 0=text, 1=image
                    continue
                bbox = (x0, y0, x1, y1)
                if any(_bbox_iou_coverage(bbox, tb) > 0.5 for tb in table_bboxes):
                    continue  # tablo içindeki text duplicate olmasın
                text = (text or "").strip()
                if not text:
                    continue
                documents.append(Document(
                    page_content=text,
                    metadata={**extra_metadata, "source": file_path, "page": page_num, "category": "NarrativeText"},
                ))
                n_blocks += 1

    print(f"--- {filename} [PyMuPDF] | {n_pages} sayfa | {n_blocks} metin bloğu | {n_tables} tablo ---")
    return documents


def _load_with_unstructured(file_path, extra_metadata):
    """Hibrit fallback: UnstructuredPDFLoader ile okuma (eski davranış).

    `UNSTRUCTURED_OVERRIDES` set'ine eklenen dosyalar bu yoldan geçer.
    Mevcut `category` etiketleri (Title, NarrativeText, Table, UncategorizedText...) korunur
    ki `_filter_noise` (Header/Footer/PageBreak) davranışı değişmesin.
    """
    filename = os.path.basename(file_path)
    print(f"--- {filename} [Unstructured fallback] okunuyor... ---")
    loader = UnstructuredPDFLoader(file_path, mode="elements", languages=["tur"])
    data = loader.load()
    for d in data:
        d.metadata.update(extra_metadata)
    return data


def load_pdfs(directory_path):
    """Verilen klasördeki tüm PDF'leri okur. Her PDF için loader tercihi:
    - UNSTRUCTURED_OVERRIDES içindeyse → Unstructured
    - Değilse → PyMuPDF (varsayılan)
    """
    documents = []
    files = sorted(f for f in os.listdir(directory_path) if f.lower().endswith(".pdf"))
    for filename in files:
        file_path = os.path.join(directory_path, filename)
        extra_metadata = _get_metadata_for_file(filename)

        if filename in UNSTRUCTURED_OVERRIDES:
            documents.extend(_load_with_unstructured(file_path, extra_metadata))
        else:
            documents.extend(_load_with_pymupdf(file_path, extra_metadata))

    print(f"Toplam {len(documents)} veri parçası çıkarıldı.")
    return documents


if __name__ == "__main__":
    import sys
    # Windows konsolunda Türkçe karakterler için UTF-8 zorla
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    _backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    raw_data_path = os.path.join(_backend_root, "data", "2209A_pdf")
    all_docs = load_pdfs(raw_data_path)

    # Metadata doğrulama
    print("\n[DEBUG] İlk 3 dokümanın metadata bilgisi:")
    for i, doc in enumerate(all_docs[:3]):
        print(f"  [{i}] source_document: {doc.metadata.get('source_document')}")
        print(f"      document_type: {doc.metadata.get('document_type')}")
        print(f"      program: {doc.metadata.get('program')}")
        print(f"      year: {doc.metadata.get('year')}")
        print(f"      category: {doc.metadata.get('category')}")
        print(f"      page: {doc.metadata.get('page')}")
