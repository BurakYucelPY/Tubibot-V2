"""
generation/test_generator.py

src/generation/generator.py::get_llm:
- MODEL_MAP anahtarları doğru Groq model adlarına çözümleniyor mu?
- GROQ_API_KEY yoksa ValueError fırlatıyor mu?
- Default çağrı (model_id=None) çalışıyor mu?
- Live smoke: llm.invoke("selam") yanıt dönüyor mu?
"""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from _helpers.bootstrap import setup_backend_path
setup_backend_path()

from _helpers.runner import TestRunner


def main():
    from src.generation.generator import DEFAULT_MODEL_ID, MODEL_MAP, get_llm

    runner = TestRunner("generation/test_generator")

    runner.info(f"MODEL_MAP ({len(MODEL_MAP)} mapping): {list(MODEL_MAP.keys())}")
    runner.check("DEFAULT_MODEL_ID MODEL_MAP içinde", DEFAULT_MODEL_ID in MODEL_MAP)
    runner.check("MODEL_MAP boş değil", len(MODEL_MAP) > 0)

    # --- API key var mı? ---
    api_key = os.getenv("GROQ_API_KEY")
    runner.check("GROQ_API_KEY ortamda tanımlı", bool(api_key), "(değeri gizli)")

    if not api_key:
        runner.info("API key yok — kalan testler atlanıyor.")
        return runner.summary()

    # --- Live LLM ---
    llm_default = get_llm()
    runner.check("get_llm() default çağrısı None değil", llm_default is not None)
    # langchain_groq.ChatGroq model_name attribute'ı taşır
    runner.info(f"Default model_name: {getattr(llm_default, 'model_name', '?')}")

    llm_named = get_llm("groq/llama-3.3-70b")
    default_maps_to = MODEL_MAP[DEFAULT_MODEL_ID]
    runner.check(
        f"get_llm('groq/llama-3.3-70b') model_name = {default_maps_to}",
        getattr(llm_named, "model_name", "") == default_maps_to,
    )

    # Bilinmeyen model_id default'a fallback eder
    llm_unknown = get_llm("groq/bilinmeyen-model")
    runner.check(
        "Bilinmeyen model_id default'a düşer",
        getattr(llm_unknown, "model_name", "") == default_maps_to,
    )

    # --- Hata yolu: GROQ_API_KEY silindiğinde ValueError ---
    original_key = os.environ.pop("GROQ_API_KEY", None)
    try:
        raised = False
        try:
            get_llm()
        except ValueError as e:
            raised = True
            runner.info(f"Beklenen hata: {e}")
        runner.check("GROQ_API_KEY yokken ValueError fırlatılır", raised)
    finally:
        if original_key is not None:
            os.environ["GROQ_API_KEY"] = original_key

    # --- Live smoke: basit bir prompt ---
    try:
        resp = llm_default.invoke("Sadece 'Merhaba' de.")
        content = getattr(resp, "content", "")
        runner.check(
            "LLM canlı yanıt döndü",
            len(content.strip()) > 0,
            f"yanıt uzunluğu: {len(content)} char",
        )
    except Exception as e:
        runner.check(f"LLM live çağrı (hata: {type(e).__name__})", False, str(e)[:100])

    return runner.summary()


if __name__ == "__main__":
    sys.exit(main())
