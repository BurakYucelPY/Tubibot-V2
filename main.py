import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.retrieval.retriever import get_retriever
from src.generation.generator import get_llm
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ====================================================================
# GELİŞMİŞ PROMPT TEMPLATE
# - Chain-of-Thought (adım adım düşünme)
# - Yapılandırılmış cevap formatı
# - Kaynak referansları
# - Hallüsinasyon koruması
# - Belirsizlik yönetimi
# ====================================================================
RAG_PROMPT_TEMPLATE = """Sen TÜBİTAK projeleri (özellikle 2209-A Üniversite Öğrencileri Araştırma Projeleri) ve Sürdürülebilir Kalkınma Amaçları (SKA) konusunda uzman, profesyonel bir Türkçe asistansın.

## GÖREV
Aşağıda sana "Bağlam" olarak verilen belge parçalarını kullanarak kullanıcının sorusunu eksiksiz ve doğru şekilde cevapla.

## KURALLAR (KESİNLİKLE UYULMASI GEREKEN)
1. **SADECE bağlamda bulunan bilgileri kullan.** Bağlamda olmayan bilgiyi asla uydurma veya tahmin etme.
2. Eğer sorunun cevabı bağlamda yoksa, açıkça şunu söyle: "Bu bilgiye mevcut TÜBİTAK belgelerinde ulaşamadım. Lütfen TÜBİTAK'ın güncel kaynaklarını kontrol ediniz."
3. Eğer bağlamda kısmi bilgi varsa, bulduğun kadarını paylaş ve eksik kısımları belirt.
4. Tarih, sayı, limit gibi somut bilgileri verirken bağlamdaki değerleri AYNEN kullan, yuvarlama.

## CEVAP FORMATI
- Cevabını açık ve anlaşılır Türkçe ile yaz.
- Gerektiğinde madde işaretleri veya numaralı listeler kullan.
- Cevabın sonunda, bilgilerin hangi belgelerden alındığını kısaca belirt.
- Karmaşık soruları adım adım ele al.

## BAĞLAM (Kaynak Belgeler)
{context}

## KULLANICI SORUSU
{question}

## CEVAP
Önce soruyu analiz edeyim, sonra bağlam belgelerinden ilgili bilgileri derleyerek cevaplayayım:
"""


def format_docs_with_sources(docs):
    """
    Bulunan belgeleri metadata bilgileriyle birlikte formatla.
    Her chunk hangi belgeden ve hangi bölümden geldiği bilgisiyle sunulur.
    """
    formatted_parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source_document", "Bilinmeyen Kaynak")
        section = doc.metadata.get("section_heading", "")
        doc_type = doc.metadata.get("document_type", "")
        
        header = f"[Kaynak {i}: {source}"
        if section and section != "Genel":
            header += f" — {section}"
        header += "]"
        
        formatted_parts.append(f"{header}\n{doc.page_content}")
    
    return "\n\n---\n\n".join(formatted_parts)


def get_rag_chain():
    """Gelişmiş RAG zincirini oluştur ve döndür."""
    # 1. Retriever ve LLM'i başlat
    retriever = get_retriever()
    llm = get_llm()

    # 2. Gelişmiş prompt
    prompt = PromptTemplate.from_template(RAG_PROMPT_TEMPLATE)

    # 3. Zinciri kur (retriever özel sınıf olduğu için manuel pipeline)
    def rag_invoke(question):
        # Retrieval: Hybrid search + re-ranking ile en kaliteli chunk'ları bul
        docs = retriever.invoke(question)
        
        # Güven kontrolü: Hiç doküman bulunamadıysa
        if not docs:
            return "Bu konuyla ilgili mevcut belgelerde herhangi bir bilgi bulunamadı. Lütfen TÜBİTAK'ın güncel kaynaklarını kontrol ediniz."
        
        # Bağlamı formatla (kaynaklar ile birlikte)
        context = format_docs_with_sources(docs)
        
        # Prompt'u doldur
        formatted_prompt = prompt.format(context=context, question=question)
        
        # LLM'e gönder
        response = llm.invoke(formatted_prompt)
        
        # Çıktıyı parse et
        parser = StrOutputParser()
        return parser.invoke(response)
    
    return rag_invoke


if __name__ == "__main__":
    print("\n[INFO] Tubibot V2 Gelişmiş RAG Sistemi Başlatılıyor...")
    print("=" * 60)
    
    rag_chain = get_rag_chain()
    
    # Test soruları
    test_questions = [
        "2209-A projesine kimler başvuru yapabilir?",
        "Sürdürülebilir Kalkınma Amaçlarından 1. amaç nedir?",
    ]
    
    for soru in test_questions:
        print(f"\n[KULLANICI]: {soru}\n")
        print("[TUBİBOT DÜŞÜNÜYOR...]\n")
        cevap = rag_chain(soru)
        print(f"[TUBİBOT V2]:\n{cevap}")
        print("=" * 60)