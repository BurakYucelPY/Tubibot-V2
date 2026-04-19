"""
diagnostics/perf_bench.py

Tanı aracı — PASS/FAIL üretmez, latency profilini raporlar.

Ölçümler:
- Retriever cold-start (ilk invoke: cross-encoder yüklemesi + ilk arama)
- Retriever warm (sonraki sorular)
- get_rag_chain() end-to-end (LLM dahil) — ilk token / toplam süre yaklaşık
- Gündem retriever (varsa)

Not: Wall-clock zamanı — makine yüküne bağlı, mutlak değerler karşılaştırılabilir değil.
"""
import os, sys, time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from _helpers.bootstrap import setup_backend_path
BACKEND_ROOT = setup_backend_path()


def _timed(label, fn):
    t0 = time.perf_counter()
    out = fn()
    dt = time.perf_counter() - t0
    print(f"  [{dt*1000:>7.1f} ms]  {label}")
    return out, dt


def bench_pdf_retriever():
    print("\n" + "="*72)
    print("[PDF Retriever]")
    print("="*72)
    from src.retrieval.retriever_pdf import get_retriever
    retriever, _ = _timed("get_retriever() (factory)", lambda: get_retriever())

    sorular = [
        "2209-A'ya kimler başvurabilir?",
        "SKA 13 iklim değişikliği hedefi nedir?",
        "Öncelikli alanlar hangileridir?",
        "TÜBİTAK Mükemmeliyet Rehberi neleri içerir?",
        "2209-A proje önerisi formunda hangi bölümler var?",
    ]

    cold = None
    warm_times = []
    for i, q in enumerate(sorular, 1):
        label = f"invoke #{i} {'(COLD)' if i == 1 else '(warm)'}: {q[:40]}..."
        _, dt = _timed(label, lambda q=q: retriever.invoke(q))
        if i == 1:
            cold = dt
        else:
            warm_times.append(dt)

    if warm_times:
        avg = sum(warm_times) / len(warm_times)
        print(f"\n  Özet — cold: {cold*1000:.0f} ms,  warm ort: {avg*1000:.0f} ms,  n_warm={len(warm_times)}")


def bench_gundem_retriever():
    print("\n" + "="*72)
    print("[Gündem Retriever]")
    print("="*72)
    gundem_db = os.path.join(BACKEND_ROOT, "data", "gundem_vector_db")
    if not os.path.isdir(gundem_db):
        print("  ⚠️  gundem_vector_db yok — atlandı.")
        return

    from src.retrieval.retriever_gundem import get_gundem_retriever
    retriever, _ = _timed("get_gundem_retriever()", lambda: get_gundem_retriever())

    sorular = [
        "Son duyurular nelerdir?",
        "Yeni açılan çağrılar",
        "TÜBİTAK haberleri",
    ]
    for i, q in enumerate(sorular, 1):
        _timed(f"invoke #{i}: {q}", lambda q=q: retriever.invoke(q))


def bench_end_to_end():
    print("\n" + "="*72)
    print("[End-to-end (PDF RAG + LLM)]")
    print("="*72)
    if not os.getenv("GROQ_API_KEY"):
        print("  ⚠️  GROQ_API_KEY yok — atlandı.")
        return

    from main import get_rag_chain
    chain, _ = _timed("get_rag_chain()", lambda: get_rag_chain())

    sorular = [
        "2209-A'ya kimler başvurabilir?",
        "SKA 13 hedefleri nelerdir?",
    ]
    for i, q in enumerate(sorular, 1):
        ans, dt = _timed(f"chain #{i}: {q[:40]}...", lambda q=q: chain(q))
        print(f"      yanıt uzunluğu: {len(ans or '')} char")


def main():
    bench_pdf_retriever()
    bench_gundem_retriever()
    bench_end_to_end()
    print("\n" + "="*72)
    print("Perf bench tamamlandı.")
    print("="*72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
