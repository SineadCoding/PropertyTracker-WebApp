#!/usr/bin/env python3
"""
PropertyTracker Web Application
Complete web version of the PropertyTracker Android app with all functionality
"""
from flask import Flask, render_template, jsonify, request
import json
import os
import requests
from datetime import datetime
import logging
from typing import List, Dict, Any, Optional
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


# Import models and scraping logic
from models import Property
from property_scraper import fetch_all_properties
from utils import fetch_gbp_exchange_rate

LISTINGS_FILE = "listings.json"
UNVERIFIED_LIMIT = 3

def property_to_dict(prop):
    # GBP conversion
    try:
        gbp_rate = fetch_gbp_exchange_rate() or 0.042
        price_gbp = float(getattr(prop, "price", 0)) * gbp_rate
    except Exception:
        price_gbp = ""
    return {
        "title": getattr(prop, "title", ""),
        "location": getattr(prop, "location", ""),
        "price": getattr(prop, "price", ""),
        "price_gbp": f"{price_gbp:,.0f}" if price_gbp else "",
        "agency": getattr(prop, "agency", ""),
        "url": getattr(prop, "link", ""),
        "status": getattr(prop, "status", "active"),
        "source": getattr(prop, "source", "unknown"),
        "sold": getattr(prop, "sold", False)
    }

def dict_to_property(d):
    from datetime import datetime
    date_val = d.get("date", "")
    if isinstance(date_val, str) and date_val:
        try:
            date_val = datetime.fromisoformat(date_val).date()
        except Exception:
            date_val = date_val
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

