import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from langchain_huggingface import HuggingFaceEmbeddings
# YENİ VE MODERN IMPORT BURADA:
from langchain_chroma import Chroma 

def get_retriever():
    model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embeddings = HuggingFaceEmbeddings(model_name=model_name)
    
    persist_directory = "data/vector_db"
    
    vector_db = Chroma(
        persist_directory=persist_directory, 
        embedding_function=embeddings
    )
    
    # k=3'tü, k=5 yaptık! Artık ilk 5 lokmayı getirecek, rakamı kaçırmayacağız.
    retriever = vector_db.as_retriever(search_kwargs={"k": 5})
    return retriever

if __name__ == "__main__":
    print("\n[INFO] Botun hafızası test ediliyor...")
    
    arama_motoru = get_retriever()
    
    # Soruyu biraz daha nokta atışı yapalım
    soru = "Sürdürülebilir Kalkınma Amaçları (SKA) kapsamında yoksulluğu ve açlığı bitirmek için belirlenen hedefler nelerdir?"
    print(f"\n[SORU] {soru}")
    print("=" * 60)
    
    bulunan_belgeler = arama_motoru.invoke(soru)
    
    for i, belge in enumerate(bulunan_belgeler, 1):
        print(f"\n[KAYNAK {i}]")
        print(belge.page_content)
        print("-" * 60)