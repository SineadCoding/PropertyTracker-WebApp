"""
PropertyTracker Web App - Complete Functionality Replica
Modern Flask web application that exactly replicates the Android Kivy app
"""

import json
import os
import threading
import time
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_from_directory
import logging

# Import modules with error handling
try:
    from property_scraper import fetch_all_properties
except ImportError as e:
    print(f"Warning: Could not import property_scraper: {e}")
    fetch_all_properties = None

try:
    from models import Property
except ImportError as e:
    print(f"Warning: Could not import models: {e}")
    Property = None

try:
    from utils import fetch_gbp_exchange_rate
except ImportError as e:
    print(f"Warning: Could not import utils: {e}")
    fetch_gbp_exchange_rate = None

app = Flask(__name__)
app.logger.setLevel(logging.INFO)

# Global variables
LISTINGS_FILE = "listings.json"
UNVERIFIED_LIMIT = 3
properties_data = []
blocked_sources = []
gbp_rate = 0.0
is_scraping = False

def property_to_dict(prop):
    """Convert Property object to dictionary with error handling"""
    try:
        if hasattr(prop, '__dict__'):
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
        else:
            return {
                "title": prop.get("title", ""),
                "location": prop.get("location", ""),
                "price": prop.get("price", 0),
                "agency": prop.get("agency", ""),
                "link": prop.get("link", ""),
                "date": str(prop.get("date", "")),
                "source": prop.get("source", "unknown"),
                "sold": prop.get("sold", False),
                "status": prop.get("status", "active"),
                "missing_count": prop.get("missing_count", 0)
            }
    except Exception as e:
        app.logger.error(f"Error converting property to dict: {e}")
        return {
            "title": "",
            "location": "",
            "price": 0,
            "agency": "",
            "link": "",
            "date": "",
            "source": "unknown",
            "sold": False,
            "status": "active",
            "missing_count": 0
        }

def dict_to_property(d):
    """Convert dictionary to Property object with error handling"""
    if Property is None:
        return d
        
    date_val = d.get("date", "")
    if isinstance(date_val, str) and date_val:
        try:
            date_val = datetime.fromisoformat(date_val).date()
        except Exception:
            date_val = date_val
    
    try:
        p = Property(
            title=d.get("title", ""),
            price=d["price"],
            location=d["location"],
            agency=d["agency"],
            link=d["link"],
            date=date_val
        )
        p.source = d.get("source", "unknown")
        p.sold = d.get("sold", False)
        p.status = d.get("status", "active")
        p.missing_count = d.get("missing_count", 0)
        return p
    except Exception as e:
        app.logger.error(f"Error creating Property object: {e}")
        return d

