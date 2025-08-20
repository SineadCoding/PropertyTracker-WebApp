import requests
from bs4 import BeautifulSoup
from datetime import datetime
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
    cards = soup.select("div.p24_regularTile")
    print(f"Found {len(cards)} property cards on Property24.")
    for listing in cards:
        link_tag = listing.select_one("a.p24_content")
        link = "https://www.property24.com" + link_tag["href"] if link_tag and link_tag.get("href") else ""
        price_tag = listing.select_one(".p24_price")
        price_str = price_tag.text if price_tag else ""
        price_digits = re.sub(r"[^\d]", "", price_str)
        price = int(price_digits) if price_digits else 0
        title = listing.select_one(".p24_title").text.strip() if listing.select_one(".p24_title") else ""
        location = listing.select_one(".p24_location").text.strip() if listing.select_one(".p24_location") else ""
        agency_tag = listing.select_one(".p24_branding img")
        agency = agency_tag["alt"].strip() if agency_tag and agency_tag.get("alt") else "Property24"
        print(f"Scraped: {title} | {location} | {price} | {agency}")
        prop = Property(title, price, location, agency, link, datetime.today().date())
        prop.source = source
        properties.append(prop)
    return properties, True

def fetch_privateproperty():
    source = "privateproperty"
    url = "https://www.privateproperty.co.za/commercial-sales/western-cape/garden-route/52?pt=6"
    html = get_html(url)
    if not html:
        return [], False

    soup = BeautifulSoup(html, "html.parser")
    properties = []
    cards = soup.select("a.listing-result")
    print(f"Found {len(cards)} property cards on PrivateProperty.")

    for listing in cards:
        title_tag = listing.select_one(".listing-result__title")
        title = title_tag.text.strip() if title_tag else ""
        if not title or not any(k in title.lower() for k in ["industrial", "warehouse", "commercial", "space"]):
            continue

        price_str = listing.select_one(".listing-result__price").text.strip() if listing.select_one(".listing-result__price") else ""
        price_digits = re.sub(r"[^\d]", "", price_str)
        price = int(price_digits) if price_digits else 0

        location = listing.select_one(".listing-result__desktop-suburb").text.strip() if listing.select_one(".listing-result__desktop-suburb") else "Garden Route"
        agency = "Private Listing" if listing.select_one(".listing-result__listed-privately") else "Unknown Agency"
        href = listing.get("href")
        link = "https://www.privateproperty.co.za" + href if href and href.startswith("/") else href or ""

        print(f"Scraped (PrivateProperty): {title} | {location} | {price} | {agency}")
        prop = Property(title, price, location, agency, link, datetime.today().date())
        prop.source = source
        properties.append(prop)
    return properties, True

def fetch_pamgolding():
    source = "pamgolding"
    url = "https://www.pamgolding.co.za/property-search/commercial-industrial-properties-for-sale-garden-route/510"
    html = get_html(url)
    if not html:
        return [], False

    soup = BeautifulSoup(html, "html.parser")
    properties = []
    cards = soup.select("article.pgp-property__item")
    print(f"Found {len(cards)} property cards on Pam Golding.")

    for listing in cards:
        full_title = listing.select_one(".pgp-description").text.strip() if listing.select_one(".pgp-description") else ""
        if not full_title or not any(k in full_title.lower() for k in ["industrial", "warehouse", "commercial"]):
            continue

        title = full_title
        location = "Garden Route"
        if ' for sale in ' in full_title:
            parts = full_title.rsplit(' for sale in ', 1)
            title = parts[0].strip()
            location = parts[1].strip()

        price_str = listing.select_one(".pgp-price").text.strip() if listing.select_one(".pgp-price") else ""
        price_digits = re.sub(r"[^\d]", "", price_str)
        price = int(price_digits) if price_digits else 0

        agency = "Pam Golding"
        href = listing.select_one("a").get("href") if listing.select_one("a") else ""
        link = "https://www.pamgolding.co.za" + href if href.startswith("/") else href

        print(f"Scraped (Pam Golding): {title} | {location} | {price} | {agency}")
        prop = Property(title, price, location, agency, link, datetime.today().date())
        prop.source = source
        properties.append(prop)
    # Only return True if we actually found listings
    if properties:
        return properties, True
    else:
        return [], False

