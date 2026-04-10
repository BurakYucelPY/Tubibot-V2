"""Vektör DB'deki tüm belge türlerini kontrol et."""
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large")
_backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
db = Chroma(persist_directory=os.path.join(_backend_root, "data", "vector_db"), embedding_function=embeddings)

all_data = db.get(include=["metadatas"])

types = set()
sources = set()
type_counts = {}
for m in all_data["metadatas"]:
    t = m.get("document_type", "YOK")
    s = m.get("source_document", "YOK")
    types.add(t)
    sources.add(s)
    type_counts[t] = type_counts.get(t, 0) + 1

ids = all_data["ids"]
print(f"Toplam chunk: {len(ids)}")
print(f"\nBelge turleri: {types}")
print(f"\nKaynaklar: {sources}")
print(f"\nTur bazinda dagilim:")
for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
    print(f"  {t}: {c} chunk")
