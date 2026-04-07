"""
TEST 1: Metadata Zenginleştirme
PDF dosyalarına doğru metadata'nın eklenip eklenmediğini test eder.
"""
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

PASS = "✅ GEÇTI"
FAIL = "❌ BASARISIZ"


def test_metadata_enrichment():
    """PDF'lere metadata eklendi mi?"""
    print("\n" + "="*60)
    print("TEST 1: Metadata Zenginleştirme (pdf_loader.py)")
    print("="*60)
    from src.ingestion.pdf_loader import PDF_METADATA_MAP, _get_metadata_for_file
    
    # Yeni PDF'lerin mapping'de olmalı
    expected_files = [
        "2209-A_2025_Cagri_Duyurusu.pdf",
        "2209-A_arastirma_onerisi_formu_09102025.pdf",
        "Öncelikli Alanlar.pdf",
        "SKA_Surdurulebilir_Kalkinma.pdf",
        "kimlerbasvurur.pdf"
    ]
    
    all_ok = True
    for f in expected_files:
        meta = _get_metadata_for_file(f)
        has_fields = all(k in meta for k in ["source_document", "document_type", "year"])
        not_fallback = meta["document_type"] != "diger"
        ok = has_fields and not_fallback
        status = PASS if ok else FAIL
        print(f"  {status} {f} → type={meta['document_type']}, source={meta['source_document']}")
        if not ok:
            all_ok = False
    
    # Fallback testi
    fallback = _get_metadata_for_file("bilinmeyen.pdf")
    fb_ok = fallback["document_type"] == "diger"
    print(f"  {PASS if fb_ok else FAIL} Fallback → bilinmeyen dosya 'diger' tipinde")
    
    result = all_ok and fb_ok
    print(f"\n  {'🎉 TEST BAŞARILI!' if result else '⚠️ TEST BAŞARISIZ!'}")
    return result


if __name__ == "__main__":
    test_metadata_enrichment()