def fetch_sahometraders():
    source = "sahometraders"
    url = "https://www.sahometraders.co.za/industrial-property-for-sale-in-garden-route-as1"
    html = get_html(url)
    if not html:
        return [], False

    soup = BeautifulSoup(html, "html.parser")
    properties = []
    cards = soup.select("div.p24_regularTile")
    print(f"Found {len(cards)} property cards on SAHometraders.")

    for listing in cards:
        link_tag = listing.select_one("a")
        href = link_tag.get("href") if link_tag else ""
        link = "https://www.sahometraders.co.za" + href if href and href.startswith("/") else href or ""
        title = link_tag.get("title", "").strip() if link_tag else ""

        price_tag = listing.select_one(".p24_price")
        price_str = price_tag.contents[0].strip() if price_tag and price_tag.contents else ""
        price_digits = re.sub(r"[^\d]", "", price_str)
        price = int(price_digits) if price_digits else 0

        if not title:
            title = listing.select_one(".p24_propertyTitle").text.strip() if listing.select_one(".p24_propertyTitle") else "No Title"

        location = listing.select_one(".p24_location").text.strip() if listing.select_one(".p24_location") else ""
        agency_tag = listing.select_one(".p24_branding img")
        agency = agency_tag["alt"].strip() if agency_tag and agency_tag.get("alt") else "SAHometraders"

        print(f"Scraped (SAHometraders): {title} | {location} | {price} | {agency}")
        prop = Property(title, price, location, agency, link, datetime.today().date())
        prop.source = source
        properties.append(prop)
    return properties, True

def fetch_all_properties():
    all_properties = []
    successful_sources = []
    fetch_funcs = [
        fetch_property24,
        fetch_privateproperty,
        fetch_pamgolding,
        fetch_sahometraders
    ]
    for fetch_func in fetch_funcs:
        try:
            props, success = fetch_func()
            if success:
                if props and hasattr(props[0], "source"):
                    successful_sources.append(props[0].source)
                elif fetch_func.__name__.startswith("fetch_"):
                    successful_sources.append(fetch_func.__name__[6:])
            all_properties.extend(props)
        except Exception as e:
            print(f"[ERROR] {fetch_func.__name__} failed: {e}")
    # Deduplicate by 'link'
    seen_links = set()
    deduped_properties = []
    for prop in all_properties:
        if hasattr(prop, 'link') and prop.link not in seen_links:
            seen_links.add(prop.link)
            deduped_properties.append(prop)
    return deduped_properties, successful_sources
# Currency exchange scraping
def get_exchange_rate():
    # Example: scrape from exchangerate.host
    try:
        resp = requests.get("https://api.exchangerate.host/latest?base=ZAR&symbols=GBP")
        data = resp.json()
        rate = data['rates']['GBP']
        return rate
    except Exception as e:
        print(f"[ERROR] Exchange rate fetch failed: {e}")
        return None

def save_properties_to_json(properties, filename="listings.json"):
    properties_dicts = [prop for prop in properties]
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(properties_dicts, f, ensure_ascii=False, indent=2)

def scrape_and_update_listings():
    properties, _ = fetch_all_properties()
    rate = get_exchange_rate()
    if rate:
        for prop in properties:
            # Add price_gbp to each property
            price_val = None
            if hasattr(prop, 'price') and prop.price:
                price_val = float(prop.price)
            elif isinstance(prop, dict) and 'price' in prop and prop['price']:
                price_val = float(prop['price'])
            if price_val is not None:
                # Convert ZAR to GBP using the exchange rate
                gbp_val = round(price_val * rate, 2)
                if hasattr(prop, 'price_gbp'):
                    prop.price_gbp = gbp_val
                elif isinstance(prop, dict):
                    prop['price_gbp'] = gbp_val
    save_properties_to_json([prop.__dict__ if hasattr(prop, '__dict__') else prop for prop in properties])