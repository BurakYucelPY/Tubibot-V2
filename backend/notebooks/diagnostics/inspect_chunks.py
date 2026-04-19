"""
diagnostics/inspect_chunks.py

Tanı aracı — PASS/FAIL üretmez, vektör DB'deki chunk dağılımını raporlar.

- PDF vector_db: source_document bazında chunk sayıları, örnek section_heading'ler,
  ortalama/min/max chunk uzunluğu, boş metadata alanı sayaçları.
- Gündem vector_db (varsa): document_type dağılımı, kaynak bazında sayılar.

Sadece `print` çıktısı — CI'ya değil geliştiriciye yönelik.
"""
import os, sys
from collections import Counter, defaultdict
from statistics import mean

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from _helpers.bootstrap import setup_backend_path
BACKEND_ROOT = setup_backend_path()


def _inspect(persist_dir: str, label: str):
    print(f"\n{'='*72}")
    print(f"[{label}]  {persist_dir}")
    print("="*72)

    if not os.path.isdir(persist_dir):
        print(f"  ⚠️  Dizin yok — atlandı.")
        return

    from langchain_chroma import Chroma
    from src.database.vector_store import E5Embeddings

    emb = E5Embeddings()
    db = Chroma(persist_directory=persist_dir, embedding_function=emb)
    data = db.get()

    docs = data.get("documents", [])
    metas = data.get("metadatas", [])
    print(f"Toplam chunk: {len(docs)}")
    if not docs:
        return

    # Uzunluk istatistikleri
    lens = [len(d or "") for d in docs]
    print(f"Chunk uzunluğu — min: {min(lens)}  max: {max(lens)}  ort: {mean(lens):.1f}")

    # source_document dağılımı
    sources = Counter((m or {}).get("source_document") for m in metas)
    print(f"\nsource_document dağılımı (top 10):")
    for s, c in sources.most_common(10):
        print(f"  {c:>5}  {s}")

    # document_type dağılımı
    types = Counter((m or {}).get("document_type") for m in metas)
    print(f"\ndocument_type dağılımı:")
    for t, c in types.most_common():
        print(f"  {c:>5}  {t!r}")

    # section_heading örnekleri (kaynak bazlı 2 örnek)
    sec_examples = defaultdict(list)
    for m in metas:
        s = (m or {}).get("source_document")
        sh = (m or {}).get("section_heading")
        if sh and len(sec_examples[s]) < 2:
            sec_examples[s].append(sh)
    print(f"\nsection_heading örnekleri (her kaynaktan 2):")
    for s in list(sec_examples.keys())[:10]:
        print(f"  {s}: {sec_examples[s]}")

    # Boş metadata alanları
    check_fields = ("source_document", "document_type", "section_heading", "year")
    empty_counts = {f: 0 for f in check_fields}
    for m in metas:
        md = m or {}
        for f in check_fields:
            if not md.get(f):
                empty_counts[f] += 1
    print(f"\nBoş metadata alanı sayıları (toplam {len(metas)} chunk içinden):")
    for f, c in empty_counts.items():
        print(f"  {c:>5}  {f}")


def main():
    pdf_db = os.path.join(BACKEND_ROOT, "data", "vector_db")
    gundem_db = os.path.join(BACKEND_ROOT, "data", "gundem_vector_db")

    _inspect(pdf_db, "PDF vector_db")
    _inspect(gundem_db, "Gündem vector_db")

    print("\n" + "="*72)
    print("Tanı tamamlandı.")
    print("="*72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
