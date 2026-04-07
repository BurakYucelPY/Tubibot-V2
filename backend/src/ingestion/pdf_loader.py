import os
from langchain_community.document_loaders import UnstructuredPDFLoader, PyPDFLoader

# ====================================================================
# METADATA MAPPING: Her PDF dosyasına anlamlı metadata ekliyoruz.
# Bu sayede chunk'lar hangi belgeden/türden geldiğini bilecek.
# ====================================================================
PDF_METADATA_MAP = {
    "2209-A_2025_Yili_Cagri_Duyurusu_09102025.pdf": {
        "source_document": "2209-A 2025 Yılı Çağrı Duyurusu",
        "document_type": "cagri_duyurusu",
        "year": "2025",
    },
    "2209-A_arastirma_onerisi_formu_09102025.pdf": {
        "source_document": "2209-A Araştırma Önerisi Formu",
        "document_type": "basvuru_formu",
        "year": "2025",
    },
    "Oncelikli_Alanlar_2025-2.pdf": {
        "source_document": "2025 Öncelikli Alanlar Listesi",
        "document_type": "oncelikli_alanlar",
        "year": "2025",
    },
    "Öncelikli Alanlar.pdf": {
        "source_document": "2025 Öncelikli Alanlar Listesi",
        "document_type": "oncelikli_alanlar",
        "year": "2025",
    },
    "SKA Kapsamı ve Göstergeleri.pdf": {
        "source_document": "Sürdürülebilir Kalkınma Amaçları Kapsamı ve Göstergeleri",
        "document_type": "ska_rehberi",
        "year": "",
    },
    "SKA_Surdurulebilir_Kalkinma.pdf": {
        "source_document": "Sürdürülebilir Kalkınma Amaçları Kapsamı ve Göstergeleri",
        "document_type": "ska_rehberi",
        "year": "",
    },
    "kimlerbasvurur.pdf": {
        "source_document": "2209-A Kimler Başvurabilir",
        "document_type": "basvuru_kosullari",
        "year": "2025",
    },
}


def _get_metadata_for_file(filename):
    """Dosya adına göre metadata mapping'den bilgi döndür."""
    if filename in PDF_METADATA_MAP:
        return PDF_METADATA_MAP[filename]
    # Bilinmeyen dosyalar için fallback
    return {
        "source_document": filename,
        "document_type": "diger",
        "year": "",
    }


def load_pdfs(directory_path):
    documents = []
    
    for filename in os.listdir(directory_path):
        if filename.endswith(".pdf"):
            file_path = os.path.join(directory_path, filename)
            extra_metadata = _get_metadata_for_file(filename)
            
            # Artık tüm belgeler temiz (Word/PDF düz formunda) olduğu için 
            # başlık ve madde ayrımlarını daha iyi anlaması adına hepsini Unstructured ile okuyoruz.
            print(f"--- {filename} [Unstructured] ile okunuyor (Tablo/Başlık modu)... ---")
            loader = UnstructuredPDFLoader(file_path, mode="elements", languages=["tur"])
            data = loader.load()
            for d in data:
                d.metadata.update(extra_metadata)
            documents.extend(data)
            
    print(f"Toplam {len(documents)} veri parçası çıkarıldı.")
    return documents


if __name__ == "__main__":
    raw_data_path = "backend/data/2209A_pdf"
    all_docs = load_pdfs(raw_data_path)
    
    # Metadata doğrulama
    print("\n[DEBUG] İlk 3 dokümanın metadata bilgisi:")
    for i, doc in enumerate(all_docs[:3]):
        print(f"  [{i}] source_document: {doc.metadata.get('source_document')}")
        print(f"      document_type: {doc.metadata.get('document_type')}")
        print(f"      year: {doc.metadata.get('year')}")
        print(f"      category: {doc.metadata.get('category')}")