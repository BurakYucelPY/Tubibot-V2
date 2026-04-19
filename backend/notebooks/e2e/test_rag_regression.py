"""
e2e/test_rag_regression.py

PDF RAG golden dataset regression:
- golden_pdf.json'daki her soru için:
  - get_rag_chain() yanıt döndürüyor mu?
  - must_contain_terms_any: en az bir terim yanıtta geçiyor mu?
  - must_contain_source_substr: retriever'ın getirdiği kaynaklardan en az
    biri bu substring'lerden birini içeriyor mu?
- Domain kapsaması: 2209-A, SKA, oncelikli_alanlar — her biri ≥ 1 soru.

Live: Groq API + vector_db. Her soru 1 LLM çağrısı → yaklaşık N × 2-5 sn.
"""
import os, sys, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from _helpers.bootstrap import setup_backend_path
setup_backend_path()

from _helpers.runner import TestRunner


def _load_golden():
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "golden_pdf.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    runner = TestRunner("e2e/test_rag_regression")

    if not os.getenv("GROQ_API_KEY"):
        runner.check("GROQ_API_KEY mevcut", False, "Ortamda tanımlı değil")
        return runner.summary()

    try:
        cases = _load_golden()
    except Exception as e:
        runner.check(f"golden_pdf.json yüklendi — {type(e).__name__}", False, str(e)[:80])
        return runner.summary()

    runner.check("golden_pdf.json non-empty", len(cases) > 0, f"{len(cases)} soru")
    domains = {c.get("domain") for c in cases}
    runner.check("2209-A domain var", "2209-A" in domains)
    runner.check("SKA domain var", "SKA" in domains)
    runner.check("oncelikli_alanlar domain var", "oncelikli_alanlar" in domains)

    from src.retrieval.retriever_pdf import get_retriever
    from main import get_rag_chain

    retriever = get_retriever()
    chain = get_rag_chain()

    total = len(cases)
    answered = 0
    src_ok = 0
    term_ok = 0

    for i, case in enumerate(cases, 1):
        q = case["question"]
        runner.info(f"[{i}/{total}] {q}")
        try:
            docs = retriever.invoke(q)
            answer = chain(q)
        except Exception as e:
            runner.check(f"[{i}] Chain crash — {type(e).__name__}", False, str(e)[:100])
            continue

        answered += 1

        # Kaynak kontrolü
        sources = [(d.metadata.get("source_document") or "") for d in docs]
        src_substrs = case.get("must_contain_source_substr", [])
        src_match = any(
            any(sub.lower() in s.lower() for sub in src_substrs) for s in sources
        )
        if src_match:
            src_ok += 1
        runner.check(
            f"[{i}] Kaynak eşleşmesi ({', '.join(src_substrs)})",
            src_match,
            f"ilk kaynak: {sources[0] if sources else 'YOK'}",
        )

        # Terim kontrolü
        ans_lower = (answer or "").lower()
        terms = case.get("must_contain_terms_any", [])
        term_match = any(t.lower() in ans_lower for t in terms)
        if term_match:
            term_ok += 1
        runner.check(
            f"[{i}] Yanıt terim eşleşmesi ({', '.join(terms[:3])}...)",
            term_match,
            f"yanıt ilk 120: {(answer or '')[:120]!r}",
        )

    runner.info(f"Özet: {answered}/{total} yanıt, {src_ok}/{total} kaynak OK, {term_ok}/{total} terim OK")
    runner.check("En az 1 soru yanıtlandı", answered >= 1)
    runner.check("Kaynak başarı oranı ≥ %60", src_ok >= int(0.6 * total), f"{src_ok}/{total}")
    runner.check("Terim başarı oranı ≥ %60", term_ok >= int(0.6 * total), f"{term_ok}/{total}")

    return runner.summary()


if __name__ == "__main__":
    sys.exit(main())
