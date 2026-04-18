import os

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DUYURULAR_JSON = os.path.join(BACKEND_DIR, "duyurular.json")
HABERLER_JSON = os.path.join(BACKEND_DIR, "haberler.json")
PDF_DIR = os.path.join(BACKEND_DIR, "data", "TübitakBilgi_pdf")
THUMB_DIR = os.path.join(BACKEND_DIR, "data", "dokuman_thumbs")
GUNDEM_DB_DIR = os.path.join(BACKEND_DIR, "data", "gundem_vector_db")
