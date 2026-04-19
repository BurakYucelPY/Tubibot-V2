"""
api/test_chat_gundem_endpoint.py

POST /api/chat-gundem — gündem RAG stream endpoint:
- Geçerli sorgu → 200 + text/plain stream
- Yanıt URL veya tarih içeriyor (prompt kaynak atmayı zorunlu kılıyor)
- Out-of-scope sorguda halüsinasyon yapmıyor (bilmediğini söylüyor)
- Eksik body → 422

Ön koşul: backend/data/gundem_vector_db mevcut olmalı.
Live: gerçek Groq API tüketilir.
"""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from _helpers.bootstrap import setup_backend_path
BACKEND_ROOT = setup_backend_path()

from _helpers.runner import TestRunner
from _helpers.api_client import get_test_client


def main():
    runner = TestRunner("api/test_chat_gundem_endpoint")

    gundem_db = os.path.join(BACKEND_ROOT, "data", "gundem_vector_db")
    if not os.path.isdir(gundem_db):
        runner.check("gundem_vector_db mevcut", False, "Yok — build_gundem_vector_database() çalıştırın")
        return runner.summary()

    client = get_test_client()

    # --- Valid gündem çağrısı ---
    soru = "Son duyurular ve yeni çağrılar nelerdir?"
    runner.info(f"Sorgu: {soru}")
    resp = client.post("/api/chat-gundem", json={"message": soru})
    runner.check("POST /api/chat-gundem → 200", resp.status_code == 200, f"status={resp.status_code}")
    runner.check(
        "Content-Type text/plain",
        "text/plain" in resp.headers.get("content-type", ""),
        resp.headers.get("content-type", ""),
    )

    body = resp.text
    runner.info(f"Yanıt uzunluğu: {len(body)} karakter")
    runner.check("Yanıt boş değil", len(body) > 0)

    body_lower = body.lower()
    has_source_hint = (
        "http" in body_lower
        or "tubitak.gov.tr" in body_lower
        or any(m in body_lower for m in (
            "ocak", "şubat", "mart", "nisan", "mayıs", "haziran",
            "temmuz", "ağustos", "eylül", "ekim", "kasım", "aralık",
        ))
        or any(str(y) in body for y in range(2023, 2027))
    )
    runner.check(
        "Yanıt URL veya tarih içeriyor (kaynak atma)",
        has_source_hint,
        f"ilk 120: {body[:120]!r}",
    )

    # --- Out-of-scope: halüsinasyon guard ---
    oos = "New York Yankees bu yıl kaç kupa kazandı?"
    runner.info(f"Out-of-scope sorgu: {oos}")
    resp_oos = client.post("/api/chat-gundem", json={"message": oos})
    runner.check("OOS sorgu da 200 döner", resp_oos.status_code == 200)
    oos_body = resp_oos.text.lower()
    guard_keywords = (
        "bilgi yer almıyor", "bilgi bulunamadı", "bilgi bulunmuyor",
        "bilmiyorum", "cevap veremem", "mevcut değil", "yer almamakta",
        "bulunmamakta", "emin değil",
    )
    runner.check(
        "OOS yanıt halüsinasyon guard'ı içeriyor",
        any(k in oos_body for k in guard_keywords),
        f"ilk 120: {oos_body[:120]!r}",
    )

    # --- Eksik body ---
    resp_bad = client.post("/api/chat-gundem", json={})
    runner.check("Eksik body → 422", resp_bad.status_code == 422, f"status={resp_bad.status_code}")

    return runner.summary()


if __name__ == "__main__":
    sys.exit(main())
