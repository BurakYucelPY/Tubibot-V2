"""
api/test_schemas.py

api/schemas.py::ChatRequest Pydantic doğrulama:
- Sadece message ile valid
- message + model ile valid
- Eksik message → ValidationError
- model=None default
- Boş string Pydantic tarafından kabul ediliyor (route kontrolü ayrı)
"""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from _helpers.bootstrap import setup_backend_path
setup_backend_path()

from _helpers.runner import TestRunner


def main():
    from pydantic import ValidationError
    from api.schemas import ChatRequest

    runner = TestRunner("api/test_schemas")

    # --- Valid: sadece message ---
    try:
        req = ChatRequest(message="merhaba")
        runner.check("ChatRequest(message='merhaba') valid", req.message == "merhaba")
        runner.check("model default None", req.model is None)
    except Exception as e:
        runner.check(f"Minimal ChatRequest — {type(e).__name__}", False, str(e)[:80])

    # --- Valid: message + model ---
    try:
        req = ChatRequest(message="test", model="groq/llama-3.3-70b")
        runner.check("ChatRequest(message, model) valid", req.message == "test")
        runner.check("model='groq/llama-3.3-70b' korundu", req.model == "groq/llama-3.3-70b")
    except Exception as e:
        runner.check(f"Model'li ChatRequest — {type(e).__name__}", False, str(e)[:80])

    # --- Invalid: eksik message ---
    raised = False
    try:
        ChatRequest()  # type: ignore[call-arg]
    except ValidationError:
        raised = True
    except Exception as e:
        runner.info(f"Beklenmeyen exception tipi: {type(e).__name__}")
    runner.check("Eksik 'message' → ValidationError", raised)

    # --- Boş string Pydantic tarafında kabul ediliyor mu? (belgeleyici) ---
    try:
        req = ChatRequest(message="")
        runner.check(
            "Boş string Pydantic'te valid (route tarafında değerlendirilir)",
            req.message == "",
        )
    except ValidationError:
        runner.info("Boş string ValidationError fırlattı — schema katmanında reddediliyor.")

    # --- Yanlış tip ---
    raised = False
    try:
        ChatRequest(message=123)  # type: ignore[arg-type]
    except ValidationError:
        raised = True
    runner.check("message=int → ValidationError", raised)

    return runner.summary()


if __name__ == "__main__":
    sys.exit(main())
