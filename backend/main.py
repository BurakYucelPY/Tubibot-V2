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

# 1. Sorgu Genişletme (Query Expansion) Prompt'u
# Orijinal sorguyu DEĞİŞTİRMEZ, kısaltmaları açarak ek arama termleri üretir.
QUERY_EXPANSION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "Kullanıcının sorusunu vektör veritabanında arama için HAFİFÇE genişlet. "
               "KESİNLİKLE soruya cevap verme.\n\n"
               "KURALLAR:\n"
               "1. Orijinal soruyu neredeyse AYNEN koru.\n"
               "2. SADECE kısaltmaların açılımını parantez içinde ekle:\n"
               "   - SKA -> Sürdürülebilir Kalkınma Amaçları (SKA)\n"
               "   - 2209-A -> TÜBİTAK 2209-A\n"
               "3. Kendi bilginden ek anahtar kelime, konu veya alan EKLEME.\n"
               "4. Çıktın en fazla 30 kelime olmalı ve soru işaretiyle bitmeli.\n"
               "5. Sorunun niyetini DEĞİŞTİRME."),
    ("human", "{question}")
])

# 2. Ana RAG Promptu (Llama 3 Uyumlu)
RAG_SYSTEM_PROMPT = """Sen TÜBİTAK projeleri (özellikle 2209-A) ve Sürdürülebilir Kalkınma Amaçları (SKA) konusunda uzman asistan "Tubibot"sun.
Aşağıda verilen "Bağlam" (Context) metinlerini kullanarak soruyu detaylıca cevapla.

KURALLAR:
1. SADECE ve SADECE bağlamda bulunan bilgileri kullan. Kendi dış bilginle (örneğin bağlamda geçmeyen 14.1.1, 6.1.1 gibi alt gösterge numaraları uydurarak) ASLA ekleme veya yorum yapma.
2. Bağlamda cevap yoksa sadece: "Bu bilgiye mevcut TÜBİTAK belgelerinde ulaşamadım." de.
3. SKA hedefleri (Örn: Hedef 14.1, Hedef 14.2 vb.) soruluyorsa, bu maddeleri bağlamda yazan orijinal haliyle EKSİKSİZ, NOKTASI VİRGÜLÜNE, KISALTMADAN ve ÖZETLEMEDEN listeleyeceksin. Yarım yamalak bilgi verme.
4. Çıktında HİÇBİR ŞEKİLDE kaynak, belge numarası veya referans (Örn: [Kaynak 1]) belirtme.

BAĞLAM:
{context}"""

RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", RAG_SYSTEM_PROMPT),
    ("human", "{question}")
])

def format_docs_plain(docs):
    """
    Belgeleri kaynak bilgisiyle birlikte formatlar.
    LLM'nin bilgiyi doğru kaynaklara atfedebilmesi için her chunk'un önüne
    kaynak ve bölüm bilgisi eklenir.
    """
    formatted_parts = []
    for doc in docs:
        source = doc.metadata.get("source_document", "Bilinmeyen Belge")
        section = doc.metadata.get("section_heading", "Genel")
        header = f"[Kaynak: {source} | Bölüm: {section}]"
        formatted_parts.append(f"{header}\n{doc.page_content}")
    return "\n\n---\n\n".join(formatted_parts)

def get_rag_chain():
    """Gelişmiş RAG zinciri (Query Transformation + Arama + Saf Üretim) oluştur."""
    retriever = get_retriever()
    llm = get_llm()
    parser = StrOutputParser()

    # Query Expansion Zinciri
    query_expansion_chain = QUERY_EXPANSION_PROMPT | llm | parser

    def rag_invoke(raw_question):
        # Aşama 1: Sorgu Genişletme (Query Expansion)
        print("\n[INFO] Orijinal Sorgu:", raw_question)
        try:
            expanded_question = query_expansion_chain.invoke({"question": raw_question}).strip()
            print(f"[INFO] Genişletilmiş Sorgu: {expanded_question}")
        except Exception:
            expanded_question = raw_question

        # Aşama 2: Arama — genişletilmiş sorguyla retrieval
        docs = retriever.invoke(expanded_question)
        
        if not docs:
            return "Bu konuyla ilgili mevcut belgelerde herhangi bir bilgi bulunamadı. Lütfen TÜBİTAK'ın güncel kaynaklarını kontrol ediniz."
        
        # Aşama 3: Bağlam Formatlama
        context = format_docs_plain(docs)
        
        # Aşama 4: LLM Üretimi (orijinal soruyla — genişletilmiş değil)
        response_chain = RAG_PROMPT | llm | parser
        return response_chain.invoke({
            "context": context,
            "question": raw_question
        })
    
    return rag_invoke


if __name__ == "__main__":
    print("\n[INFO] Tubibot V2 Gelişmiş RAG Sistemi Başlatılıyor...")
    print("=" * 60)
    
    rag_chain = get_rag_chain()
    
    # Test soruları
    test_questions = [
        "Tübitak öncelikli alanlar nelerdir?"]
    
    for soru in test_questions:
        print(f"\n[KULLANICI]: {soru}\n")
        print("[TUBİBOT DÜŞÜNÜYOR...]\n")
        cevap = rag_chain(soru)
        print(f"[TUBİBOT V2]:\n{cevap}")
        print("=" * 60)