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
    ("system", "Sen kullanıcının girdiği soruyu vektör veritabanında arama yapmak için en uygun hale getiren bir asistansın. "
               "KESİNLİKLE soruya cevap verme. Çıktın sadece TEK BİR SORU CÜMLESİ olmalı ve soru işaretiyle bitmelidir. "
               "\n\nÇOK ÖNEMLİ KURALLAR:\n"
               "1. Kullanıcının sorusundaki kavramları, kısaltmaları (TÜBİTAK, SKA, 2209-A vb.) ve hedefleri ASLA değiştirme, genel kavramlara dönüştürme.\n"
               "2. Eğer kullanıcı 'SKA' (Sürdürülebilir Kalkınma Amaçları) diyorsa, bunu mutlaka 'Sürdürülebilir Kalkınma Amaçları (SKA)' şeklinde arama sorgusunda koru.\n"
               "3. Sorunun ana niyetini (hangi kapsama girer, şartlar nelerdir vb.) birebir korumak zorundasın, kendi yorumunu katma."),
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
        # Aşama 1: Sorgu İyileştirme (GEÇİCİ OLARAK DEVRE DIŞI BIRAKILDI)
        print("\n[INFO] Sorgu:", raw_question)
        # improved_question = query_transform_chain.invoke({"question": raw_question}).strip()
        # print(f"[INFO] İyileştirilmiş Sorgu: {improved_question}")
        improved_question = raw_question  # İyileştirme yapmadan direkt orijinal soruyu kullan
        
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
        "Sulardaki yaşamı korumak için bir sümilasyon ile alakalı bir proje yapacağım. Sence bu hangi SKA kapsamına girer ve tübitak öncelikli alanlardan hangisine girebilir?"]
    
    for soru in test_questions:
        print(f"\n[KULLANICI]: {soru}\n")
        print("[TUBİBOT DÜŞÜNÜYOR...]\n")
        cevap = rag_chain(soru)
        print(f"[TUBİBOT V2]:\n{cevap}")
        print("=" * 60)