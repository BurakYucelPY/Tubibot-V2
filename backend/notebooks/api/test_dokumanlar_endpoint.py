"""
api/test_dokumanlar_endpoint.py

Doküman endpoint'leri:
- GET /api/dokumanlar → list, her item {filename, title, size_bytes, download_url, thumbnail_url}
- GET /api/dokumanlar/thumb/<filename>  → 200 + image/jpeg + >0 bayt
- GET /api/dokumanlar/indir/<filename>  → 200 + application/pdf + >0 bayt
- Var olmayan dosya (thumb/indir) → 404
- .pdf olmayan path (thumb) → 404

Live: gerçek PDF_DIR'e bakar, PyMuPDF ile thumbnail üretir.
"""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from _helpers.bootstrap import setup_backend_path
setup_backend_path()

from _helpers.runner import TestRunner
from _helpers.api_client import get_test_client


def main():
    runner = TestRunner("api/test_dokumanlar_endpoint")

    from api.paths import PDF_DIR

    client = get_test_client()

    # --- /api/dokumanlar listesi ---
    resp = client.get("/api/dokumanlar")
    runner.check("GET /api/dokumanlar → 200", resp.status_code == 200, f"status={resp.status_code}")

    items = []
    try:
        items = resp.json()
    except Exception as e:
        runner.check(f"/api/dokumanlar JSON parse — {type(e).__name__}", False, str(e)[:80])

    runner.check("/api/dokumanlar list tipinde", isinstance(items, list))

    if not os.path.isdir(PDF_DIR):
        runner.info(f"PDF_DIR yok: {PDF_DIR} — sonraki testler atlanacak.")
        return runner.summary()

    runner.info(f"Dokuman sayısı: {len(items)}")
    runner.check("En az 1 doküman listelendi", len(items) >= 1)

    if items:
        first = items[0]
        required_keys = ("filename", "title", "size_bytes", "download_url", "thumbnail_url")
        for k in required_keys:
            runner.check(f"item['{k}'] mevcut", k in first)
        runner.check(
            "filename .pdf ile bitiyor",
            isinstance(first.get("filename"), str) and first["filename"].lower().endswith(".pdf"),
        )
        runner.check("size_bytes > 0", isinstance(first.get("size_bytes"), int) and first["size_bytes"] > 0)

        target = first["filename"]
        runner.info(f"Test hedefi: {target}")

        # --- Thumbnail ---
        thumb_resp = client.get(f"/api/dokumanlar/thumb/{target}")
        runner.check(
            f"GET thumb/{target} → 200",
            thumb_resp.status_code == 200,
            f"status={thumb_resp.status_code}",
        )
        runner.check(
            "Thumbnail content-type image/jpeg",
            "image/jpeg" in thumb_resp.headers.get("content-type", ""),
            thumb_resp.headers.get("content-type", ""),
        )
        runner.check(
            "Thumbnail bayt > 0",
            len(thumb_resp.content) > 0,
            f"{len(thumb_resp.content)} bayt",
        )

        # --- Download ---
        dl_resp = client.get(f"/api/dokumanlar/indir/{target}")
        runner.check(
            f"GET indir/{target} → 200",
            dl_resp.status_code == 200,
            f"status={dl_resp.status_code}",
        )
        runner.check(
            "Download content-type application/pdf",
            "application/pdf" in dl_resp.headers.get("content-type", ""),
            dl_resp.headers.get("content-type", ""),
        )
        runner.check(
            "Download bayt > 0",
            len(dl_resp.content) > 0,
            f"{len(dl_resp.content)} bayt",
        )
        runner.check(
            "Download PDF başlık imzası (%PDF)",
            dl_resp.content.startswith(b"%PDF"),
        )

    # --- Var olmayan dosya ---
    missing = "cok-kesin-yok-12345.pdf"
    resp_miss_thumb = client.get(f"/api/dokumanlar/thumb/{missing}")
    runner.check("Olmayan thumb → 404", resp_miss_thumb.status_code == 404)

    resp_miss_dl = client.get(f"/api/dokumanlar/indir/{missing}")
    runner.check("Olmayan download → 404", resp_miss_dl.status_code == 404)

    # --- PDF olmayan path ---
    resp_non_pdf = client.get("/api/dokumanlar/thumb/sayfa.html")
    runner.check("Non-pdf thumb → 404", resp_non_pdf.status_code == 404)

    return runner.summary()


if __name__ == "__main__":
    sys.exit(main())