def load_previous_properties():
    if not os.path.exists(LISTINGS_FILE):
        return []
    with open(LISTINGS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [dict_to_property(d) for d in data]

def save_properties(properties):
    with open(LISTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump([property_to_dict(p) for p in properties], f, indent=2)

def merge_properties(new_props, old_props, successful_sources):
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

class WebPropertyTracker:
    """Main web application class that replicates Android app functionality"""
    
    def __init__(self):
        self.properties = []
        self.previous_properties = []
        self.blocked_sources = set()
        self.exchange_rate = 1.0
        self.current_filter = "all"
        self.current_sort = "price_desc"
        self.price_filter_min = 0
        self.price_filter_max = 1000000
        self.scraper = None
        
    # No PropertyScraper, use fetch_all_properties for scraping
            
        # Load initial data
        self.load_previous_properties()
        self.load_blocked_sources()
        self.update_exchange_rate()
    
    def load_previous_properties(self):
        """Load previously saved properties"""
        try:
            if os.path.exists('listings.json'):
                with open('listings.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.previous_properties = [dict_to_property(d) for d in data]
                logger.info(f"Loaded {len(self.previous_properties)} previous properties")
        except Exception as e:
            logger.error(f"Error loading previous properties: {e}")
            self.previous_properties = []
    
    def load_blocked_sources(self):
        """Load blocked sources"""
        try:
            if os.path.exists('blocked_sources.json'):
                with open('blocked_sources.json', 'r') as f:
                    self.blocked_sources = set(json.load(f))
        except Exception as e:
            logger.error(f"Error loading blocked sources: {e}")
            self.blocked_sources = set()
    
    def save_blocked_sources(self):
        """Save blocked sources"""
        try:
            with open('blocked_sources.json', 'w') as f:
                json.dump(list(self.blocked_sources), f)
        except Exception as e:
            logger.error(f"Error saving blocked sources: {e}")
    
    def update_exchange_rate(self):
        """Update EUR to GBP exchange rate"""
        try:
            self.exchange_rate = fetch_gbp_exchange_rate() or 0.042
            logger.info(f"Updated exchange rate: 1 ZAR = £{self.exchange_rate:.5f}")
        except Exception as e:
            logger.error(f"Error updating exchange rate: {e}")
            self.exchange_rate = 0.042  # Default fallback
    
    def scrape_properties(self):
        """Scrape properties using fetch_all_properties"""
        try:
            new_properties, successful_sources = fetch_all_properties()
            # Filter out blocked sources
            filtered_properties = [
                prop for prop in new_properties 
                if prop.source not in self.blocked_sources
            ]
            # Merge with previous properties
            self.properties = merge_properties(filtered_properties, self.previous_properties, successful_sources)
            # Save properties
            save_properties(self.properties)
            # Update blocked sources
            all_sources = {"property24", "privateproperty", "pamgolding", "sahometraders"}
            self.blocked_sources = list(all_sources - set(successful_sources))
            logger.info(f"Scraped {len(new_properties)} properties, {len(filtered_properties)} after filtering")
            return len(filtered_properties)
        except Exception as e:
            logger.error(f"Error scraping properties: {e}")
            self.properties = self.previous_properties[:]
            return 0
    
    def merge_properties(self, new_properties: List, previous_properties: List) -> List:
        """Merge new properties with previous ones, handling status updates"""
        merged = {}
        
        # Add previous properties
        for prop in previous_properties:
            key = f"{prop.address}_{prop.price}_{prop.source}"
            merged[key] = prop
        
        # Add/update with new properties
        for prop in new_properties:
            key = f"{prop.address}_{prop.price}_{prop.source}"
            if key in merged:
                # Update existing property
                merged[key].last_seen = datetime.now().isoformat()
                if merged[key].status == "unverified":
                    merged[key].status = "active"
            else:
                # New property
                prop.status = "active"
                prop.first_seen = datetime.now().isoformat()
                prop.last_seen = datetime.now().isoformat()
                merged[key] = prop
        
        # Mark properties as sold if not seen in new scrape
        new_keys = {f"{prop.address}_{prop.price}_{prop.source}" for prop in new_properties}
        for key, prop in merged.items():
            if key not in new_keys and prop.status == "active":
                prop.status = "sold"
        
        return list(merged.values())
    
    def save_properties(self):
        """Save properties to JSON file"""
        try:
            properties_data = []
            for prop in self.properties:
                prop_dict = {}
                for attr in ['address', 'price', 'currency', 'bedrooms', 'bathrooms', 
                           'area', 'source', 'url', 'image_url', 'description', 
                           'status', 'first_seen', 'last_seen']:
                    if hasattr(prop, attr):
                        prop_dict[attr] = getattr(prop, attr)
                properties_data.append(prop_dict)
            
            with open('listings.json', 'w', encoding='utf-8') as f:
                json.dump(properties_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(properties_data)} properties")
        except Exception as e:
            logger.error(f"Error saving properties: {e}")
    
    def get_filtered_properties(self) -> List:
        """Get properties filtered by current settings"""
        filtered = self.properties[:]
        # Filter by status
        if self.current_filter == "active":
            filtered = [p for p in filtered if p.status == "active"]
        elif self.current_filter == "sold":
            filtered = [p for p in filtered if p.status == "sold"]
        elif self.current_filter == "unverified":
            filtered = [p for p in filtered if p.status == "unverified"]
        # Filter by price range (convert to EUR if needed)
        price_filtered = []
        for prop in filtered:
            try:
                price = float(prop.price) if prop.price else 0
                if hasattr(prop, 'currency') and prop.currency == "GBP":
                    price = price / self.exchange_rate  # Convert GBP to EUR for comparison
                if self.price_filter_min <= price <= self.price_filter_max:
                    price_filtered.append(prop)
            except (ValueError, TypeError):
                price_filtered.append(prop)  # Include if price parsing fails
        filtered = price_filtered
        # Sort properties
        if self.current_sort == "price_asc":
            filtered.sort(key=lambda p: float(p.price or 0))
        elif self.current_sort == "price_desc":
            filtered.sort(key=lambda p: float(p.price or 0), reverse=True)
        elif self.current_sort == "bedrooms_asc":
            filtered.sort(key=lambda p: int(getattr(p, 'bedrooms', 0)))
        elif self.current_sort == "bedrooms_desc":
            filtered.sort(key=lambda p: int(getattr(p, 'bedrooms', 0)), reverse=True)
        elif self.current_sort == "area_asc":
            filtered.sort(key=lambda p: float(getattr(p, 'area', 0)))
        elif self.current_sort == "area_desc":
            filtered.sort(key=lambda p: float(getattr(p, 'area', 0)), reverse=True)
        elif self.current_sort == "date_asc":
            filtered.sort(key=lambda p: getattr(p, 'first_seen', ""))
        elif self.current_sort == "date_desc":
            filtered.sort(key=lambda p: getattr(p, 'first_seen', ""), reverse=True)
        return filtered
    
    def get_property_stats(self) -> Dict[str, int]:
        """Get property statistics"""
        stats = {
            "total": len(self.properties),
            "active": len([p for p in self.properties if p.status == "active"]),
            "sold": len([p for p in self.properties if p.status == "sold"]),
            "unverified": len([p for p in self.properties if p.status == "unverified"])
        }
        return stats
    
    def property_to_dict(self, prop) -> Dict[str, Any]:
        """Convert property object to dictionary"""
        prop_dict = {
            'address': getattr(prop, 'address', ''),
            'price': getattr(prop, 'price', ''),
            'currency': getattr(prop, 'currency', 'EUR'),
            'bedrooms': getattr(prop, 'bedrooms', ''),
            'bathrooms': getattr(prop, 'bathrooms', ''),
            'area': getattr(prop, 'area', ''),
            'source': getattr(prop, 'source', ''),
            'url': getattr(prop, 'url', ''),
            'image_url': getattr(prop, 'image_url', ''),
            'description': getattr(prop, 'description', ''),
            'status': getattr(prop, 'status', 'active'),
            'first_seen': getattr(prop, 'first_seen', ''),
            'last_seen': getattr(prop, 'last_seen', '')
        }
        
        # Add GBP price if currency is EUR
        if prop_dict['currency'] == 'EUR' and prop_dict['price']:
            try:
                eur_price = float(prop_dict['price'])
                gbp_price = eur_price * self.exchange_rate
                prop_dict['price_gbp'] = f"{gbp_price:,.0f}"
            except (ValueError, TypeError):
                prop_dict['price_gbp'] = ''
        else:
            prop_dict['price_gbp'] = prop_dict['price']
        
        return prop_dict

# Initialize the tracker
tracker = WebPropertyTracker()

# Flask routes
@app.route('/')
def index():
    """Main page"""
    # Just render the template, JS will fetch properties
    return render_template('index.html')
                    # Only run the app, do not scrape on startup
    """Get filtered properties"""
    try:
        # Update filters from request
        tracker.current_filter = request.args.get('filter', 'all')
        tracker.current_sort = request.args.get('sort', 'price_desc')
        
        try:
            tracker.price_filter_min = float(request.args.get('min_price', 0))
            tracker.price_filter_max = float(request.args.get('max_price', 1000000))
        except (ValueError, TypeError):
            tracker.price_filter_min = 0
            tracker.price_filter_max = 1000000
        
        # Get filtered properties
        properties = tracker.get_filtered_properties()
        properties_dict = [tracker.property_to_dict(prop) for prop in properties]
        
        return jsonify({
            'success': True,
            'properties': properties_dict,
            'count': len(properties_dict)
        })
    except Exception as e:
        logger.error(f"Error getting properties: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'properties': [],
            'count': 0
        })

@app.route('/api/stats')
def get_stats():
    """Get property statistics"""
    try:
        stats = tracker.get_property_stats()
        return jsonify({
            'success': True,
            'stats': stats,
            'exchange_rate': tracker.exchange_rate
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'stats': {'total': 0, 'active': 0, 'sold': 0, 'unverified': 0},
            'exchange_rate': 0.85
        })

@app.route('/api/scrape', methods=['POST'])
def scrape_properties():
    """Trigger property scraping"""
    try:
        count = tracker.scrape_properties()
        return jsonify({
            'success': True,
            'message': f'Scraped {count} properties',
            'count': count
        })
    except Exception as e:
        logger.error(f"Error scraping properties: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'count': 0
        })

@app.route('/api/refresh', methods=['POST'])
def refresh_data():
    """Refresh exchange rate and reload data"""
    try:
        tracker.update_exchange_rate()
        tracker.load_previous_properties()
        return jsonify({
            'success': True,
            'message': 'Data refreshed successfully',
            'exchange_rate': tracker.exchange_rate
        })
    except Exception as e:
        logger.error(f"Error refreshing data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/block_source', methods=['POST'])
def block_source():
    """Block a property source"""
    try:
        data = request.get_json()
        source = data.get('source')
        if source:
            tracker.blocked_sources.add(source)
            tracker.save_blocked_sources()
            return jsonify({
                'success': True,
                'message': f'Blocked source: {source}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No source specified'
            })
    except Exception as e:
        logger.error(f"Error blocking source: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/unblock_source', methods=['POST'])
def unblock_source():
    """Unblock a property source"""
    try:
        data = request.get_json()
        source = data.get('source')
        if source and source in tracker.blocked_sources:
            tracker.blocked_sources.remove(source)
            tracker.save_blocked_sources()
            return jsonify({
                'success': True,
                'message': f'Unblocked source: {source}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Source not found in blocked list'
            })
    except Exception as e:
        logger.error(f"Error unblocking source: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/blocked_sources')
def get_blocked_sources():
    """Get list of blocked sources"""
    try:
        return jsonify({
            'success': True,
            'blocked_sources': list(tracker.blocked_sources)
        })
    except Exception as e:
        logger.error(f"Error getting blocked sources: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'blocked_sources': []
        })

if __name__ == '__main__':
    # Load initial data
    tracker.scrape_properties()
    
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
