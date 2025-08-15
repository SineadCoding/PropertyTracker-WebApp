# Flask web app for Property Tracker


import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from flask import Flask, render_template, jsonify, request
import json

from property_scraper import fetch_all_properties
from utils import fetch_gbp_exchange_rate

LISTINGS_FILE = os.path.join(os.path.dirname(__file__), '..', 'listings.json')

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/listings')
def get_listings():
    with open(LISTINGS_FILE, 'r', encoding='utf-8') as f:
        listings = json.load(f)
    # Fetch GBP rate
    gbp_rate = fetch_gbp_exchange_rate() or 0.042
    # Add GBP price to each listing, handle string prices
    for listing in listings:
        price = listing.get('price')
        try:
            # If price is a string that can be converted to float, do so
            price_num = float(price)
            listing['price_gbp'] = round(price_num * gbp_rate, 2)
        except (ValueError, TypeError):
            # If price is not a number, show GBP as N/A
            listing['price_gbp'] = None
    return jsonify(listings)

# New route to trigger live scraping and update listings.json

import threading

def scrape_and_update():
    print("[SCRAPER] Starting property scrape...")
    properties, sources = fetch_all_properties()
    print(f"[SCRAPER] Scrape complete. Sources: {sources}. Total properties: {len(properties)}")
    def property_to_dict(prop):
        return {
            "title": getattr(prop, "title", ""),
            "location": prop.location,
            "price": prop.price,
            "agency": prop.agency,
            "link": prop.link,
            "date": str(getattr(prop, "date", "")),
            "source": getattr(prop, "source", "unknown"),
            "sold": getattr(prop, "sold", False),
            "status": getattr(prop, "status", "active"),
            "missing_count": getattr(prop, "missing_count", 0)
        }
    listings = [property_to_dict(p) for p in properties]
    with open(LISTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(listings, f, ensure_ascii=False, indent=2)
    print(f"[SCRAPER] Listings file updated with {len(listings)} properties.")

@app.route('/api/refresh', methods=['POST'])
def refresh_listings():
    thread = threading.Thread(target=scrape_and_update)
    thread.start()
    return jsonify({"success": True, "message": "Scraping started in background."})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
