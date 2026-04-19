"""
Notebook testleri için ortak PASS/FAIL toplayıcı.

Kullanım:
    from _helpers.runner import TestRunner
    runner = TestRunner("ingestion/test_json_loader")
    runner.check("Doküman sayısı > 0", len(docs) > 0, f"{len(docs)} adet")
    sys.exit(runner.summary())

Varlıklar:
- PASS / FAIL işaretçileri.
- TestRunner: her satırı anında yazar, sonunda X/Y özeti ve exit code döner.
- section(title): görsel ayraç yazdırır (testi gruplamak için).
"""
import os
import sys


# Windows cp1254 Türkçe kod sayfası emoji / özel karakterleri kodlayamaz.
# Konsol çıkışını UTF-8'e zorla (Python 3.7+).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


_ASCII = os.getenv("TUBIBOT_ASCII_TESTS") == "1"

PASS = "[PASS]" if _ASCII else "✅"
FAIL = "[FAIL]" if _ASCII else "❌"
INFO = "[INFO] " if _ASCII else "ℹ️ "


def section(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


class TestRunner:
    def __init__(self, title: str):
        self.title = title
        self.results: list = []
        section(title)

    def check(self, label: str, condition: bool, details: str = "") -> bool:
        mark = PASS if condition else FAIL
        suffix = f" — {details}" if details else ""
        print(f"  {mark} {label}{suffix}")
        self.results.append((label, bool(condition), details))
        return bool(condition)

    def info(self, label: str, details: str = ""):
        """Bilgi satırı yazar — PASS/FAIL sayacını etkilemez."""
        suffix = f" — {details}" if details else ""
        print(f"  {INFO}{label}{suffix}")

    def summary(self) -> int:
        total = len(self.results)
        passed = sum(1 for _, ok, _ in self.results if ok)
        if _ASCII:
            status = "[OK] BASARILI" if passed == total else "[FAIL] BASARISIZ"
        else:
            status = "🎉 BAŞARILI" if passed == total else "⚠️  BAŞARISIZ"
        print(f"\n  [{self.title}] {passed}/{total} kontrol geçti.  {status}")
        return 0 if passed == total else 1
