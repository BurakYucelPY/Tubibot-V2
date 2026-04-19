"""
Tüm notebook test dosyalarının ilk satırları için tek noktadan import bootstrap'i.

Kullanım (her test dosyasının başında):
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from _helpers.bootstrap import setup_backend_path
    BACKEND_ROOT = setup_backend_path()

setup_backend_path():
- `backend/` dizinini sys.path'e ekler (src.*, api.*, main, scraper_* import'ları için).
- `backend/notebooks/` dizinini de ekler (_helpers.* import zinciri için).
- Mutlak yol olarak backend_root döndürür (data/, duyurular.json vb. için).
"""
import os
import sys


def setup_backend_path():
    here = os.path.dirname(os.path.abspath(__file__))           # .../notebooks/_helpers
    notebooks_root = os.path.dirname(here)                      # .../notebooks
    backend_root = os.path.dirname(notebooks_root)              # .../backend

    for p in (backend_root, notebooks_root):
        if p not in sys.path:
            sys.path.insert(0, p)

    return backend_root


if __name__ == "__main__":
    # Akıl sağlığı kontrolü: bootstrap çağrıldığında backend içindeki birkaç modül
    # import edilebilmeli.
    root = setup_backend_path()
    print(f"[bootstrap] backend_root = {root}")

    trial = [
        "src.ingestion.processor",
        "src.retrieval.retriever",
        "src.database.vector_store",
        "src.generation.generator",
        "api.formatters",
        "api.prompts",
        "api.schemas",
    ]

    for modname in trial:
        try:
            __import__(modname)
            print(f"  ✅ import {modname}")
        except Exception as e:
            print(f"  ❌ import {modname} — {type(e).__name__}: {e}")
