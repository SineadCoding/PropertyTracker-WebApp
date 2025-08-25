import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import random
import time
import json
from models import Property

import os
LISTINGS_FILE = "listings.json"
UNVERIFIED_LIMIT = 3

def property_to_dict(prop):
    return {
        "title": prop.get("title", "") if isinstance(prop, dict) else getattr(prop, "title", ""),
        "location": prop.get("location", "") if isinstance(prop, dict) else getattr(prop, "location", ""),
        "price": prop.get("price", 0) if isinstance(prop, dict) else getattr(prop, "price", 0),
        "agency": prop.get("agency", "") if isinstance(prop, dict) else getattr(prop, "agency", ""),
        "link": prop.get("link", "") if isinstance(prop, dict) else getattr(prop, "link", ""),
        "date": str(prop.get("date", "")) if isinstance(prop, dict) else str(getattr(prop, "date", "")),
        "source": prop.get("source", "unknown") if isinstance(prop, dict) else getattr(prop, "source", "unknown"),
        "sold": prop.get("sold", False) if isinstance(prop, dict) else getattr(prop, "sold", False),
        "status": prop.get("status", "active") if isinstance(prop, dict) else getattr(prop, "status", "active"),
        "missing_count": prop.get("missing_count", 0) if isinstance(prop, dict) else getattr(prop, "missing_count", 0)
    }

def dict_to_property(d):
    date_val = d.get("date", "")
    if isinstance(date_val, str) and date_val:
        try:
            date_val = datetime.fromisoformat(date_val).date()
        except Exception:
            pass
    p = dict(d)
    p["date"] = date_val
    return p

