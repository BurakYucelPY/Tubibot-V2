"""
ingestion/test_pdf_loader.py

pdf_loader.py gerçekten PDF'leri yüklüyor mu ve metadata'yı zenginleştiriyor mu?
PDF_METADATA_MAP'te listelenen dosyaların her biri diskte mevcut mu?

Live test: mevcut backend/data/2209A_pdf klasöründeki PDF'lerle çalışır.
"""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from _helpers.bootstrap import setup_backend_path
BACKEND_ROOT = setup_backend_path()

from _helpers.runner import TestRunner


def main():
    from src.ingestion.pdf_loader import PDF_METADATA_MAP, _get_metadata_for_file, load_pdfs

    runner = TestRunner("ingestion/test_pdf_loader")

    pdf_dir = os.path.join(BACKEND_ROOT, "data", "2209A_pdf")
    runner.check(
        "2209A_pdf dizini mevcut",
        os.path.isdir(pdf_dir),
        pdf_dir,
    )

    existing_pdfs = {f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")} if os.path.isdir(pdf_dir) else set()
    missing_map_files = [f for f in PDF_METADATA_MAP if f not in existing_pdfs]
    runner.check(
        "PDF_METADATA_MAP'teki tüm dosyalar diskte",
        not missing_map_files,
        f"eksik: {missing_map_files}" if missing_map_files else f"{len(PDF_METADATA_MAP)} dosya doğrulandı",
    )

    for fname in PDF_METADATA_MAP:
        meta = _get_metadata_for_file(fname)
        all_fields = all(k in meta for k in ("source_document", "document_type", "year"))
        not_fallback = meta["document_type"] != "diger"
        runner.check(
            f"metadata({fname})",
            all_fields and not_fallback,
            f"type={meta['document_type']}",
        )

    fallback = _get_metadata_for_file("yok_böyle_bir_dosya.pdf")
    runner.check(
        "Fallback metadata 'diger' tipini veriyor",
        fallback["document_type"] == "diger",
        f"source_document={fallback['source_document']}",
    )

    # Gerçek yükleme (maliyetli — dakikalar sürebilir) — sadece pdf_dir varsa
    if os.path.isdir(pdf_dir) and existing_pdfs:
        runner.info("load_pdfs() çağrılıyor (maliyetli, bekleyin)...")
        docs = load_pdfs(pdf_dir)
        runner.check(
            "load_pdfs() boş olmayan doküman listesi döndü",
            len(docs) > 0,
            f"{len(docs)} parça",
        )
        if docs:
            all_have_source = all(d.metadata.get("source_document") for d in docs)
            all_have_type = all(d.metadata.get("document_type") for d in docs)
            runner.check("Tüm dokümanlarda source_document dolu", all_have_source)
            runner.check("Tüm dokümanlarda document_type dolu", all_have_type)

            unique_types = {d.metadata.get("document_type") for d in docs}
            runner.info(f"Yüklenen document_type çeşitleri: {unique_types}")

    return runner.summary()


if __name__ == "__main__":
    sys.exit(main())
