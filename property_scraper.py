# List of free proxies (can be updated with working proxies)
PROXIES = [
    None,  # No proxy (direct)
    # Example proxies (replace with working ones if needed)
    # "http://51.158.68.68:8811",
    # "http://185.61.152.137:8080",
    # "http://103.216.82.22:6667",
]
# List of user agents for rotating requests (helps avoid blocking)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Mobile Safari/537.36",
]
# Property24 scraper
def fetch_property24():
    print("[SCRAPER] Starting Property24 scraper...")
    print(f"[SCRAPER] Requesting URL: {url}")
    print(f"[SCRAPER] Found {len(cards)} property cards on Property24 page {page}.")
            print(f"[SCRAPER] Extracted listing: title='{title}', location='{location}', price={price}, agency='{agency}', link='{link}'")
    print(f"[SCRAPER] Total listings scraped from Property24: {len(properties)}")
    source = "property24"
    base_url = "https://www.property24.com/industrial-property-for-sale/alias/garden-route/1/western-cape/9"
    properties = []
    page = 1
    while True:
        url = base_url if page == 1 else f"{base_url}/p{page}"
        html = get_html(url)
        if not html:
            break
        soup = BeautifulSoup(html, "html.parser")
        # Try multiple selectors for robustness
        cards = soup.select("div.p24_regularTile")
        if not cards:
            cards = soup.select(".js_resultTile")
        print(f"Found {len(cards)} property cards on Property24 page {page}.")
        if not cards:
            break
        for listing in cards:
            link_tag = listing.select_one("a[href]")
            link = link_tag["href"] if link_tag and link_tag.get("href") else ""
            if link.startswith("/"):
                link = "https://www.property24.com" + link
            title_tag = listing.select_one(".p24_title, .p24_propertyTitle")
            title = title_tag.text.strip() if title_tag else ""
            location_tag = listing.select_one(".p24_location")
            location = location_tag.text.strip() if location_tag else ""
            price_tag = listing.select_one(".p24_price")
            price_str = price_tag.text if price_tag else ""
            price_digits = re.sub(r"[^\d]", "", price_str)
            price = int(price_digits) if price_digits else 0
            agency_tag = listing.select_one(".p24_brandingLogoBoosted, .p24_branding img")
            agency = agency_tag["alt"].strip() if agency_tag and agency_tag.get("alt") else "Property24"
            if title and location and link and price:
                prop = Property(title, price, location, agency, link, datetime.today().date())
                prop.source = source
                properties.append(prop)
        page += 1
        time.sleep(random.uniform(2, 5))
    return properties, True
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import random
from models import Property
import time
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
    max_retries = 5
    for attempt in range(max_retries):
        proxy = random.choice(PROXIES)
        proxies = {"http": proxy, "https": proxy} if proxy else None
        try:
            # Longer random delay between 5 and 15 seconds
            time.sleep(random.uniform(5, 15))
            response = requests.get(url, headers=headers, timeout=20, proxies=proxies)
            response.raise_for_status()
            print(f"[SCRAPER] Success for {url} using proxy: {proxy}")
            return response.text
        except requests.exceptions.HTTPError as e:
            if response.status_code == 503:
                print(f"[ERROR] 503 for {url} (attempt {attempt+1}/{max_retries}), proxy: {proxy}, retrying after delay...")
                time.sleep(random.uniform(20, 40))
                continue
            print(f"[ERROR] HTTP error for {url} -> {e}, proxy: {proxy}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Request failed for {url} -> {e}, proxy: {proxy}")
            time.sleep(random.uniform(10, 20))
            continue
    print(f"[ERROR] Max retries exceeded for {url}")
    return None


def fetch_privateproperty():
    print("[SCRAPER] Starting PrivateProperty scraper...")
    print(f"[SCRAPER] Requesting URL: {url}")
    print(f"[SCRAPER] Found {len(cards)} property cards on PrivateProperty page {page}.")
            print(f"[SCRAPER] Extracted listing: title='{title}', location='{location}', price={price}, agency='{agency}', link='{link}'")
    print(f"[SCRAPER] Total listings scraped from PrivateProperty: {len(properties)}")
    source = "privateproperty"
    base_url = "https://www.privateproperty.co.za/commercial-sales/western-cape/garden-route/52?pt=6"
    properties = []
    page = 1
    while True:
        url = base_url if page == 1 else f"{base_url}&page={page}"
        html = get_html(url)
        if not html:
            break
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("a.listing-result, div.js_resultTile")
        print(f"Found {len(cards)} property cards on PrivateProperty page {page}.")
        if not cards:
            break
        for listing in cards:
            title_tag = listing.select_one(".listing-result__title, .p24_title")
            title = title_tag.text.strip() if title_tag else ""
            if not title or not any(k in title.lower() for k in ["industrial", "warehouse", "commercial", "space"]):
                continue
            price_str = listing.select_one(".listing-result__price, .p24_price").text.strip() if listing.select_one(".listing-result__price, .p24_price") else ""
            price_digits = re.sub(r"[^\d]", "", price_str)
            price = int(price_digits) if price_digits else 0
            location = listing.select_one(".listing-result__desktop-suburb, .p24_location").text.strip() if listing.select_one(".listing-result__desktop-suburb, .p24_location") else "Garden Route"
            agency = "Private Listing" if listing.select_one(".listing-result__listed-privately") else "Unknown Agency"
            href = listing.get("href")
            link = "https://www.privateproperty.co.za" + href if href and href.startswith("/") else href or ""
            print(f"Scraped (PrivateProperty): {title} | {location} | {price} | {agency}")
            prop = Property(title, price, location, agency, link, datetime.today().date())
            prop.source = source
            properties.append(prop)
        page += 1
        time.sleep(random.uniform(2, 5))
    return properties, True

