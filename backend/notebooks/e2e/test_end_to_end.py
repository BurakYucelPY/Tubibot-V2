"""
TEST 6: Uçtan Uca Test
Gerçek sorularla RAG pipeline'ın tam çalışmasını test eder.
"""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from _helpers.bootstrap import setup_backend_path
setup_backend_path()

PASS = "✅ GEÇTI"
FAIL = "❌ BASARISIZ"


def test_end_to_end():
    """Gerçek soru ile uçtan uca test."""
    print("\n" + "="*60)
    print("TEST 6: Uçtan Uca Test (Gerçek Soru)")
    print("="*60)
    from main import get_rag_chain
    
    chain = get_rag_chain()
    
    # Test 1: Spesifik bilgi sorusu
    soru1 = "2209-A projesine kimler başvuru yapabilir?"
    print(f"  Soru: {soru1}")
    cevap1 = chain(soru1)
    
    # Cevap boş olmamalı, makul uzunlukta olmalı
    has_content = len(cevap1) > 100
    has_source_mention = any(w in cevap1.lower() for w in ["kaynak", "belge", "duyuru", "başvur", "öğrenci", "lisans"])
    
    print(f"  {PASS if has_content else FAIL} Cevap yeterli uzunlukta ({len(cevap1)} karakter)")
    print(f"  {PASS if has_source_mention else FAIL} Cevap ilgili anahtar kelimeler içeriyor")
    print(f"  Cevap (ilk 300 karakter): {cevap1[:300]}...")
    
    # Test 2: SKA sorusu
    soru2 = "İklim değişikliği ile ilgili SKA hedefi hangisidir?"
    print(f"\n  Soru: {soru2}")
    cevap2 = chain(soru2)
    
    has_ska = any(w in cevap2.lower() for w in ["ska", "iklim", "13", "hedef", "sürdürülebilir"])
    print(f"  {PASS if has_ska else FAIL} SKA/iklim anahtar kelimeleri var")
    print(f"  Cevap (ilk 300 karakter): {cevap2[:300]}...")
    
    result = has_content and has_source_mention
    print(f"\n  {'🎉 TEST BAŞARILI!' if result else '⚠️ TEST BAŞARISIZ!'}")
    return result


if __name__ == "__main__":
    test_end_to_end()
