"""
FastAPI TestClient cache'i.

FastAPI uygulaması başlatıldığında (on_event("startup")) retriever'lar + LLM
yüklenir — bu 10-30 saniye sürer. Tek process içinde birden fazla test dosyası
çalışırken (run_suite.py üzerinden) app'i bir kez açıp cache'lemek gerekir.

TestClient'ın context manager olarak girilmesi startup event'ini tetikler; bu
fixture tam olarak bunu yapar.
"""

_client = None


def get_test_client():
    """Lifespan'ı başlatılmış tek-instance TestClient döndürür."""
    global _client
    if _client is None:
        from fastapi.testclient import TestClient
        from api import app

        _client = TestClient(app)
        # TestClient'ı context olarak aç — on_event("startup") tetiklenir.
        _client.__enter__()
    return _client


def close_test_client():
    """İsteğe bağlı: test süreci sonunda lifespan'ı kapat."""
    global _client
    if _client is not None:
        try:
            _client.__exit__(None, None, None)
        finally:
            _client = None