def load_previous_properties():
    if not os.path.exists(LISTINGS_FILE):
        return []
    with open(LISTINGS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [dict_to_property(d) for d in data]

def save_properties(properties):
    with open(LISTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump([property_to_dict(p) for p in properties], f, indent=2, ensure_ascii=False)

def merge_properties(new_props, old_props, successful_sources):
    new_by_source = {}
    for p in new_props:
        new_by_source.setdefault(p.get("source", "unknown"), {})[p["link"]] = p

    old_by_source = {}
    for p in old_props:
        old_by_source.setdefault(p.get("source", "unknown"), {})[p["link"]] = p

    merged = []

    for source in successful_sources:
        new_links = set(new_by_source.get(source, {}))
        old_links = set(old_by_source.get(source, {}))

        # Listings found in new scrape: reset status
        for link, p in new_by_source.get(source, {}).items():
            p["sold"] = False
            p["status"] = "active"
            p["missing_count"] = 0
            merged.append(p)

        # Listings missing from new scrape: increment missing_count
        for link in old_links - new_links:
            old = old_by_source[source][link]
            old["missing_count"] = old.get("missing_count", 0) + 1
            if old["missing_count"] >= UNVERIFIED_LIMIT:
                old["sold"] = True
                old["status"] = "sold"
            else:
                old["sold"] = False
                old["status"] = "unverified"
            merged.append(old)

    # Listings from sources not scraped this time: keep as is
    for source in old_by_source:
        if source not in successful_sources:
            for link, p in old_by_source[source].items():
                if not any((x["link"] == p["link"] and x.get("source", "unknown") == p.get("source", "unknown")) for x in merged):
                    merged.append(p)

    return merged
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import random
import time
import json
import re
import random
from models import Property
import time
import random
import json

# ✅ List of User-Agents to rotate
USER_AGENTS = [
    # Chrome (Windows, Mac, Linux, Android, iOS)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    # Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13.3; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    # Safari (Mac, iOS)
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
    "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    # Googlebot
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    # Bingbot
    "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
]

def get_html(url):
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": random.choice(["en-US,en;q=0.9", "en-GB,en;q=0.8", "en;q=0.7"]),
        "Referer": random.choice([
            "https://www.google.com/",
            "https://www.bing.com/",
            "https://duckduckgo.com/",
            "https://www.yahoo.com/"
        ]),
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    try:
        # Random delay between 2 and 7 seconds
        time.sleep(random.uniform(2, 7))
        response = requests.get(url, headers=headers, timeout=12)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request failed for {url} -> {e}")
        return None

def fetch_property24():
    source = "property24"
    url = "https://www.property24.com/industrial-property-for-sale/alias/garden-route/1/western-cape/9"
    html = get_html(url)
    if not html:
        return [], False
    soup = BeautifulSoup(html, "html.parser")
    properties = []
    # Updated selector and parsing for Property24
    properties = []
    anchors = soup.find_all("a", href=True)
    for a in anchors:
        href = a["href"]
        if href.startswith("/for-sale/"):
            link = "https://www.property24.com" + href
            # Try to get price and title from surrounding text
            parent = a.parent
            text = parent.get_text(" ", strip=True) if parent else a.get_text(strip=True)
            price_match = re.search(r"R\s*([\d\s,]+)", text)
            if price_match:
                price_str = re.sub(r"[^\d]", "", price_match.group(1))
                try:
                    price = int(price_str) if price_str else 0
                except Exception:
                    price = 0
            else:
                price = 0
            title_match = re.search(r"Industrial Property.*", text)
            title = title_match.group(0) if title_match else text[:50]
            location_match = re.search(r"in ([A-Za-z\s]+)", text)
            location = location_match.group(1).strip() if location_match else "Garden Route"
            agency = "Property24"
            prop = {
                "title": title,
                "price": price,
                "location": location,
                "agency": agency,
                "link": link,
                "date": str(datetime.today().date()),
                "source": source,
                "status": "active"
            }
            properties.append(prop)
    print(f"Property24: Found {len(properties)} property cards.")
    if properties:
        print(f"Property24: First property: {properties[0]}")
    return properties, True

def fetch_privateproperty():
    source = "privateproperty"
    base_url = "https://www.privateproperty.co.za"
    category_path = "/commercial-sales/western-cape/garden-route/52"
    properties = []
    seen_links = set()
    page_num = 1
    while True:
        if page_num == 1:
            page_url = f"{base_url}{category_path}?pt=6"
        else:
            page_url = f"{base_url}{category_path}?pt=6&page={page_num}"
        print(f"Scraping PrivateProperty page {page_num}: {page_url}")
        html = get_html(page_url)
        if not html:
            break
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.find_all("a", class_="listing-result", href=True)
        if not cards:
            print(f"No property cards found on page {page_num}. Stopping.")
            break
        new_links = set()
        new_props = []
        for card in cards:
            href = card["href"]
            link = base_url + href if href.startswith("/") else href
            if link in seen_links:
                continue
            new_links.add(link)
            price_tag = card.find("div", class_="listing-result__price")
            price_text = price_tag.get_text(strip=True) if price_tag else ""
            price_match = re.search(r"R\s*([\d\s,]+)", price_text)
            price = int(re.sub(r"[^\d]", "", price_match.group(1))) if price_match else 0
            title_tag = card.find("div", class_="listing-result__title")
            title = title_tag.get_text(" ", strip=True) if title_tag else "Commercial Property"
            location_tag = card.find("span", class_="listing-result__desktop-suburb")
            if not location_tag:
                location_tag = card.find("span", class_="listing-result__mobile-suburb")
            location = location_tag.get_text(strip=True) if location_tag else "Garden Route"
            address_tag = card.find("span", class_="listing-result__address")
            address = ""
            if address_tag:
                address_span = address_tag.find("span", title=True)
                address = address_span["title"] if address_span and address_span.has_attr("title") else ""
            agency = "PrivateProperty"
            prop = {
                "title": title,
                "price": price,
                "location": location,
                "address": address,
                "agency": agency,
                "link": link,
                "date": str(datetime.today().date()),
                "source": source,
                "status": "active"
            }
            if link and price:
                new_props.append(prop)
        if not new_props:
            print(f"No new property cards found on page {page_num}. Stopping.")
            break
        properties.extend(new_props)
        seen_links.update(new_links)
        page_num += 1
    print(f"PrivateProperty: Found {len(properties)} property cards across all pages.")
    if properties:
        print(f"PrivateProperty: First property: {properties[0]}")
    return properties, True


def fetch_pamgolding():
    source = "pamgolding"
    url = "https://www.pamgolding.co.za/property-search/commercial-industrial-properties-for-sale-garden-route/510"
    html = get_html(url)
    if not html:
        return [], False
    soup = BeautifulSoup(html, "html.parser")
    properties = []
    # Updated selector for Pam Golding (based on provided HTML)
    cards = soup.find_all("article", class_="pgp-property__item")  # Already correct
    print(f"Pam Golding: Found {len(cards)} property cards.")
    for card in cards:
        try:
            link_tag = card.find("a")
            href = link_tag.get("href") if link_tag else ""
            link = "https://www.pamgolding.co.za" + href if href and href.startswith("/") else href or ""
            title_tag = card.find("span", class_="pgp-description")
            title = title_tag.get_text(strip=True) if title_tag else ""
            price_tag = card.find("span", class_="pgp-price")
            price_str = price_tag.get_text(strip=True) if price_tag else ""
            price_digits = re.sub(r"[^\d]", "", price_str)
            price = int(price_digits) if price_digits else 0
            location = "Garden Route"
            agency = "Pam Golding"
            prop = {
                "title": title,
                "price": price,
                "location": location,
                "agency": agency,
                "link": link,
                "date": str(datetime.today().date()),
                "source": source,
                "status": "active"
            }
            properties.append(prop)
        except Exception as e:
            print(f"Pam Golding: Error parsing card: {e}")
    if properties:
        print(f"Pam Golding: First property: {properties[0]}")
    return properties, True


def fetch_sahometraders():
    source = "sahometraders"
    base_url = "https://www.sahometraders.co.za/industrial-property-for-sale-in-garden-route-as1"
    properties = []
    page_num = 1
    while True:
        if page_num == 1:
            url = base_url
        else:
            url = f"{base_url}?Page={page_num}"
        print(f"Scraping SAHometraders page {page_num}: {url}")
        html = get_html(url)
        if not html:
            break
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.find_all("div", class_="js_listingTile")
        if not cards:
            print(f"No property cards found on page {page_num}. Stopping.")
            break
        new_props = []
        for card in cards:
            try:
                link_tag = card.find("a")
                href = link_tag.get("href") if link_tag else ""
                link = "https://www.sahometraders.co.za" + href if href and href.startswith("/") else href or ""
                title = card.find("span", class_="p24_propertyTitle")
                title = title.get_text(strip=True) if title else ""
                price_tag = card.find("span", class_="p24_price")
                price_str = price_tag.get_text(strip=True) if price_tag else ""
                price_digits = re.sub(r"[^\d]", "", price_str)
                price = int(price_digits) if price_digits else 0
                location = card.find("span", class_="p24_location")
                location = location.get_text(strip=True) if location else ""
                agency_tag = card.find("span", class_="p24_branding")
                agency = agency_tag.get("title", "SAHometraders") if agency_tag else "SAHometraders"
                prop = {
                    "title": title,
                    "price": price,
                    "location": location,
                    "agency": agency,
                    "link": link,
                    "date": str(datetime.today().date()),
                    "source": source,
                    "status": "active"
                }
                new_props.append(prop)
            except Exception as e:
                print(f"SAHometraders: Error parsing card: {e}")
        if not new_props:
            print(f"No new property cards found on page {page_num}. Stopping.")
            break
        properties.extend(new_props)
        page_num += 1
    print(f"SAHometraders: Found {len(properties)} property cards across all pages.")
    if properties:
        print(f"SAHometraders: First property: {properties[0]}")
    return properties, True

# Currency exchange scraping

def fetch_all_properties():
    # Only enable Property24 scraping
    fetch_funcs = [
        (fetch_property24, "property24"),
        (fetch_privateproperty, "privateproperty"),
        (fetch_pamgolding, "pamgolding"),
        (fetch_sahometraders, "sahometraders")
    ]
    all_properties = []
    successful_sources = []
    for fetch_func, source_name in fetch_funcs:
        try:
            props, success = fetch_func()
            print(f"{source_name}: Found {len(props)} properties.")
            for p in props:
                p["source"] = source_name
            if success and props:
                all_properties.extend(props)
                successful_sources.append(source_name)
        except Exception as e:
            print(f"Error running {source_name}: {e}")
    # Deduplicate by 'link'
    seen_links = set()
    deduped_properties = []
    for prop in all_properties:
        link = prop.get('link') if isinstance(prop, dict) else getattr(prop, 'link', None)
        if link and link not in seen_links:
            deduped_properties.append(prop)
            seen_links.add(link)
    return deduped_properties, successful_sources
def get_exchange_rate():
    # Example: scrape from exchangerate.host
    try:
        resp = requests.get("https://open.er-api.com/v6/latest/ZAR", timeout=10)
        data = resp.json()
        if 'rates' in data and 'GBP' in data['rates']:
            return data['rates']['GBP']
        else:
            print(f"[ERROR] Exchange rate fetch failed: 'rates' or 'GBP' missing in response: {data}")
            return 0.042
    except Exception as e:
        print(f"[ERROR] Exchange rate fetch failed: {e}")
        return 0.042

def save_properties_to_json(properties, filename="listings.json"):
    pass  # replaced by save_properties()

def scrape_and_update_listings():
    old_props = load_previous_properties()
    new_props, successful_sources = fetch_all_properties()
    print(f"Scraped {len(new_props)} properties from sources: {successful_sources}")
    if not new_props:
        print("No properties found. listings.json will remain empty.")
        save_properties([])
        return
    rate = get_exchange_rate()
    for prop in new_props:
        price_val = None
        if 'price' in prop and prop['price']:
            try:
                price_val = float(prop['price'])
            except Exception:
                price_val = None
        if price_val is not None and rate:
            prop['price_gbp'] = round(price_val * rate, 2)
    merged = merge_properties(new_props, old_props, successful_sources)
    save_properties(merged)
    print(f"Saved {len(merged)} properties to listings.json.")

if __name__ == "__main__":
    print("Starting property scraper main block...")
    print("Calling scrape_and_update_listings()...")
    scrape_and_update_listings()