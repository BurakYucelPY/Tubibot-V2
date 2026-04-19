"""
database/test_e5_embeddings.py

E5Embeddings sarmalayıcı davranışı:
- embed_documents [passage: ...] prefix ekler
- embed_query [query: ...] prefix ekler → iki vektör FARKLI olmalı
- Embedding boyutu = 1024 (multilingual-e5-large)
- Aynı metnin passage + query temsilleri yüksek cosine similarity'de (> 0.5)
"""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from _helpers.bootstrap import setup_backend_path
setup_backend_path()

from _helpers.runner import TestRunner


def _cosine(a, b):
    import math
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def main():
    from src.database.vector_store import E5Embeddings

    runner = TestRunner("database/test_e5_embeddings")

    runner.info("E5 modeli yükleniyor (ilk çağrıda ~15sn)...")
    emb = E5Embeddings(model_name="intfloat/multilingual-e5-large")

    # Embedding boyutu
    q_vec = emb.embed_query("Tübitak 2209-A nedir?")
    runner.check(
        "embed_query boyutu = 1024",
        len(q_vec) == 1024,
        f"dim={len(q_vec)}",
    )

    d_vecs = emb.embed_documents(["Tübitak 2209-A nedir?"])
    runner.check(
        "embed_documents tek giriş için tek vektör döner",
        len(d_vecs) == 1,
    )
    runner.check(
        "embed_documents boyutu = 1024",
        len(d_vecs[0]) == 1024,
    )

    # Prefix farkı — aynı metin olmasına rağmen passage: vs query: farklı
    passage = d_vecs[0]
    query = q_vec
    eq = all(abs(a - b) < 1e-6 for a, b in zip(passage, query))
    runner.check(
        "passage: prefix ≠ query: prefix (iki vektör farklı)",
        not eq,
    )

    # Yüksek benzerlik: aynı anlamdaki query/passage cosine > 0.5
    sim = _cosine(passage, query)
    runner.info(f"Aynı metnin query vs passage cosine: {sim:.3f}")
    runner.check("cosine(query, passage) > 0.5", sim > 0.5)

    # İki farklı dokümanın vektörleri de 1024
    multi = emb.embed_documents([
        "Tübitak 2209-A araştırma projeleri için destek verir.",
        "Sürdürülebilir Kalkınma Amaçları 17 başlık altında incelenir.",
    ])
    runner.check(
        "Çoklu doküman embed_documents boyutu tutarlı",
        all(len(v) == 1024 for v in multi),
    )
    sim_diff = _cosine(multi[0], multi[1])
    runner.info(f"Farklı konulardaki iki vektörün cosine'i: {sim_diff:.3f}")

    return runner.summary()


if __name__ == "__main__":
    sys.exit(main())
