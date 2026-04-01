import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.retrieval.retriever import get_retriever
from src.generation.generator import get_llm
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

def get_rag_chain():
    # 1. Hafıza ve Konuşma motorlarını çağır
    retriever = get_retriever()
    llm = get_llm()

    # 2. Bota karakterini ve kurallarını dikte et (Prompt Engineering)
    template = """Sen TÜBİTAK projeleri (özellikle 2209-A) ve Sürdürülebilir Kalkınma Amaçları (SKA) konusunda uzman, profesyonel bir asistansın.
    Aşağıdaki "Bağlam" (Context) bölümünde sana sağlanan bilgileri kullanarak kullanıcının "Soru"sunu Türkçe olarak cevapla.
    Eğer cevabı bağlamda bulamazsan, 'Bu bilgiye TÜBİTAK belgelerinde ulaşamadım' de, asla kendi kendine bilgi uydurma.

    Bağlam: {context}

    Soru: {question}

    Cevap:"""
    prompt = PromptTemplate.from_template(template)

    # 3. Bulunan 5 farklı belgeyi aralarına boşluk koyarak tek bir metin haline getiren fonksiyon
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # 4. LCEL (LangChain Expression Language) ile zinciri kuruyoruz
    # Sırasıyla: Soruyu al -> Belgeleri bul ve formatla -> Prompt'a yerleştir -> Groq'a gönder -> Metin olarak çıkar
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain

if __name__ == "__main__":
    print("\n[INFO] Tubibot V2 Tam Sistem (RAG) Başlatılıyor...")
    print("-" * 60)
    
    zincir = get_rag_chain()
    
    # İŞTE O BÜYÜK TEST SORUSU
    soru = "2209-A projesine kimler başvuru yapabilir? Hangi bölüm veya sınıf öğrencileri başvurmaya hak kazanır?"
    print(f"[KULLANICI]: {soru}\n")
    
    print("[TUBİBOT DÜŞÜNÜYOR...]\n")
    cevap = zincir.invoke(soru)
    
    print(f"[TUBİBOT V2]:\n{cevap}")
    print("=" * 60)