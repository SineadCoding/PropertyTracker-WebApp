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
        # Link
        link_tag = listing.select_one("a.p24_content")
        link = link_tag["href"] if link_tag and link_tag.get("href") else ""
        if link.startswith("/"):
            link = "https://www.property24.com" + link

        # Title
        title_tag = listing.select_one(".p24_title")
        title = title_tag.text.strip() if title_tag else ""

        # Location
        location_tag = listing.select_one(".p24_location")
        location = location_tag.text.strip() if location_tag else ""

        # Price
        price_tag = listing.select_one(".p24_price")
        price_str = price_tag.text if price_tag else ""
        price_digits = re.sub(r"[^\d]", "", price_str)
        price = int(price_digits) if price_digits else 0

        # Agency
        agency_tag = listing.select_one(".p24_brandingLogoBoosted")
        agency = agency_tag["alt"].strip() if agency_tag and agency_tag.get("alt") else "Property24"

        # Only add if all main info is present
        if title and location and link and price:
            prop = Property(title, price, location, agency, link, datetime.today().date())
            prop.source = source
            properties.append(prop)
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
    try:
        # Random delay between 2 and 7 seconds
        time.sleep(random.uniform(2, 7))
        response = requests.get(url, headers=headers, timeout=12)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request failed for {url} -> {e}")
        return None
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
    url = "https://www.sahometraders.co.za/industrial-property-to-rent-in-garden-route-as1"
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
        price_tag = listing.select_one(".p24_price")
        price_str = price_tag.text if price_tag else ""
        price_digits = re.sub(r"[^\d]", "", price_str)
        price = int(price_digits) if price_digits else 0
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