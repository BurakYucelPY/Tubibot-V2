import os

from src.generation.generator import get_llm
from src.retrieval.retriever import get_retriever, get_gundem_retriever

from api import state
from api.paths import GUNDEM_DB_DIR
from api.prompts import QUERY_EXPANSION_PROMPT


def startup():
    print("[INFO] Tubibot V2 API baslatiliyor...")
    state.retriever = get_retriever()

    if os.path.exists(GUNDEM_DB_DIR):
        print("[INFO] Gundem retriever yukleniyor...")
        state.gundem_retriever = get_gundem_retriever()
    else:
        print("[WARN] Gundem DB bulunamadi; /api/chat-gundem aktif degil.")

    state.default_llm = get_llm()
    state.llm_cache["__default__"] = state.default_llm
    state.query_expansion_chain = QUERY_EXPANSION_PROMPT | state.default_llm | state.parser
    print("[INFO] RAG pipeline hazir.")
