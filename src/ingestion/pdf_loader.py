import os
from langchain_community.document_loaders import UnstructuredPDFLoader, PyPDFLoader

def load_pdfs(directory_path):
    documents = []
    
    for filename in os.listdir(directory_path):
        if filename.endswith(".pdf"):
            file_path = os.path.join(directory_path, filename)
            
            # EĞER DOSYA SKA REHBERİ İSE: Satır satır okuyan PyPDF kullan
            if "SKA" in filename or "Göstergeleri" in filename:
                print(f"--- {filename} [PyPDF] ile okunuyor (Satır koruma modu)... ---")
                loader = PyPDFLoader(file_path)
                data = loader.load()
                # PyPDF parçalara kategori vermez, bizim filtreye takılmasın diye 'NarrativeText' etiketi basıyoruz
                for d in data:
                    d.metadata["category"] = "NarrativeText"
                documents.extend(data)
                
            # EĞER DOSYA TÜBİTAK FORMUYSA: Tabloları çözen Unstructured kullan
            else:
                print(f"--- {filename} [Unstructured] ile okunuyor (Tablo/Başlık modu)... ---")
                loader = UnstructuredPDFLoader(file_path, mode="elements", languages=["tur"])
                data = loader.load()
                documents.extend(data)
            
    print(f"Toplam {len(documents)} veri parçası çıkarıldı.")
    return documents

if __name__ == "__main__":
    raw_data_path = "data/raw_pdf"
    all_docs = load_pdfs(raw_data_path)