"""
TEST 5: Prompt & Kaynak Referansları
Prompt template'inin kaynak referansları, hallüsinasyon koruması ve format kurallarını test eder.
"""
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

PASS = "✅ GEÇTI"
FAIL = "❌ BASARISIZ"


def test_prompt_and_sources():
    """Prompt kaynak referansları oluşturuyor mu?"""
    print("\n" + "="*60)
    print("TEST 5: Prompt & Kaynak Referansları (main.py)")
    print("="*60)
    from main import format_docs_plain, RAG_SYSTEM_PROMPT
    from langchain_core.documents import Document
    
    # Sahte dokümanlarla test
    test_docs = [
        Document(
            page_content="2209-A programına lisans öğrencileri başvurabilir.",
            metadata={"source_document": "2209-A Çağrı Duyurusu", "section_heading": "Madde 5", "document_type": "cagri_duyurusu"}
        ),
        Document(
            page_content="Bütçe üst limiti 7.500 TL'dir.",
            metadata={"source_document": "2209-A Çağrı Duyurusu", "section_heading": "Genel", "document_type": "cagri_duyurusu"}
        ),
    ]
    
    formatted = format_docs_plain(test_docs)
    
    has_separator = "---" in formatted
    has_content = "lisans öğrencileri" in formatted
    
    print(f"  {PASS if has_separator else FAIL} Chunk'lar arasında ayırıcı var")
    print(f"  {PASS if has_content else FAIL} İçerik korunuyor")
    
    # Prompt'ta kritik kurallar var mı
    has_hallucination_guard = "uydurma" in RAG_SYSTEM_PROMPT.lower() or "asla" in RAG_SYSTEM_PROMPT.lower()
    has_cot = "analiz" in RAG_SYSTEM_PROMPT.lower() or "kapsam" in RAG_SYSTEM_PROMPT.lower() or "adım" in RAG_SYSTEM_PROMPT.lower()
    has_format = "eksiksiz" in RAG_SYSTEM_PROMPT.lower() or "liste" in RAG_SYSTEM_PROMPT.lower()
    
    print(f"  {PASS if has_hallucination_guard else FAIL} Hallüsinasyon koruması prompt'ta var")
    print(f"  {PASS if has_cot else FAIL} Chain-of-Thought talimatı var")
    print(f"  {PASS if has_format else FAIL} Yapılandırılmış cevap formatı talimatı var")
    
    result = has_source_ref and has_separator and has_content and has_hallucination_guard
    print(f"\n  {'🎉 TEST BAŞARILI!' if result else '⚠️ TEST BAŞARISIZ!'}")
    return result


if __name__ == "__main__":
    test_prompt_and_sources()
