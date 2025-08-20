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

# Import Property always, handle PropertyScraper separately
try:
    from property_scraper import PropertyScraper
except ImportError as e:
    logger.error(f"Import error: {e}")
    PropertyScraper = None
try:
    from models import Property
except ImportError as e:
    logger.error(f"Import error: {e}")
    # Fallback Property class
    class Property:
        def __init__(self, title='', price='', location='', agency='', link='', date='', **kwargs):
            self.title = title
            self.price = price
            self.location = location
            self.agency = agency
            self.link = link
            self.date = date
            for k, v in kwargs.items():
                setattr(self, k, v)
try:
    from utils import get_exchange_rate, format_price_gbp
except ImportError as e:
    logger.error(f"Import error: {e}")

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
        
        # Initialize scraper if available
        try:
            self.scraper = PropertyScraper()
        except:
            logger.warning("PropertyScraper not available, using fallback")
            
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
                    self.previous_properties = []
                    self.properties = []
                    for prop_data in data:
                        prop = Property()
                        for key, value in prop_data.items():
                            setattr(prop, key, value)
                        self.previous_properties.append(prop)
                        self.properties.append(prop)
                logger.info(f"Loaded {len(self.properties)} properties from listings.json")
        except Exception as e:
            logger.error(f"Error loading previous properties: {e}")
            self.previous_properties = []
            self.properties = []
    
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
            if hasattr(self, 'get_exchange_rate'):
                self.exchange_rate = get_exchange_rate()
            else:
                # Fallback exchange rate
                response = requests.get('https://api.exchangerate-api.com/v4/latest/EUR', timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    self.exchange_rate = data['rates'].get('GBP', 0.85)
                else:
                    self.exchange_rate = 0.85  # Fallback rate
            logger.info(f"Updated exchange rate: 1 EUR = {self.exchange_rate:.4f} GBP")
        except Exception as e:
            logger.error(f"Error updating exchange rate: {e}")
            self.exchange_rate = 0.85  # Default fallback
    
    def scrape_properties(self):
        """Scrape properties using the property scraper"""
        try:
            if self.scraper:
                new_properties = self.scraper.scrape_all_sources()
                # Filter out blocked sources
                filtered_properties = [
                    prop for prop in new_properties 
                    if prop.source not in self.blocked_sources
                ]
                
                # Merge with previous properties
                self.properties = self.merge_properties(filtered_properties, self.previous_properties)
                
                # Save properties
                self.save_properties()
                
                logger.info(f"Scraped {len(new_properties)} properties, {len(filtered_properties)} after filtering")
                return len(filtered_properties)
            else:
                # Load from existing file if scraper not available
                self.properties = self.previous_properties[:]
                return len(self.properties)
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
        
    # Remove sold marking logic
    # Only keep active properties
        
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
        # Only show active properties
        filtered = [p for p in filtered if p.status == "active"]
        # Filter by price range (convert to EUR if needed)
        price_filtered = []
        for prop in filtered:
            try:
                price = float(prop.price) if prop.price else 0
                if prop.currency == "GBP":
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
            filtered.sort(key=lambda p: int(p.bedrooms or 0))
        elif self.current_sort == "bedrooms_desc":
            filtered.sort(key=lambda p: int(p.bedrooms or 0), reverse=True)
        elif self.current_sort == "area_asc":
            filtered.sort(key=lambda p: float(p.area or 0))
        elif self.current_sort == "area_desc":
            filtered.sort(key=lambda p: float(p.area or 0), reverse=True)
        elif self.current_sort == "date_asc":
            filtered.sort(key=lambda p: p.first_seen or "")
        elif self.current_sort == "date_desc":
            filtered.sort(key=lambda p: p.first_seen or "", reverse=True)
        return filtered
    
    def get_property_stats(self) -> Dict[str, int]:
        """Get property statistics"""
        stats = {
            "total": len([p for p in self.properties if p.status == "active"]),
            "active": len([p for p in self.properties if p.status == "active"])
        }
        return stats
    
    def property_to_dict(self, prop) -> Dict[str, Any]:
        """Convert property object to dictionary"""
        prop_dict = {
            'title': getattr(prop, 'title', getattr(prop, 'address', getattr(prop, 'location', ''))),
            'location': getattr(prop, 'location', getattr(prop, 'address', '')),
            'address': getattr(prop, 'address', getattr(prop, 'location', '')),
            'price': getattr(prop, 'price', ''),
            'agency': getattr(prop, 'agency', getattr(prop, 'source', '')),
            'link': getattr(prop, 'link', getattr(prop, 'url', '')),
            'date': getattr(prop, 'date', getattr(prop, 'first_seen', '')),
            'status': getattr(prop, 'status', 'active'),
        }
        # Add GBP price if currency is EUR
        currency = getattr(prop, 'currency', 'ZAR')
        if currency == 'EUR' and prop_dict['price']:
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
    return render_template('index.html')

@app.route('/api/properties')
def get_properties():
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
