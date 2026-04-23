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
               "   - 2209-A -> TÜBİTAK 2209-A Üniversite Öğrencileri Araştırma Projeleri\n"
               "   - 2209-B -> TÜBİTAK 2209-B Sanayiye Yönelik Araştırma\n"
               "   - 2211-A -> TÜBİTAK 2211-A Yurt İçi Doktora Bursu\n"
               "   - 2219 -> TÜBİTAK 2219 Yurt Dışı Doktora Sonrası Burs\n"
               "   - 1001 -> TÜBİTAK 1001 ARDEB Bilimsel ve Teknolojik Araştırma\n"
               "   - 1002 -> TÜBİTAK 1002 ARDEB Hızlı Destek\n"
               "   - 1501 -> TÜBİTAK 1501 Sanayi Ar-Ge Destek Programı\n"
               "   - 1507 -> TÜBİTAK 1507 KOBİ Ar-Ge Başlangıç Destek Programı\n"
               "   - ARDEB -> Araştırma Destek Programları Başkanlığı (ARDEB)\n"
               "   - BİDEB -> Bilim İnsanı Destek Programları Başkanlığı (BİDEB)\n"
               "   - TEYDEB -> Teknoloji ve Yenilik Destek Programları Başkanlığı (TEYDEB)\n"
               "3. Kendi bilginden ek anahtar kelime, konu veya alan EKLEME.\n"
               "4. Soruda birden fazla alt soru veya konu varsa HEPSİNİ koru. Hiçbir kısmı silme, birleştirme veya başka bir şeyle değiştirme.\n"
               "5. Sorunun niyetini DEĞİŞTİRME.\n"
               "6. Yazım hatalarını düzelt (ör: 'ypamayı' -> 'yapmayı')."),
    ("human", "{question}")
])

# 2. Ana RAG Promptu (Llama 3 Uyumlu)
RAG_SYSTEM_PROMPT = """Sen "Tubibot"sun — TÜBİTAK destek programları, başvuru rehberleri, uygulama esasları, mali ve idari yönetmelikler, yazım kılavuzları, stratejik plan ve faaliyet raporları konusunda yardımcı bir asistan.

Bilgi kaynağın aşağıdaki bağlamda verilen TÜBİTAK belgeleridir. Bu belgelerin kapsamı arasında 2209-A, 2209-B, 2211-A, 2219 BİDEB burs programları; 1001, 1002 ARDEB araştırma destek programları; 1501, 1507 TEYDEB sanayi/KOBİ Ar-Ge programları; ARDEB ve TEYDEB yönetmelikleri; mali rapor kılavuzu; fikri haklar esasları; öncelikli alanlar listesi; Sürdürülebilir Kalkınma Amaçları (SKA); ve TÜBİTAK 2024-2028 Stratejik Planı + 2025 Faaliyet Raporu yer almaktadır.

Aşağıdaki bağlamı kullanarak soruyu cevapla. Bilgiyi kullanıcının sorusuyla ilişkilendirerek açıkla. Mümkünse hangi programdan / hangi belgeden bilgi verdiğini cevabın içinde doğal bir şekilde belirt (örn. "1001 ARDEB programında..." veya "Mali Rapor Hazırlama Kılavuzuna göre...").

Bağlamda olmayan bilgiyi UYDURMA. Birden fazla program için geçerli olabilen sorularda (örn. "mali rapor nasıl hazırlanır") farklılıkları varsa ayrı ayrı belirt. Kaynak veya referans numarası verme; metin içindeki dahili belge atıflarını ("158. paragrafında belirtildiği üzere" gibi) çıkar.

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
    kaynak, program ve bölüm bilgisi eklenir.
    """
    formatted_parts = []
    for doc in docs:
        source = doc.metadata.get("source_document", "Bilinmeyen Belge")
        section = doc.metadata.get("section_heading", "Genel")
        program = doc.metadata.get("program", "")
        program_str = f" | Program: {program}" if program else ""
        header = f"[Kaynak: {source}{program_str} | Bölüm: {section}]"
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
        "Tübitak 2209-A raporun yöntem kısmı nasıl yazılır?"]
    
    for soru in test_questions:
        print(f"\n[KULLANICI]: {soru}\n")
        print("[TUBİBOT DÜŞÜNÜYOR...]\n")
        cevap = rag_chain(soru)
        print(f"[TUBİBOT V2]:\n{cevap}")
        print("=" * 60)