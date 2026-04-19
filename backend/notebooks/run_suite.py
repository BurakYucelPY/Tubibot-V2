"""
notebooks/run_suite.py

Tüm alt klasörlerdeki test_*.py dosyalarını tek process içinde sırayla çalıştırır.
Her dosya kendi `if __name__ == "__main__"` bloğunda `sys.exit(runner.summary())`
döndürdüğü için exit code'ları biriktirip sonda özet basar.

Kullanım:
  cd backend
  python notebooks/run_suite.py
  python notebooks/run_suite.py --only ingestion,api
  python notebooks/run_suite.py --skip e2e,diagnostics

Notlar:
- Tek process → TestClient + retriever + cross-encoder bir kez yüklenir.
- diagnostics/ varsayılan olarak çalışır; sadece rapor basar (PASS/FAIL yok).
- Runner, beklenmeyen crash'leri de yakalar ve FAIL olarak sayar.
"""
import argparse
import os
import runpy
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers.bootstrap import setup_backend_path  # noqa: E402

setup_backend_path()

NOTEBOOKS_DIR = os.path.dirname(os.path.abspath(__file__))

# Alan → dosya çalıştırma sırası (hızlıdan yavaşa).
SUITE_ORDER = [
    ("ingestion", [
        "test_chunking.py",
        "test_pdf_metadata.py",
        "test_pdf_loader.py",
        "test_json_loader.py",
        "test_processor_pdf.py",
        "test_processor_gundem.py",
    ]),
    ("database", [
        "test_vector_db.py",
        "test_gundem_vector_db.py",
        "test_e5_embeddings.py",
    ]),
    ("retrieval", [
        "test_query_type_hints.py",
        "test_hybrid_retrieval.py",
        "test_retriever_pdf.py",
        "test_retriever_gundem.py",
    ]),
    ("generation", [
        "test_prompt.py",
        "test_gundem_prompt.py",
        "test_generator.py",
        "test_query_expansion.py",
    ]),
    ("api", [
        "test_schemas.py",
        "test_health_and_startup.py",
        "test_chat_endpoint.py",
        "test_chat_gundem_endpoint.py",
        "test_dokumanlar_endpoint.py",
        "test_icerik_endpoints.py",
    ]),
    ("e2e", [
        "test_end_to_end.py",
        "test_rag_regression.py",
        "test_hallucination_guard.py",
    ]),
    ("diagnostics", [
        # Sadece rapor — PASS/FAIL yok, exit code 0 beklenir.
        "inspect_chunks.py",
        # perf_bench.py isteğe bağlı; varsayılan olarak atlanır (ağır).
    ]),
]


def _run_file(path: str) -> tuple[int, float]:
    """Dosyayı __main__ olarak çalıştır, exit code ve süre dönder."""
    t0 = time.perf_counter()
    try:
        runpy.run_path(path, run_name="__main__")
        code = 0
    except SystemExit as e:
        code = int(e.code) if isinstance(e.code, int) else (0 if e.code is None else 1)
    except Exception:
        print(f"\n❌ [CRASH] {path}")
        traceback.print_exc()
        code = 2
    dt = time.perf_counter() - t0
    return code, dt


def main():
    parser = argparse.ArgumentParser(description="Tubibot V2 notebook test süiti")
    parser.add_argument("--only", type=str, help="Sadece bu alanları çalıştır (virgüllü)")
    parser.add_argument("--skip", type=str, help="Bu alanları atla (virgüllü)")
    parser.add_argument("--list", action="store_true", help="Süiti listele, çalıştırma")
    args = parser.parse_args()

    only = set((args.only or "").split(",")) - {""}
    skip = set((args.skip or "").split(",")) - {""}

    if args.list:
        for area, files in SUITE_ORDER:
            print(f"[{area}]")
            for f in files:
                print(f"  - {f}")
        return 0

    results: list[tuple[str, str, int, float]] = []  # (area, file, code, dt)
    t_all = time.perf_counter()

    for area, files in SUITE_ORDER:
        if only and area not in only:
            continue
        if area in skip:
            continue

        area_dir = os.path.join(NOTEBOOKS_DIR, area)
        if not os.path.isdir(area_dir):
            print(f"\n⚠️  [{area}] dizin yok — atlandı.")
            continue

        print(f"\n{'#'*72}")
        print(f"#  {area.upper()}")
        print(f"{'#'*72}")

        for fname in files:
            fpath = os.path.join(area_dir, fname)
            if not os.path.isfile(fpath):
                print(f"\n⚠️  {area}/{fname} yok — atlandı.")
                continue

            print(f"\n{'-'*72}")
            print(f">>> {area}/{fname}")
            print("-"*72)
            code, dt = _run_file(fpath)
            results.append((area, fname, code, dt))
            mark = "✅" if code == 0 else "❌"
            print(f"{mark} {area}/{fname}  ({dt:.2f} sn, exit={code})")

    total_dt = time.perf_counter() - t_all

    # --- Özet ---
    print("\n" + "="*72)
    print("SÜİT ÖZETİ")
    print("="*72)

    by_area: dict[str, list[tuple[str, int, float]]] = {}
    for area, fname, code, dt in results:
        by_area.setdefault(area, []).append((fname, code, dt))

    overall_ok = True
    for area, rows in by_area.items():
        ok = sum(1 for _, c, _ in rows if c == 0)
        total = len(rows)
        if ok != total:
            overall_ok = False
        print(f"  [{area}] {ok}/{total} geçti")
        for fname, code, dt in rows:
            mark = "✅" if code == 0 else "❌"
            print(f"      {mark} {fname:<40} ({dt:5.2f} sn)")

    total_files = len(results)
    total_ok = sum(1 for _, _, c, _ in results if c == 0)
    print(f"\nTOPLAM: {total_ok}/{total_files} dosya  |  süre: {total_dt:.2f} sn")
    return 0 if overall_ok and total_files > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
