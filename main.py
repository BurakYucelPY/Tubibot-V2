import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.retrieval.retriever import get_retriever
from src.generation.generator import get_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ====================================================================
# TÜRKÇE ODAKLI ÇOKLU ADIM (LLAMA 3 UYUMLU) RAG SİSTEMİ
# 1. Query Transformation
# 2. System / Human Message Ayrımı
# 3. Kaynaksız Saf Türkçe Çıktı
# ====================================================================

# 1. Sorgu İyileştirme Prompt'u
QUERY_TRANSFORM_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "Sen sadece kullanıcının girdiği bozuk veya eksik soruyu anlamsal olarak düzelten bir asistansın. KESİNLİKLE soruya cevap verme. Çıktın bir SORU CÜMLESİ olmalı ve sonu soru işareti (?) ile bitmelidir. Kullanıcının sorusunu, vektör arama için en uygun hale getirip tek bir cümlelik soru olarak geri döndür."),
    ("human", "{question}")
])

# 2. Ana RAG Promptu (Llama 3 Uyumlu)
RAG_SYSTEM_PROMPT = """Sen TÜBİTAK projeleri (özellikle 2209-A) ve Sürdürülebilir Kalkınma Amaçları (SKA) konusunda uzman asistan "Tubibot"sun.
Aşağıda verilen "Bağlam" (Context) metinlerini kullanarak soruyu detaylıca cevapla.

KURALLAR:
1. SADECE bağlamda bulunan bilgileri kullan.
2. Bağlamda cevap yoksa sadece: "Bu bilgiye mevcut TÜBİTAK belgelerinde ulaşamadım." de.
3. Eğen spesifik alt maddeler veya SKA hedefleri soruluyorsa, genel konuşmak yerine bağlamda geçen maddeleri (Örn: Hedef 4.1, Hedef 9.5 vb.) detaylıca ve açıklayıcı şekilde madde madde (bullet points) listele. Analizini derin yap, genel yorumlardan kaçın.
4. Çıktında HİÇBİR ŞEKİLDE kaynak, belge numarası veya referans (Örn: [Kaynak 1]) belirtme. Bilgiyi doğrudan kendi analizinmiş gibi, pürüzsüz Türkçe ile anlat.

BAĞLAM:
{context}"""

RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", RAG_SYSTEM_PROMPT),
    ("human", "{question}")
])

def format_docs_plain(docs):
    """
    Belgeleri aralarına ayraç koyarak salt metin olarak birleştirir.
    Kaynak (Citation) gösterimleri plan dahilinde kaldırılmıştır.
    """
    return "\n\n---\n\n".join([doc.page_content for doc in docs])

def get_rag_chain():
    """Gelişmiş RAG zinciri (Query Transformation + Arama + Saf Üretim) oluştur."""
    retriever = get_retriever()
    llm = get_llm()
    parser = StrOutputParser()

    # Query Transformation Zinciri
    query_transform_chain = QUERY_TRANSFORM_PROMPT | llm | parser

    def rag_invoke(raw_question):
        # Aşama 1: Sorgu İyileştirme
        print("\n[INFO] Orijinal Sorgu:", raw_question)
        improved_question = query_transform_chain.invoke({"question": raw_question}).strip()
        print(f"[INFO] İyileştirilmiş Sorgu: {improved_question}")
        
        # Aşama 2: Arama (Retrieval)
        docs = retriever.invoke(improved_question)
        
        if not docs:
            return "Bu konuyla ilgili mevcut belgelerde herhangi bir bilgi bulunamadı. Lütfen TÜBİTAK'ın güncel kaynaklarını kontrol ediniz."
        
        # Aşama 3: Bağlam Formatlama
        context = format_docs_plain(docs)
        
        # Aşama 4: LLM Üretimi (Ana CEVAP)
        response_chain = RAG_PROMPT | llm | parser
        return response_chain.invoke({
            "context": context,
            "question": improved_question
        })
    
    return rag_invoke


if __name__ == "__main__":
    print("\n[INFO] Tubibot V2 Gelişmiş RAG Sistemi Başlatılıyor...")
    print("=" * 60)
    
    rag_chain = get_rag_chain()
    
    # Test soruları
    test_questions = [
        "TÜBİTAK Bilgi Erişim Süreçleri için Geri-getirme Artırımlı Üretim (RAG) Tabanlı Bir Asistan Geliştirilmesi bir proje yapacağım. Sence hangi ska kapsamlarına girebilir?"]
    
    for soru in test_questions:
        print(f"\n[KULLANICI]: {soru}\n")
        print("[TUBİBOT DÜŞÜNÜYOR...]\n")
        cevap = rag_chain(soru)
        print(f"[TUBİBOT V2]:\n{cevap}")
        print("=" * 60)