def load_previous_properties():
    """Load properties from JSON file"""
    if not os.path.exists(LISTINGS_FILE):
        return []
    try:
        with open(LISTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [dict_to_property(d) for d in data]
    except Exception as e:
        app.logger.error(f"Error loading previous properties: {e}")
        return []

def save_properties(properties):
    """Save properties to JSON file"""
    try:
        with open(LISTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump([property_to_dict(p) for p in properties], f, indent=2)
    except Exception as e:
        app.logger.error(f"Error saving properties: {e}")

def merge_properties(new_props, old_props, successful_sources):
    """Merge new and old properties with status tracking - EXACT Android logic"""
    new_by_source = {}
    for p in new_props:
        new_by_source.setdefault(p.source, {})[p.link] = p

    old_by_source = {}
    for p in old_props:
        old_by_source.setdefault(getattr(p, "source", "unknown"), {})[p.link] = p

    merged = []

    for source in successful_sources:
        new_links = set(new_by_source.get(source, {}))
        old_links = set(old_by_source.get(source, {}))

        # Listings found in new scrape: reset status
        for link, p in new_by_source.get(source, {}).items():
            p.sold = False
            p.status = "active"
            p.missing_count = 0
            merged.append(p)

        # Listings missing from new scrape: increment missing_count
        for link in old_links - new_links:
            old = old_by_source[source][link]
            old.missing_count = getattr(old, "missing_count", 0) + 1
            if old.missing_count >= UNVERIFIED_LIMIT:
                old.sold = True
                old.status = "sold"
            else:
                old.sold = False
                old.status = "unverified"
            merged.append(old)

    # Listings from sources not scraped this time: keep as is
    for source in old_by_source:
        if source not in successful_sources:
            for link, p in old_by_source[source].items():
                if not any((x.link == p.link and x.source == p.source) for x in merged):
                    merged.append(p)

    return merged

def refresh_exchange_rate():
    """Fetch current GBP exchange rate"""
    global gbp_rate
    if fetch_gbp_exchange_rate is None:
        gbp_rate = 0.0
        return
        
    try:
        rate = fetch_gbp_exchange_rate()
        if rate:
            gbp_rate = rate
        else:
            gbp_rate = 0.0
    except Exception as e:
        app.logger.error(f"Failed to fetch exchange rate: {e}")
        gbp_rate = 0.0

def scrape_and_update():
    """Scrape properties and update data - EXACT Android logic"""
    global properties_data, blocked_sources, is_scraping
    
    if fetch_all_properties is None:
        app.logger.warning("Scraping functionality not available")
        return
    
    is_scraping = True
    old_props = properties_data.copy()
    
    try:
        new_props, successful_sources = fetch_all_properties()
    except Exception as e:
        app.logger.error(f"Scraping failed: {e}")
        blocked_sources = []
        is_scraping = False
        return

    all_sources = {"property24", "privateproperty", "pamgolding", "sahometraders"}
    blocked_sources = list(all_sources - set(successful_sources))
    
    properties_data = merge_properties(new_props, old_props, successful_sources)
    save_properties(properties_data)
    is_scraping = False

def sort_properties(properties, sort_option):
    """Sort properties based on option - EXACT Android logic"""
    if sort_option in ("No Sort", "", None):
        return properties
    elif sort_option == "Price High to Low":
        return sorted(properties, key=lambda x: x.price if hasattr(x, 'price') else x.get('price', 0), reverse=True)
    elif sort_option == "Price Low to High":
        return sorted(properties, key=lambda x: x.price if hasattr(x, 'price') else x.get('price', 0))
    elif sort_option == "A-Z":
        return sorted(properties, key=lambda x: (x.location if hasattr(x, 'location') else x.get('location', '')).lower())
    elif sort_option == "Z-A":
        return sorted(properties, key=lambda x: (x.location if hasattr(x, 'location') else x.get('location', '')).lower(), reverse=True)
    return properties

def filter_properties(properties, status_filter="active", min_price=10000, max_price=8000000):
    """Filter properties by status and price range - EXACT Android logic"""
    filtered = []
    
    for prop in properties:
        prop_dict = property_to_dict(prop) if hasattr(prop, '__dict__') else prop
        
        # Status filtering
        if status_filter == "active":
            if prop_dict.get("sold", False) or prop_dict.get("status", "active") != "active":
                continue
        elif status_filter == "sold":
            if not prop_dict.get("sold", False) or prop_dict.get("status", "active") != "sold":
                continue
        elif status_filter == "unverified":
            if prop_dict.get("sold", False) or prop_dict.get("status", "active") != "unverified":
                continue
        
        # Price filtering
        prop_price = prop_dict.get("price", 0)
        if min_price <= prop_price <= max_price:
            filtered.append(prop)
    
    return filtered

def get_property_stats():
    """Get property statistics - EXACT Android logic"""
    stats = {"active": 0, "sold": 0, "unverified": 0, "total": 0}
    
    for prop in properties_data:
        prop_dict = property_to_dict(prop) if hasattr(prop, '__dict__') else prop
        
        if prop_dict.get("sold", False) or prop_dict.get("status", "active") == "sold":
            stats["sold"] += 1
        elif prop_dict.get("status", "active") == "unverified":
            stats["unverified"] += 1
        else:
            stats["active"] += 1
        
        stats["total"] += 1
    
    return stats

# Routes
@app.route('/')
def index():
    """Main page with complete UI"""
    return render_template('index.html')

@app.route('/api/properties')
def api_properties():
    """Get properties with filtering and sorting"""
    try:
        status_filter = request.args.get('status', 'active')
        sort_option = request.args.get('sort', 'No Sort')
        min_price = int(request.args.get('min_price', 10000))
        max_price = int(request.args.get('max_price', 8000000))
        
        # Filter properties
        filtered_props = filter_properties(properties_data, status_filter, min_price, max_price)
        
        # Sort properties
        sorted_props = sort_properties(filtered_props, sort_option)
        
        # Convert to dictionaries and add GBP prices
        result = []
        for prop in sorted_props:
            prop_dict = property_to_dict(prop) if hasattr(prop, '__dict__') else prop
            
            # Add GBP price calculation
            try:
                zar_price = prop_dict.get("price", 0)
                gbp_price = zar_price * gbp_rate if gbp_rate else 0
                prop_dict["gbp_price"] = f"£{gbp_price:,.2f}"
                prop_dict["zar_price_formatted"] = f"R{zar_price:,}"
            except Exception:
                prop_dict["gbp_price"] = "£0.00"
                prop_dict["zar_price_formatted"] = f"R{prop_dict.get('price', 0):,}"
            
            result.append(prop_dict)
        
        return jsonify({
            "success": True,
            "properties": result,
            "count": len(result)
        })
        
    except Exception as e:
        app.logger.error(f"Error in api_properties: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "properties": [],
            "count": 0
        }), 500

@app.route('/api/stats')
def api_stats():
    """Get property statistics"""
    try:
        stats = get_property_stats()
        return jsonify({
            "success": True,
            "stats": stats,
            "blocked_sources": blocked_sources,
            "gbp_rate": gbp_rate,
            "is_scraping": is_scraping
        })
    except Exception as e:
        app.logger.error(f"Error in api_stats: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "stats": {"active": 0, "sold": 0, "unverified": 0, "total": 0},
            "blocked_sources": [],
            "gbp_rate": 0.0,
            "is_scraping": False
        }), 500

@app.route('/api/refresh', methods=['POST'])
def api_refresh():
    """Trigger property scraping"""
    global is_scraping
    
    if is_scraping:
        return jsonify({
            "success": False,
            "message": "Scraping already in progress"
        })
    
    def background_scrape():
        scrape_and_update()
    
    threading.Thread(target=background_scrape, daemon=True).start()
    
    return jsonify({
        "success": True,
        "message": "Scraping started"
    })

@app.route('/api/exchange-rate', methods=['POST'])
def api_exchange_rate():
    """Refresh exchange rate"""
    refresh_exchange_rate()
    return jsonify({
        "success": True,
        "gbp_rate": gbp_rate
    })

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Initialize data on startup
def initialize_app():
    """Initialize application data"""
    global properties_data
    properties_data = load_previous_properties()
    refresh_exchange_rate()
    app.logger.info(f"Loaded {len(properties_data)} properties")

if __name__ == '__main__':
    initialize_app()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