def fetch_pamgolding():
    print("[SCRAPER] Starting Pam Golding scraper...")
    print(f"[SCRAPER] Requesting URL: {url}")
    print(f"[SCRAPER] Found {len(cards)} property cards on Pam Golding page {page}.")
            print(f"[SCRAPER] Extracted listing: title='{title}', location='{location}', price={price}, agency='{agency}', link='{link}'")
    print(f"[SCRAPER] Total listings scraped from Pam Golding: {len(properties)}")
    source = "pamgolding"
    base_url = "https://www.pamgolding.co.za/property-search/commercial-industrial-properties-for-sale-garden-route/510"
    properties = []
    page = 1
    while True:
        url = base_url if page == 1 else f"{base_url}?page={page}"
        html = get_html(url)
        if not html:
            break
        soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("article.pgp-property__item")
        print(f"Found {len(cards)} property cards on Pam Golding page {page}.")
        if not cards:
            break
        for listing in cards:
            # Extract link
            link_tag = listing.select_one(".pgp-property-image a[href]")
            href = link_tag["href"] if link_tag and link_tag.get("href") else ""
            link = "https://www.pamgolding.co.za" + href if href.startswith("/") else href
            # Extract title
            title_tag = listing.select_one(".pgp-description")
            title = title_tag.text.strip() if title_tag else ""
            # Extract price
            price_tag = listing.select_one(".pgp-price")
            price_str = price_tag.text.strip() if price_tag else ""
            price_digits = re.sub(r"[^\d]", "", price_str)
            price = int(price_digits) if price_digits else 0
            # Extract location from title if possible
            location = "Garden Route"
            if ' for sale in ' in title:
                parts = title.rsplit(' for sale in ', 1)
                title = parts[0].strip()
                location = parts[1].strip()
            agency = "Pam Golding"
            print(f"Scraped (Pam Golding): {title} | {location} | {price} | {agency}")
            prop = Property(title, price, location, agency, link, datetime.today().date())
            prop.source = source
            properties.append(prop)
        page += 1
        time.sleep(random.uniform(2, 5))
    if properties:
        return properties, True
    else:
        return [], False

def fetch_sahometraders():
    print("[SCRAPER] Starting SAHometraders scraper...")
    print(f"[SCRAPER] Requesting URL: {url}")
    print(f"[SCRAPER] Found {len(cards)} property cards on SAHometraders page {page}.")
            print(f"[SCRAPER] Extracted listing: title='{title}', location='{location}', price={price}, agency='{agency}', link='{link}'")
    print(f"[SCRAPER] Total listings scraped from SAHometraders: {len(properties)}")
    source = "sahometraders"
    base_url = "https://www.sahometraders.co.za/industrial-property-for-sale-in-garden-route-as1"
    properties = []
    page = 1
    while True:
        url = base_url if page == 1 else f"{base_url}?page={page}"
        html = get_html(url)
        if not html:
            break
        soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("div.p24_regularTile")
        print(f"Found {len(cards)} property cards on SAHometraders page {page}.")
        if not cards:
            break
        for listing in cards:
            # Extract link
            link_tag = listing.select_one("a[href]")
            href = link_tag["href"] if link_tag and link_tag.get("href") else ""
            link = "https://www.sahometraders.co.za" + href if href.startswith("/") else href
            # Extract price
            price_tag = listing.select_one(".p24_price")
            price_str = price_tag.text.strip() if price_tag else ""
            price_digits = re.sub(r"[^\d]", "", price_str)
            price = int(price_digits) if price_digits else 0
            # Extract title
            title_tag = listing.select_one(".p24_propertyTitle")
            title = title_tag.text.strip() if title_tag else "No Title"
            # Extract location
            location_tag = listing.select_one(".p24_location")
            location = location_tag.text.strip() if location_tag else ""
            # Extract agency
            agency_tag = listing.select_one(".p24_branding img")
            agency = agency_tag["alt"].strip() if agency_tag and agency_tag.get("alt") else "SAHometraders"
            print(f"Scraped (SAHometraders): {title} | {location} | {price} | {agency}")
            prop = Property(title, price, location, agency, link, datetime.today().date())
            prop.source = source
            properties.append(prop)
        page += 1
        time.sleep(random.uniform(2, 5))
    return properties, True

def fetch_all_properties():
    print("[SCRAPER] Starting fetch_all_properties...")
    print(f"[SCRAPER] Calling {fetch_func.__name__}")
            print(f"[SCRAPER] {fetch_func.__name__} returned {len(props)} properties, success={success}")
    print(f"[SCRAPER] Total filtered properties: {len(all_properties)}")
    all_properties = []
    successful_sources = []
    fetch_funcs = [
        # fetch_property24,  # Commented out to prevent blocking
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
                # Filter out rentals and incomplete listings
                filtered = []
                for p in props:
                    # Exclude rentals by checking title and price_str
                    title_str = str(getattr(p, 'title', '')).lower()
                    price_str = str(getattr(p, 'price', ''))
                    if 'rent' in title_str or 'rental' in title_str:
                        continue
                    # Exclude listings with missing info
                    if not getattr(p, 'title', None) or not getattr(p, 'location', None) or not getattr(p, 'link', None):
                        continue
                    # Exclude listings with link pointing to the web app
                    if 'propertytracker-webapp' in str(getattr(p, 'link', '')):
                        continue
                    filtered.append(p)
                all_properties.extend(filtered)
        except Exception as e:
            print(f"[ERROR] {fetch_func.__name__} failed: {e}")
    return all_properties, successful_sources