import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import random
import time
import json
from models import Property
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
            price = int(re.sub(r"[^\d]", "", price_match.group(1))) if price_match else 0
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
    url = "https://www.privateproperty.co.za/commercial-sales/western-cape/garden-route/52?pt=6"
    html = get_html(url)
    if not html:
        return [], False
    soup = BeautifulSoup(html, "html.parser")
    # Updated selector and parsing for PrivateProperty
    properties = []
    anchors = soup.find_all("a", href=True)
    for a in anchors:
        href = a["href"]
        # Only include property detail pages, not navigation/area links
        if "/commercial-sales/" in href and re.search(r"/T\d+$", href):
            link = "https://www.privateproperty.co.za" + href if href.startswith("/") else href
            text = a.get_text(" ", strip=True)
            price_match = re.search(r"R\s*([\d\s,]+)", text)
            price = int(re.sub(r"[^\d]", "", price_match.group(1))) if price_match else 0
            if price == 0:
                continue  # Skip listings with no price
            # Clean up title: remove price, area info, and extra whitespace
            title = re.sub(r"R\s*[\d\s,]+", "", text)
            title = re.sub(r"\d+\s*m²", "", title)
            title = re.sub(r"Industrial space", "", title, flags=re.IGNORECASE)
            title = re.sub(r"\s+", " ", title).strip()
            title = title[:80] if title else "Commercial Property"
            # Try to extract location from link or text
            location_match = re.search(r"/garden-route/([a-zA-Z0-9-]+)/", href)
            location = location_match.group(1).replace("-", " ").title() if location_match else "Garden Route"
            agency = "PrivateProperty"
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
            # Only add if title and location are not empty and link is a property detail
            if title and location and link:
                properties.append(prop)
    print(f"PrivateProperty: Found {len(properties)} property cards.")
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
    url = "https://www.sahometraders.co.za/industrial-property-for-sale-in-garden-route-as1"
    html = get_html(url)
    if not html:
        return [], False
    soup = BeautifulSoup(html, "html.parser")
    properties = []
    # Updated selector for SAHometraders (based on provided HTML)
    cards = soup.find_all("div", class_="js_listingTile")
    print(f"SAHometraders: Found {len(cards)} property cards.")
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
            properties.append(prop)
        except Exception as e:
            print(f"SAHometraders: Error parsing card: {e}")

# Currency exchange scraping

def fetch_all_properties():
    fetch_funcs = [
        fetch_property24,
        fetch_privateproperty,
        fetch_pamgolding,
        fetch_sahometraders
    ]
    all_properties = []
    successful_sources = []
    for fetch_func in fetch_funcs:
        try:
            props, success = fetch_func()
            print(f"{fetch_func.__name__}: Found {len(props)} properties.")
            if success and props:
                all_properties.extend(props)
                successful_sources.append(fetch_func.__name__)
        except Exception as e:
            print(f"Error running {fetch_func.__name__}: {e}")
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
    # Deduplicate by link before saving
    seen_links = set()
    unique_properties = []
    for prop in properties:
        link = prop['link'] if isinstance(prop, dict) else getattr(prop, 'link', None)
        if link and link not in seen_links:
            unique_properties.append(prop)
            seen_links.add(link)
    print(f"Saving {len(unique_properties)} properties to {filename}")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(unique_properties, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(unique_properties)} properties to {filename}")

def scrape_and_update_listings():
    properties, sources = fetch_all_properties()
    print(f"Scraped {len(properties)} properties from sources: {sources}")
    if not properties:
        print("No properties found. listings.json will remain empty.")
    rate = get_exchange_rate()
    for prop in properties:
        price_val = None
        if isinstance(prop, dict) and 'price' in prop and prop['price']:
            try:
                price_val = float(prop['price'])
            except Exception:
                price_val = None
        if price_val is not None and rate:
            prop['price_gbp'] = round(price_val * rate, 2)
    save_properties_to_json(properties)
    print(f"Saved {len(properties)} properties to listings.json.")

if __name__ == "__main__":
    print("Starting property scraper main block...")
    print("Calling scrape_and_update_listings()...")
    scrape_and_update_listings()