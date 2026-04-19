"""
api/test_chat_endpoint.py

POST /api/chat — ana PDF RAG stream endpoint:
- Geçerli soru → 200 + text/plain stream + non-empty body
- 2209-A sorusunda yanıt belirli kelimeler içeriyor (lisans/doktora/başvuru)
- Eksik body → 422 (Pydantic)
- Yanıt makul uzunlukta (>50 char)
- model override: 'groq/llama-3.3-70b' ile çağrı da başarılı

Live: gerçek Groq API tüketilir, retriever gerçek vector_db'den çeker.
"""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from _helpers.bootstrap import setup_backend_path
setup_backend_path()

from _helpers.runner import TestRunner
from _helpers.api_client import get_test_client


def main():
    runner = TestRunner("api/test_chat_endpoint")

    client = get_test_client()

    # --- Valid çağrı ---
    soru = "2209-A'ya kimler başvurabilir?"
    runner.info(f"Sorgu: {soru}")
    resp = client.post("/api/chat", json={"message": soru})
    runner.check("POST /api/chat → 200", resp.status_code == 200, f"status={resp.status_code}")
    runner.check(
        "Content-Type text/plain",
        "text/plain" in resp.headers.get("content-type", ""),
        resp.headers.get("content-type", ""),
    )

    body = resp.text
    runner.info(f"Yanıt uzunluğu: {len(body)} karakter")
    runner.check("Yanıt boş değil", len(body) > 0)
    runner.check("Yanıt makul uzunlukta (>50 char)", len(body) > 50, f"{len(body)} char")

    body_lower = body.lower()
    has_relevant = any(k in body_lower for k in ("lisans", "doktora", "başvur", "tübitak", "2209"))
    runner.check(
        "Yanıt PDF bilgisiyle tutarlı anahtar kelime içeriyor",
        has_relevant,
        f"ilk 80: {body[:80]!r}",
    )

    # --- Eksik body → 422 ---
    resp_bad = client.post("/api/chat", json={})
    runner.check("Eksik body → 422", resp_bad.status_code == 422, f"status={resp_bad.status_code}")

    # --- Yanlış method → 405 ---
    resp_get = client.get("/api/chat")
    runner.check(
        "GET /api/chat → 405 (POST only)",
        resp_get.status_code == 405,
        f"status={resp_get.status_code}",
    )

    # --- Model override ---
    resp_model = client.post(
        "/api/chat",
        json={"message": "SKA nedir?", "model": "groq/llama-3.3-70b"},
    )
    runner.check(
        "Model override ile POST → 200",
        resp_model.status_code == 200,
        f"status={resp_model.status_code}",
    )
    runner.check(
        "Model override yanıt uzunluğu >0",
        len(resp_model.text) > 0,
    )

    return runner.summary()


if __name__ == "__main__":
    sys.exit(main())
