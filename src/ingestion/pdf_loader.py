import os
from langchain_community.document_loaders import UnstructuredPDFLoader

def load_pdfs(directory_path):
    """
    Belirtilen klasördeki tüm PDF'leri okur ve yapısal olarak ayıklar.
    """
    documents = []
    
    # Klasördeki dosyaları tara
    for filename in os.listdir(directory_path):
        if filename.endswith(".pdf"):
            file_path = os.path.join(directory_path, filename)
            print(f"--- {filename} işleniyor... ---")
            
            # mode="elements" ile tablo/metin ayrımı yapıyoruz
            # languages=["tur"] ile Türkçe karakterleri (ş, ğ, ç, ö vb.) hatasız okutuyoruz
            loader = UnstructuredPDFLoader(file_path, mode="elements", languages=["tur"])
            data = loader.load()
            documents.extend(data)
            
    print(f"Toplam {len(documents)} veri parçası (element) çıkarıldı.")
    return documents

if __name__ == "__main__":
    # Test amaçlı klasör yolunu veriyoruz
    raw_data_path = "data/raw_pdf"
    all_docs = load_pdfs(raw_data_path)
    
    # İlk 5 parçayı ekrana basıp neye benzediğine bakalım
    for doc in all_docs[:5]:
        print(f"\nTip: {doc.metadata.get('category')}")
        print(f"İçerik: {doc.page_content[:100]}...")