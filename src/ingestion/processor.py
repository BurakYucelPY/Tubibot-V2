import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.ingestion.pdf_loader import load_pdfs

def process_and_chunk_documents(raw_documents):
    """
    Ham belgeleri (raw documents) filtreler ve RAG sistemi için uygun chunk'lara böler.
    Tablo yapıları bütünlüğünü korur, metinler belirlenen boyutlara göre parçalanır.
    """
    cleaned_documents = []
    
    print("\n[INFO] Aşama 1: Veri Filtreleme (Noise Reduction) Başlatıldı.")
    # Gürültü verilerinin (Header, Footer vb.) temizlenmesi
    for doc in raw_documents:
        category = doc.metadata.get("category", "")
        if category in ["Header", "Footer", "PageBreak", "UncategorizedText"]:
            continue
        cleaned_documents.append(doc)
        
    print(f"[INFO] Filtreleme tamamlandı: {len(raw_documents)} ham belgeden {len(cleaned_documents)} geçerli belge elde edildi.")

    print("\n[INFO] Aşama 2: Metin Parçalama (Text Chunking) Başlatıldı.")
    
    # RecursiveCharacterTextSplitter konfigürasyonu
    # chunk_size: Her bir parçanın maksimum karakter sayısı
    # chunk_overlap: Bağlam (context) kaybını önlemek için önceki parçadan alınacak karakter sayısı
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    final_chunks = []
    texts_to_split = []
    
    # Yapısal ayırma: Tablolar doğrudan vektörleştirilecek, metinler chunklanacak
    for doc in cleaned_documents:
        if doc.metadata.get("category") == "Table":
            final_chunks.append(doc)
        else:
            texts_to_split.append(doc)
            
    # Metinlerin parçalanması (Chunking)
    split_texts = text_splitter.split_documents(texts_to_split)
    
    # Bütünleşik veri setinin oluşturulması
    final_chunks.extend(split_texts)
    
    print(f"[INFO] İşlem tamamlandı. Vektör veritabanı (Vector DB) için toplam {len(final_chunks)} chunk oluşturuldu.")
    return final_chunks

if __name__ == "__main__":
    raw_data_path = "data/raw_pdf"
    print("[INFO] PDF yükleme işlemi başlatılıyor...")
    raw_docs = load_pdfs(raw_data_path)
    
    processed_chunks = process_and_chunk_documents(raw_docs)
    
    # Doğrulama: İlk chunk'ın içeriğini kontrol etme
    print("\n[DEBUG] Örnek Chunk (Index 0):")
    print("-" * 50)
    print(processed_chunks[0].page_content)
    print("-" * 50)