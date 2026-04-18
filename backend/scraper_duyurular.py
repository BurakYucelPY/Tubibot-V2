"""
TÜBİTAK Duyuru Scraper
https://tubitak.gov.tr/tr/duyuru adresinden son 5 sayfayı çeker.
Sonuçları backend/duyurular.json dosyasına yazar.
"""

import json
import os
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://tubitak.gov.tr"
LIST_URL = f"{BASE_URL}/tr/duyuru"
PAGES = 5
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "duyurular.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
}

TR_MONTHS = {
    "Oca": 1, "Şub": 2, "Mar": 3, "Nis": 4,
    "May": 5, "Haz": 6, "Tem": 7, "Ağu": 8,
    "Eyl": 9, "Eki": 10, "Kas": 11, "Ara": 12,
}


def parse_turkish_date(date_str: str) -> datetime:
    try:
        parts = date_str.strip().split()
        return datetime(int(parts[2]), TR_MONTHS.get(parts[1], 1), int(parts[0]))
    except (IndexError, ValueError):
        return datetime(1970, 1, 1)


def fetch_page(url: str) -> BeautifulSoup | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except requests.RequestException as e:
        print(f"[HATA] {url} çekilemedi: {e}")
        return None


def parse_list_page(soup: BeautifulSoup) -> list[dict]:
    items = []
    content_holder = soup.find("div", id="contentHolder")
    if not content_holder:
        return items

    for row in content_holder.select("div.views-row"):
        item = {"tur": "duyuru"}

        img_el = row.select_one(".views-field-field-fotograflar img")
        if img_el and img_el.get("src"):
            src = img_el["src"]
            item["resim_url"] = src if src.startswith("http") else BASE_URL + src
        else:
            item["resim_url"] = ""

        time_el = row.select_one(".views-field-created time")
        item["tarih"] = time_el.get_text(strip=True) if time_el else ""

        title_link = row.select_one(".views-field-title a")
        if title_link:
            item["baslik"] = title_link.get_text(strip=True)
            href = title_link.get("href", "")
            item["kaynak_url"] = href if href.startswith("http") else BASE_URL + href
        else:
            item["baslik"] = ""
            item["kaynak_url"] = ""

        ozet_el = row.select_one(".views-field-field-ozet .field-content")
        item["ozet"] = ozet_el.get_text(strip=True) if ozet_el else ""
        item["tam_icerik"] = ""

        if item["baslik"]:
            items.append(item)

    return items


def fetch_detail_content(url: str) -> str:
    soup = fetch_page(url)
    if not soup:
        return ""
    content_div = soup.select_one("div.field--name-field-icerik")
    if content_div:
        return str(content_div.decode_contents()).strip()
    return ""


def run_scraper() -> list[dict]:
    all_items: list[dict] = []

    for page_num in range(PAGES):
        url = f"{LIST_URL}?page={page_num}"
        print(f"[DUYURU] Sayfa çekiliyor: {url}")
        soup = fetch_page(url)
        if not soup:
            continue
        items = parse_list_page(soup)
        print(f"  -> {len(items)} duyuru bulundu")
        all_items.extend(items)
        time.sleep(1)

    print(f"\n[DUYURU] {len(all_items)} duyurunun detay sayfası çekiliyor...")
    for i, item in enumerate(all_items, 1):
        if item["kaynak_url"]:
            print(f"  [{i}/{len(all_items)}] {item['baslik'][:60]}...")
            item["tam_icerik"] = fetch_detail_content(item["kaynak_url"])
            time.sleep(1)

    all_items.sort(key=lambda x: parse_turkish_date(x["tarih"]), reverse=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] {len(all_items)} duyuru -> {OUTPUT_PATH}")
    return all_items


if __name__ == "__main__":
    run_scraper()
