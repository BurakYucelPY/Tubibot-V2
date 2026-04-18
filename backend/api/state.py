from langchain_core.output_parsers import StrOutputParser

from src.generation.generator import get_llm


retriever = None
gundem_retriever = None
default_llm = None
parser = StrOutputParser()
query_expansion_chain = None
llm_cache: dict[str, object] = {}


def _get_or_create_llm(model_id: str | None):
    key = model_id or "__default__"
    if key not in llm_cache:
        llm_cache[key] = get_llm(model_id)
    return llm_cache[key]
