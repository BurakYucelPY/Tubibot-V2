import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.ingestion.pdf_loader import load_pdfs
from src.ingestion.processor import process_and_chunk_documents
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
# İŞTE O HAYAT KURTARAN FİLTRE
from langchain_community.vectorstores.utils import filter_complex_metadata

def build_vector_database():
    print("\n[INFO] Vektör Veritabanı (Vector DB) inşa süreci başlatılıyor...")
    
    raw_data_path = "data/raw_pdf"
    raw_docs = load_pdfs(raw_data_path)
    chunks = process_and_chunk_documents(raw_docs)
    
    # --- KOORDİNAT TEMİZLİĞİ BURADA YAPILIYOR ---
    print("[INFO] Karmaşık metadata verileri (piksel koordinatları vb.) filtreleniyor...")
    filtered_chunks = filter_complex_metadata(chunks)
    
    model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    print(f"\n[INFO] Embedding modeli yükleniyor: {model_name}")
    embeddings = HuggingFaceEmbeddings(model_name=model_name)
    
    persist_directory = "data/vector_db"
    print("[INFO] Vektörler hesaplanıyor ve veritabanına kaydediliyor...")
    
    # Veritabanına pis 'chunks' değil, temizlenmiş 'filtered_chunks' gidiyor
    vector_db = Chroma.from_documents(
        documents=filtered_chunks, 
        embedding=embeddings, 
        persist_directory=persist_directory
    )
    
    print(f"\n[SUCCESS] İşlem tamamlandı! Toplam {len(filtered_chunks)} chunk vektörleştirilip '{persist_directory}' konumuna kalıcı olarak kaydedildi.")
    return vector_db

if __name__ == "__main__":
    os.makedirs("data/vector_db", exist_ok=True)
    build_vector_database()