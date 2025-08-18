# Flask web app for Property Tracker



import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from flask import Flask, render_template, jsonify, request
from property_scraper import fetch_all_properties
from utils import fetch_gbp_exchange_rate
from db_utils import init_db, save_properties_to_db, load_properties_from_db


app = Flask(__name__)
init_db()

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/listings')
def get_listings():
    listings = load_properties_from_db()
    gbp_rate = fetch_gbp_exchange_rate() or 0.042
    for listing in listings:
        price = listing.get('price')
        try:
            price_num = float(price)
            listing['price_gbp'] = round(price_num * gbp_rate, 2)
        except (ValueError, TypeError):
            listing['price_gbp'] = None
    return jsonify(listings)

# New route to trigger live scraping and update listings.json

import threading

def scrape_and_update():
    print("[SCRAPER] Starting property scrape...")
    properties, sources = fetch_all_properties()
    print(f"[DEBUG] Raw properties from scrapers: {properties}")
    print(f"[SCRAPER] Scrape complete. Sources: {sources}. Total properties: {len(properties)}")
    def property_to_dict(prop):
        return {
            "title": getattr(prop, "title", ""),
            "location": getattr(prop, "location", ""),
            "price": getattr(prop, "price", 0),
            "agency": getattr(prop, "agency", ""),
            "link": getattr(prop, "link", ""),
            "date": str(getattr(prop, "date", "")),
            "source": getattr(prop, "source", "unknown"),
            "sold": getattr(prop, "sold", False),
            "status": getattr(prop, "status", "active"),
            "missing_count": getattr(prop, "missing_count", 0)
        }
    listings = [property_to_dict(p) for p in properties]
    print(f"[DEBUG] Listings to be saved: {listings}")
    try:
        save_properties_to_db(listings)
        print(f"[SCRAPER] Listings database updated with {len(listings)} properties.")
    except Exception as e:
        print(f"[ERROR] Failed to save listings to DB: {e}")

@app.route('/api/refresh', methods=['POST'])
def refresh_listings():
    try:
        scrape_and_update()
        return jsonify({"success": True, "message": "Scraping completed."})
    except Exception as e:
        print(f"[ERROR] Scraping failed: {e}")
        return jsonify({"success": False, "message": f"Scraping failed: {e}"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
