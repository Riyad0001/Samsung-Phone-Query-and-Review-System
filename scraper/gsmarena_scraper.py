"""
Improved scraper that correctly parses GSMArena specs-list structure.
"""
import re
import requests
import time
from bs4 import BeautifulSoup
from database import get_session, Phone, init_db


def clean_text(text):
    if not text:
        return ""
    text = text.replace("\u00a0", " ").replace("\u2009", " ").replace("\u200b", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def scrape_phone_improved(url):
    """Scrape phone specs using the correct specs-list structure."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"  [ERROR] Failed to fetch {url}: {e}")
        return None

    soup = BeautifulSoup(resp.text, "lxml")

    # Phone name
    title_tag = soup.find("h1", class_="specs-phone-name-title")
    if not title_tag:
        title_tag = soup.find("title")
    name = clean_text(title_tag.get_text() if title_tag else "Unknown")
    name = re.sub(r"\s*-\s*Full\s+phone\s+specs.*$", "", name, flags=re.IGNORECASE)
    name = clean_text(name)

    print(f"  Scraping: {name}")

    phone_data = {
        "name": name,
        "brand": "Samsung",
        "gsmarena_url": url,
        "display_size": "",
        "display_type": "",
        "resolution": "",
        "processor": "",
        "ram": "",
        "storage": "",
        "main_camera": "",
        "selfie_camera": "",
        "battery": "",
        "os_version": "",
        "weight": "",
        "dimensions": "",
        "price": "",
    }

    specs_div = soup.find("div", id="specs-list")
    if not specs_div:
        print("  [WARN] No specs-list div found")
        return phone_data

    all_tables = specs_div.find_all("table")
    section_map = {}

    for table in all_tables:
        th = table.find("th")
        section = clean_text(th.get_text()) if th else ""
        rows = table.find_all("tr")
        for row in rows:
            tds = row.find_all("td")
            if len(tds) < 2:
                continue
            label = clean_text(tds[0].get_text(separator=" ", strip=True)).lower()
            spec_val = clean_text(tds[-1].get_text(separator=" ", strip=True))
            if not spec_val:
                continue
            section_map[(section, label)] = spec_val

    # Now map section/label pairs to our fields
    for (section, label), val in section_map.items():
        sl = section.lower()
        if "display" in sl:
            if "size" in label:
                phone_data["display_size"] = val
            elif "type" in label:
                phone_data["display_type"] = val
            elif "resolution" in label:
                phone_data["resolution"] = val
        if "platform" in sl:
            if "chipset" in label:
                phone_data["processor"] = val
            if "os" in label:
                phone_data["os_version"] = val
        if "memory" in sl:
            if "internal" in label:
                phone_data["storage"] = val
        if "main camera" in sl or sl == "main camera":
            if label == "triple" or label == "dual" or label == "single" or label == "quad":
                phone_data["main_camera"] = val
            elif "features" in label:
                continue
            elif "video" in label:
                continue
            elif not phone_data["main_camera"]:
                phone_data["main_camera"] = val
        if "selfie" in sl:
            if label == "single" or label == "dual":
                phone_data["selfie_camera"] = val
            elif not phone_data["selfie_camera"]:
                phone_data["selfie_camera"] = val
        if "battery" in sl:
            if "type" in label:
                phone_data["battery"] = val
            elif not phone_data["battery"]:
                phone_data["battery"] = val
        if "body" in sl:
            if "weight" in label:
                phone_data["weight"] = val
            if "dimensions" in label:
                phone_data["dimensions"] = val
        # Also check labels directly (some specs are not inside sections)
        if "display" in label:
            if "size" in label:
                phone_data["display_size"] = phone_data["display_size"] or val
            elif "type" in label:
                phone_data["display_type"] = phone_data["display_type"] or val
            elif "resolution" in label:
                phone_data["resolution"] = phone_data["resolution"] or val
        if "processor" in label or "chipset" in label:
            phone_data["processor"] = phone_data["processor"] or val
        if "ram" in label:
            phone_data["ram"] = val
        if "storage" in label or "internal" in label:
            phone_data["storage"] = phone_data["storage"] or val
        if "battery" in label:
            phone_data["battery"] = phone_data["battery"] or val
        if "weight" in label:
            phone_data["weight"] = phone_data["weight"] or val
        if "dimensions" in label:
            phone_data["dimensions"] = phone_data["dimensions"] or val
        if "price" in label:
            phone_data["price"] = val

    # No RAM field with this name in GSMArena - extract from internal
    if phone_data["storage"]:
        ram_match = re.search(r"(\d+GB)\s*RAM", phone_data["storage"], re.IGNORECASE)
        if ram_match:
            phone_data["ram"] = ram_match.group(1)

    return phone_data


def scrape_all_phones(urls):
    init_db()
    session = get_session()
    scraped_count = 0

    for i, url in enumerate(urls):
        print(f"[{i + 1}/{len(urls)}] Scraping...")
        data = scrape_phone_improved(url)
        if data is None:
            continue

        existing = session.query(Phone).filter_by(gsmarena_url=url).first()
        if existing:
            for key, val in data.items():
                if key != "gsmarena_url":
                    setattr(existing, key, val)
        else:
            phone = Phone(**data)
            session.add(phone)

        session.commit()
        scraped_count += 1
        time.sleep(1)

    session.close()
    print(f"\nDone! Scraped {scraped_count} phones.")
    return scraped_count


if __name__ == "__main__":
    from config import SAMSUNG_PHONES
    scrape_all_phones(SAMSUNG_PHONES)