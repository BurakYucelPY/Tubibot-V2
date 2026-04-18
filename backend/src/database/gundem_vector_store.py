import os
import shutil
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from langchain_community.vectorstores import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata

from src.database.vector_store import E5Embeddings
from src.ingestion.json_loader import load_gundem_documents
from src.ingestion.processor import process_and_chunk_documents


def build_gundem_vector_database():
    """
    Gündem (duyuru + haber) için ayrı bir Chroma vektör veritabanı kurar.
    Ana PDF DB'sine (backend/data/vector_db) DOKUNMAZ.
    Persist konumu: backend/data/gundem_vector_db
    """
    print("\n[INFO] Gündem Vektör DB inşa süreci başlatılıyor...")

    backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

    # 1) JSON'lardan Document listesi üret
    json_docs = load_gundem_documents(backend_root)
    if not json_docs:
        print("[WARN] Gündem için yüklenecek belge bulunamadı. Boş DB oluşturulmayacak.")
        return None

    # 2) Mevcut chunking pipeline'ı
    chunks = process_and_chunk_documents(json_docs)

    # 3) Kompleks metadata temizliği
    print("[INFO] Karmaşık metadata verileri filtreleniyor...")
    filtered_chunks = filter_complex_metadata(chunks)

    # 4) Embedding modeli (ana DB ile aynı E5Embeddings)
    model_name = "intfloat/multilingual-e5-large"
    print(f"\n[INFO] (TÜRKÇE ODAKLI) Embedding modeli yükleniyor: {model_name}")
    embeddings = E5Embeddings(model_name=model_name)

    # 5) Persist dizini — ana DB'den ayrı
    persist_directory = os.path.join(backend_root, "data", "gundem_vector_db")

    if os.path.exists(persist_directory):
        print(f"[INFO] Eski gündem DB siliniyor: {persist_directory}")
        shutil.rmtree(persist_directory)
    os.makedirs(persist_directory, exist_ok=True)

    print("[INFO] Vektörler hesaplanıyor ve gündem DB'sine kaydediliyor...")
    vector_db = Chroma.from_documents(
        documents=filtered_chunks,
        embedding=embeddings,
        persist_directory=persist_directory,
    )

    sample = vector_db.get(limit=3, include=["metadatas"])
    print(f"\n[SUCCESS] Toplam {len(filtered_chunks)} gündem chunk'ı vektörleştirildi.")
    print(f"[INFO] Örnek metadata: {sample['metadatas'][0] if sample['metadatas'] else 'Boş'}")

    return vector_db


if __name__ == "__main__":
    build_gundem_vector_database()
