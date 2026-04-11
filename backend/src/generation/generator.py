import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from langchain_groq import ChatGroq

load_dotenv()

# Frontend model id -> Groq model adı eşleşmesi
MODEL_MAP = {
    "groq/llama-3.3-70b": "llama-3.3-70b-versatile",
    "groq/openai/gpt-oss-120b": "openai/gpt-oss-120b",
}

DEFAULT_MODEL_ID = "groq/llama-3.3-70b"


def get_llm(model_id: str | None = None):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("[HATA] GROQ_API_KEY bulunamadı! Lütfen .env dosyanızı kontrol edin.")

    selected = model_id or DEFAULT_MODEL_ID
    model_name = MODEL_MAP.get(selected, MODEL_MAP[DEFAULT_MODEL_ID])

    llm = ChatGroq(
        groq_api_key=api_key,
        model_name=model_name,
        temperature=0.2,
        max_tokens=4096
    )
    return llm

if __name__ == "__main__":
    print("\n[INFO] Groq Konuşma Motoru (LLM) test ediliyor...")
    llm = get_llm()
    
    mesaj = "Merhaba, Tubibot V2 projesi için test yapıyoruz. Lütfen sistemin çalıştığını onaylayan kısa bir Türkçe mesaj yaz."
    print(f"\n[SİSTEM TESTİ] {mesaj}")
    print("-" * 60)
    
    cevap = llm.invoke(mesaj)
    print(f"[GROQ CEVABI]\n{cevap.content}")
    print("=" * 60)