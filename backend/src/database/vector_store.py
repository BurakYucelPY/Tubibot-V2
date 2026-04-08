import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.ingestion.pdf_loader import load_pdfs
from src.ingestion.processor import process_and_chunk_documents
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata


class E5Embeddings(HuggingFaceEmbeddings):
    """
    intfloat/multilingual-e5-large modeli için prefix wrapper.
    - Dokümanlar: "passage: " prefix'i ile embed edilir
    - Sorgular: "query: " prefix'i ile embed edilir
    Bu sayede page_content temiz kalır, prefix sadece embedding hesabında eklenir.
    """

    def embed_documents(self, texts):
        prefixed = [f"passage: {t}" for t in texts]
        return super().embed_documents(prefixed)

    def embed_query(self, text):
        prefixed = f"query: {text}"
        return super().embed_query(prefixed)


def build_vector_database():
    print("\n[INFO] Vektör Veritabanı (Vector DB) inşa süreci başlatılıyor...")

    raw_data_path = "backend/data/2209A_pdf"
    raw_docs = load_pdfs(raw_data_path)
    chunks = process_and_chunk_documents(raw_docs)

    # Kompleks metadata temizliği (piksel koordinatları vb.)
    print("[INFO] Karmaşık metadata verileri filtreleniyor...")
    filtered_chunks = filter_complex_metadata(chunks)

    model_name = "intfloat/multilingual-e5-large"
    print(f"\n[INFO] (TÜRKÇE ODAKLI) Embedding modeli yükleniyor: {model_name}")
    embeddings = E5Embeddings(model_name=model_name)

    persist_directory = "backend/data/vector_db"

    # Eski veritabanını temizle (varsa)
    if os.path.exists(persist_directory):
        import shutil
        print(f"[INFO] Eski vektör veritabanı siliniyor: {persist_directory}")
        shutil.rmtree(persist_directory)
        os.makedirs(persist_directory, exist_ok=True)

    print("[INFO] Vektörler hesaplanıyor ve veritabanına kaydediliyor...")

    vector_db = Chroma.from_documents(
        documents=filtered_chunks,
        embedding=embeddings,
        persist_directory=persist_directory
    )

    # Doğrulama: metadata kontrolü
    sample = vector_db.get(limit=3, include=["metadatas"])
    print(f"\n[SUCCESS] Toplam {len(filtered_chunks)} chunk vektörleştirildi.")
    print(f"[INFO] Örnek metadata: {sample['metadatas'][0] if sample['metadatas'] else 'Boş'}")

    return vector_db

if __name__ == "__main__":
    os.makedirs("backend/data/vector_db", exist_ok=True)
    build_vector_database()
