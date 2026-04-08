"""
TUBIBOT V2 - RAG Değerlendirme Çerçevesi
Farklı soru türlerini test eder ve cevap kalitesini ölçer.
"""
import os
import sys
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import get_rag_chain

# ====================================================================
# Test Soruları — her biri farklı bir yeteneği test eder
# ====================================================================
TEST_CASES = [
    # --- Doğrudan Bilgi Soruları ---
    {
        "question": "2209-A projesine kimler başvurabilir?",
        "type": "factual",
        "expected_keywords": ["lisans", "öğrenci", "başvur"],
        "description": "Başvuru koşulları belgesi — doğrudan bilgi",
    },
    {
        "question": "2209-A proje bütçe üst limiti nedir?",
        "type": "factual",
        "expected_keywords": ["7.500", "bütçe", "limit"],
        "description": "Çağrı duyurusu — bütçe bilgisi",
    },
    # --- Listeleme Soruları ---
    {
        "question": "TÜBİTAK öncelikli alanlar nelerdir?",
        "type": "enumeration",
        "expected_keywords": ["öncelikli"],
        "min_length": 200,
        "description": "Öncelikli alanlar — tam liste beklenir",
    },
    {
        "question": "SKA 14 (Sudaki Yaşam) hedefleri nelerdir?",
        "type": "enumeration",
        "expected_keywords": ["14", "hedef"],
        "min_length": 150,
        "description": "SKA hedefleri — eksiksiz listeleme",
    },
    # --- Kısaltma / Kavram Soruları ---
    {
        "question": "SKA nedir?",
        "type": "concept",
        "expected_keywords": ["sürdürülebilir", "kalkınma"],
        "description": "Kısaltma açılımı ve tanım",
    },
    {
        "question": "2209-A programının amacı nedir?",
        "type": "concept",
        "expected_keywords": ["araştırma", "proje"],
        "description": "Program amacı",
    },
    # --- Çapraz Belge Soruları ---
    {
        "question": "Öncelikli alanlardan hangisi iklim değişikliği ile ilgilidir?",
        "type": "cross_document",
        "expected_keywords": ["iklim"],
        "description": "Öncelikli alanlar + SKA çapraz ilişki",
    },
    # --- Kapsam Dışı Sorular (Ret beklenir) ---
    {
        "question": "TÜBİTAK başkanının adı nedir?",
        "type": "out_of_scope",
        "expected_keywords": ["ulaşamadım", "bulunamadı"],
        "description": "Kapsam dışı — reddetmesi beklenir",
    },
    {
        "question": "2209-A başvuru sonuçları ne zaman açıklanır?",
        "type": "out_of_scope",
        "expected_keywords": ["ulaşamadım", "bulunamadı"],
        "description": "Belgede olmayan bilgi — ret beklenir",
    },
    # --- Koşullu Sorular ---
    {
        "question": "2209-A projesinde bütçe kalemleri nelerdir?",
        "type": "conditional",
        "expected_keywords": ["bütçe"],
        "description": "Bütçe kalemleri detayı",
    },
]


def evaluate_answer(test_case, answer):
    """Bir cevabı test kriterlerine göre değerlendir."""
    results = {
        "question": test_case["question"],
        "type": test_case["type"],
        "description": test_case["description"],
        "passed": True,
        "checks": [],
    }

    answer_lower = answer.lower()

    # Kontrol 1: Boş cevap mı?
    if len(answer.strip()) < 20:
        results["checks"].append(("Cevap çok kısa", False))
        results["passed"] = False
    else:
        results["checks"].append(("Cevap yeterli uzunlukta", True))

    # Kontrol 2: Beklenen anahtar kelimeler var mı?
    keywords_found = []
    keywords_missing = []
    for kw in test_case.get("expected_keywords", []):
        if kw.lower() in answer_lower:
            keywords_found.append(kw)
        else:
            keywords_missing.append(kw)

    if keywords_missing:
        results["checks"].append((f"Eksik anahtar kelimeler: {keywords_missing}", False))
        results["passed"] = False
    else:
        results["checks"].append((f"Tüm anahtar kelimeler bulundu: {keywords_found}", True))

    # Kontrol 3: Minimum uzunluk (listeleme soruları için)
    min_len = test_case.get("min_length", 50)
    if len(answer) < min_len:
        results["checks"].append((f"Cevap çok kısa: {len(answer)} < {min_len} karakter", False))
        results["passed"] = False
    else:
        results["checks"].append((f"Uzunluk yeterli: {len(answer)} karakter", True))

    # Kontrol 4: Halüsinasyon belirtisi — kaynak referansı olmamalı
    hallucination_markers = ["[kaynak", "[source", "[ref", "[belge"]
    has_hallucination = any(marker in answer_lower for marker in hallucination_markers)
    if has_hallucination:
        results["checks"].append(("Kaynak referansı tespit edildi (olmamalı)", False))
        results["passed"] = False
    else:
        results["checks"].append(("Kaynak referansı yok (doğru)", True))

    return results


def run_evaluation():
    """Tüm test senaryolarını çalıştır ve raporla."""
    print("\n" + "=" * 70)
    print("  TUBIBOT V2 — RAG DEĞERLENDİRME RAPORU")
    print("=" * 70)

    rag_chain = get_rag_chain()

    total = len(TEST_CASES)
    passed = 0
    failed = 0
    results_all = []

    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n[{i}/{total}] {test_case['description']}")
        print(f"  Soru: {test_case['question']}")

        start = time.time()
        try:
            answer = rag_chain(test_case["question"])
        except Exception as e:
            answer = f"[HATA] {e}"
        elapsed = time.time() - start

        print(f"  Süre: {elapsed:.1f}s")
        print(f"  Cevap: {answer[:150]}{'...' if len(answer) > 150 else ''}")

        result = evaluate_answer(test_case, answer)
        result["elapsed"] = elapsed
        result["answer"] = answer
        results_all.append(result)

        for check_msg, check_passed in result["checks"]:
            icon = "✅" if check_passed else "❌"
            print(f"  {icon} {check_msg}")

        if result["passed"]:
            passed += 1
            print("  → GEÇTI ✅")
        else:
            failed += 1
            print("  → BAŞARISIZ ❌")

    # Özet
    print("\n" + "=" * 70)
    print("  ÖZET")
    print("=" * 70)
    print(f"  Toplam: {total} | Geçen: {passed} | Başarısız: {failed}")
    print(f"  Başarı oranı: {passed/total*100:.0f}%")

    # Türe göre dağılım
    by_type = {}
    for r in results_all:
        t = r["type"]
        if t not in by_type:
            by_type[t] = {"passed": 0, "total": 0}
        by_type[t]["total"] += 1
        if r["passed"]:
            by_type[t]["passed"] += 1

    print("\n  Türe göre:")
    for t, stats in by_type.items():
        print(f"    {t}: {stats['passed']}/{stats['total']}")

    avg_time = sum(r["elapsed"] for r in results_all) / len(results_all)
    print(f"\n  Ortalama cevap süresi: {avg_time:.1f}s")
    print("=" * 70)

    return results_all


if __name__ == "__main__":
    run_evaluation()
