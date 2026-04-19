"""
TEST 2: Akıllı Chunking
Belge türüne göre farklı chunk boyutları ve başlık tespitini test eder.
"""
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

PASS = "✅ GEÇTI"
FAIL = "❌ BASARISIZ"


def test_smart_chunking():
    """Belge türüne göre farklı chunk boyutları ve başlık tespiti."""
    print("\n" + "="*60)
    print("TEST 2: Akıllı Chunking (processor.py)")
    print("="*60)
    from src.ingestion.processor import CHUNK_CONFIG, _detect_heading, _get_splitter_for_doc_type
    
    # Farklı belge türleri farklı chunk boyutu almalı
    ska_splitter = _get_splitter_for_doc_type("ska_rehberi")
    tubitak_splitter = _get_splitter_for_doc_type("cagri_duyurusu")
    
    size_ok = ska_splitter._chunk_size == 1500 and tubitak_splitter._chunk_size == 800
    print(f"  {PASS if size_ok else FAIL} SKA chunk_size=1500, TÜBİTAK chunk_size=800")
    
    # Başlık tespiti
    h1 = _detect_heading("MADDE 5 - Başvuru Koşulları")
    h2 = _detect_heading("Hedef 14.b Balıkçılık")
    h3 = _detect_heading("Bu düz bir metin parçasıdır ve başlık değildir.")
    
    heading_ok = h1 is not None and h2 is not None and h3 is None
    print(f"  {PASS if heading_ok else FAIL} Başlık tespiti: 'MADDE 5'={h1 is not None}, 'Hedef 14.b'={h2 is not None}, düz metin={h3 is None}")
    
    result = size_ok and heading_ok
    print(f"\n  {'🎉 TEST BAŞARILI!' if result else '⚠️ TEST BAŞARISIZ!'}")
    return result


if __name__ == "__main__":
    test_smart_chunking()
