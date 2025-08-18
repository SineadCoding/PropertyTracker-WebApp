import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import random
from models import Property
import time
import random

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

def fetch_privateproperty():
    source = "privateproperty"
    url = "https://www.privateproperty.co.za/for-sale/garden-route/western-cape/9"
    properties = []
    page = 1
    while True:
        paged_url = f"{url}?page={page}"
        html = get_html(paged_url)
        if not html:
            break
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("a.listing-result")
        print(f"[PrivateProperty] Page {page}: Found {len(cards)} property cards.")
        if not cards:
            break
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
        page += 1
        time.sleep(random.uniform(1, 2))
    return properties, bool(properties)

def fetch_pamgolding():
    source = "pamgolding"
    url = "https://www.pamgolding.co.za/property-search/commercial-industrial-properties-for-sale-garden-route/510"
    properties = []
    page = 1
    while True:
        paged_url = f"{url}?page={page}"
        html = get_html(paged_url)
        if not html:
            break
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("article.pgp-property__item")
        print(f"[Pam Golding] Page {page}: Found {len(cards)} property cards.")
        if not cards:
            break
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
        page += 1
        time.sleep(random.uniform(1, 2))
    return properties, bool(properties)

def fetch_sahometraders():
    source = "sahometraders"
    url = "https://www.sahometraders.co.za/industrial-property-for-sale/garden-route/western-cape/9"
    properties = []
    page = 1
    while True:
        paged_url = f"{url}?page={page}"
        html = get_html(paged_url)
        if not html:
            break
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("div.p24_regularTile")
        print(f"[SAHometraders] Page {page}: Found {len(cards)} property cards.")
        if not cards:
            break
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
        page += 1
        time.sleep(random.uniform(1, 2))
    return properties, bool(properties)

def fetch_all_properties():
    all_properties = []
    successful_sources = []
    fetch_funcs = [
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
    return all_properties, successful_sources

# Property24 scraping logic (commented out to prevent blocking)
# def scrape_property24():
#     # Property24 is sensitive to scraping, so this is commented out for now
#     pass