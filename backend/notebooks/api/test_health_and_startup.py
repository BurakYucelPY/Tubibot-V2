"""
api/test_health_and_startup.py

FastAPI lifespan + health endpoint:
- TestClient context-manager'ı startup event'ini tetikliyor
- /api/health → 200 + beklenen JSON
- state.retriever None değil
- state.gundem_retriever None değil (gundem_vector_db varsa)
- state.default_llm None değil
- state.query_expansion_chain None değil

NOT: İlk yükleme ~15-30 sn sürer (cross-encoder + Chroma).
"""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from _helpers.bootstrap import setup_backend_path
BACKEND_ROOT = setup_backend_path()

from _helpers.runner import TestRunner
from _helpers.api_client import get_test_client


def main():
    runner = TestRunner("api/test_health_and_startup")

    client = get_test_client()
    runner.info("TestClient hazır (lifespan tetiklendi).")

    # --- /api/health ---
    resp = client.get("/api/health")
    runner.check("GET /api/health → 200", resp.status_code == 200, f"status={resp.status_code}")

    try:
        body = resp.json()
        runner.check("health body dict", isinstance(body, dict))
        runner.check("health status='ok'", body.get("status") == "ok", f"body={body}")
        runner.check("health service alanı var", "service" in body)
    except Exception as e:
        runner.check(f"health body JSON parse — {type(e).__name__}", False, str(e)[:80])

    # --- state enjeksiyonu ---
    from api import state
    runner.check("state.retriever yüklendi", state.retriever is not None)
    runner.check("state.default_llm yüklendi", state.default_llm is not None)
    runner.check("state.query_expansion_chain yüklendi", state.query_expansion_chain is not None)

    gundem_db = os.path.join(BACKEND_ROOT, "data", "gundem_vector_db")
    if os.path.isdir(gundem_db):
        runner.check(
            "state.gundem_retriever yüklendi (gundem_vector_db mevcut)",
            state.gundem_retriever is not None,
        )
    else:
        runner.info("gundem_vector_db yok — gundem_retriever kontrolü atlandı.")

    # --- Olmayan rota 404 ---
    resp_404 = client.get("/api/nonexistent-route-xyz")
    runner.check("Olmayan rota → 404", resp_404.status_code == 404, f"status={resp_404.status_code}")

    return runner.summary()


if __name__ == "__main__":
    sys.exit(main())
