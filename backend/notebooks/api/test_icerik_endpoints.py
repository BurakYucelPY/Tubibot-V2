"""
api/test_icerik_endpoints.py

Duyuru / Haber içerik endpoint'leri:
- GET /api/duyurular  → list
- GET /api/haberler   → list
- Item anahtarları: baslik/tarih/kaynak_url benzeri alanlar
- Eleman sayıları duyurular.json + haberler.json ile eşit
- Dosya yoksa 200 + []
- /api/icerikleri-guncelle endpoint'i mevcut (ÇAĞIRILMIYOR — ağır iş)
"""
import os, sys, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from _helpers.bootstrap import setup_backend_path
setup_backend_path()

from _helpers.runner import TestRunner
from _helpers.api_client import get_test_client


def _load_json(path: str):
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def main():
    runner = TestRunner("api/test_icerik_endpoints")

    from api.paths import DUYURULAR_JSON, HABERLER_JSON

    client = get_test_client()

    # --- /api/duyurular ---
    resp_d = client.get("/api/duyurular")
    runner.check("GET /api/duyurular → 200", resp_d.status_code == 200, f"status={resp_d.status_code}")
    try:
        duyurular = resp_d.json()
    except Exception as e:
        runner.check(f"/api/duyurular JSON parse — {type(e).__name__}", False, str(e)[:80])
        duyurular = []
    runner.check("/api/duyurular list tipinde", isinstance(duyurular, list))
    runner.info(f"Endpoint duyuru sayısı: {len(duyurular) if isinstance(duyurular, list) else '?'}")

    # JSON ile karşılaştırma
    disk_duyurular = _load_json(DUYURULAR_JSON)
    if disk_duyurular is None:
        runner.info(f"duyurular.json yok/okunamadı ({DUYURULAR_JSON}) — endpoint boş liste dönmeli.")
        runner.check("Dosya yoksa endpoint [] döndürür", duyurular == [])
    else:
        runner.check(
            "Endpoint duyuru sayısı == disk JSON sayısı",
            len(duyurular) == len(disk_duyurular),
            f"endpoint={len(duyurular)}, disk={len(disk_duyurular)}",
        )
        if duyurular:
            first = duyurular[0]
            runner.check("duyuru item dict tipinde", isinstance(first, dict))
            expected_any = ("baslik", "title", "tarih", "kaynak_url", "url", "link")
            has_any = any(k in first for k in expected_any)
            runner.check(
                "İlk duyuruda baslik/tarih/url benzeri alan var",
                has_any,
                f"keys={list(first.keys())[:6]}",
            )

    # --- /api/haberler ---
    resp_h = client.get("/api/haberler")
    runner.check("GET /api/haberler → 200", resp_h.status_code == 200, f"status={resp_h.status_code}")
    try:
        haberler = resp_h.json()
    except Exception as e:
        runner.check(f"/api/haberler JSON parse — {type(e).__name__}", False, str(e)[:80])
        haberler = []
    runner.check("/api/haberler list tipinde", isinstance(haberler, list))
    runner.info(f"Endpoint haber sayısı: {len(haberler) if isinstance(haberler, list) else '?'}")

    disk_haberler = _load_json(HABERLER_JSON)
    if disk_haberler is None:
        runner.info(f"haberler.json yok/okunamadı ({HABERLER_JSON}).")
        runner.check("Dosya yoksa endpoint [] döndürür", haberler == [])
    else:
        runner.check(
            "Endpoint haber sayısı == disk JSON sayısı",
            len(haberler) == len(disk_haberler),
            f"endpoint={len(haberler)}, disk={len(disk_haberler)}",
        )
        if haberler:
            first = haberler[0]
            runner.check("haber item dict tipinde", isinstance(first, dict))

    # --- /api/icerikleri-guncelle endpoint KAYITLI mı (OPTIONS ile) ---
    # POST çağırmıyoruz: scraper + rebuild çok ağır.
    resp_opts = client.options("/api/icerikleri-guncelle")
    runner.check(
        "/api/icerikleri-guncelle rotası kayıtlı (405/200/204)",
        resp_opts.status_code in (200, 204, 405),
        f"status={resp_opts.status_code}",
    )
    # GET de 405 olmalı (POST-only)
    resp_get = client.get("/api/icerikleri-guncelle")
    runner.check(
        "GET /api/icerikleri-guncelle → 405 (POST-only)",
        resp_get.status_code == 405,
        f"status={resp_get.status_code}",
    )

    return runner.summary()


if __name__ == "__main__":
    sys.exit(main())
