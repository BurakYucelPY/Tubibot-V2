"""
generation/test_query_expansion.py

api/prompts.py::QUERY_EXPANSION_PROMPT + live Groq LLM:
- Kısaltma açımı: "2209-A" → "TÜBİTAK 2209-A" yer alsın
- "SKA" → "Sürdürülebilir Kalkınma Amaçları"
- Orijinal sorunun niyeti korundu mu (substring kontrolü, gevşek)
- Kısa soru için zincirin bozulmadan yanıt üretmesi

Groq LLM canlı — quota tüketir.
"""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from _helpers.bootstrap import setup_backend_path
setup_backend_path()

from _helpers.runner import TestRunner


def main():
    runner = TestRunner("generation/test_query_expansion")

    if not os.getenv("GROQ_API_KEY"):
        runner.check("GROQ_API_KEY mevcut", False, "Ortamda tanımlı değil")
        return runner.summary()

    from langchain_core.output_parsers import StrOutputParser
    from api.prompts import QUERY_EXPANSION_PROMPT
    from src.generation.generator import get_llm

    llm = get_llm()
    parser = StrOutputParser()
    chain = QUERY_EXPANSION_PROMPT | llm | parser

    # Test 1: 2209-A kısaltması açılır
    q1 = "2209-A kimler başvurabilir?"
    try:
        r1 = chain.invoke({"question": q1}).strip()
    except Exception as e:
        runner.check(f"Chain invoke (q1) — hata: {type(e).__name__}", False, str(e)[:100])
        return runner.summary()
    runner.info(f"q1 genişletilmiş: {r1[:200]}")
    runner.check("q1 boş değil", len(r1) > 0)
    runner.check("q1 orijinal anahtar kelime ('başvur') korundu", "başvur" in r1.lower())
    runner.check(
        "q1 'TÜBİTAK 2209-A' açılımı geçti",
        "TÜBİTAK 2209-A" in r1 or "Tübitak 2209-A" in r1 or "tübitak 2209-a" in r1.lower(),
    )

    # Test 2: SKA kısaltması açılır
    q2 = "SKA hedefleri nelerdir?"
    r2 = chain.invoke({"question": q2}).strip()
    runner.info(f"q2 genişletilmiş: {r2[:200]}")
    runner.check("q2 boş değil", len(r2) > 0)
    runner.check("q2 'hedef' korundu", "hedef" in r2.lower())
    runner.check(
        "q2 'Sürdürülebilir Kalkınma' açılımı geçti",
        "Sürdürülebilir Kalkınma" in r2 or "sürdürülebilir kalkınma" in r2.lower(),
    )

    # Test 3: Out-of-scope bozmuyor (crash etmiyor)
    q3 = "Bugün İstanbul hava durumu?"
    try:
        r3 = chain.invoke({"question": q3}).strip()
        runner.check("Out-of-scope sorguda zincir crash etmiyor", len(r3) > 0, f"yanıt: {r3[:80]}")
    except Exception as e:
        runner.check(f"Out-of-scope crash — {type(e).__name__}", False, str(e)[:100])

    return runner.summary()


if __name__ == "__main__":
    sys.exit(main())
