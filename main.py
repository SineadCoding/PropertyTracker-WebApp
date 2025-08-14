import json
import os
import threading
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.clock import Clock
from kivy.core.window import Window
from property_scraper import fetch_all_properties
from models import Property
from utils import fetch_gbp_exchange_rate

LISTINGS_FILE = "listings.json"
UNVERIFIED_LIMIT = 3  # Number of scrapes before marking as sold

def property_to_dict(prop):
    return {
        "title": getattr(prop, "title", ""),
        "location": prop.location,
        "price": prop.price,
        "agency": prop.agency,
        "link": prop.link,
        "date": str(getattr(prop, "date", "")),  # Save as string for JSON
        "source": getattr(prop, "source", "unknown"),
        "sold": getattr(prop, "sold", False),
        "status": getattr(prop, "status", "active"),
        "missing_count": getattr(prop, "missing_count", 0)
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

class PropertyListScreen(Screen):
    sort_option = StringProperty("")  # Empty by default for placeholder
    filter_min_price = NumericProperty(10000)
    filter_max_price = NumericProperty(8000000)
    filter_section_open = BooleanProperty(False)
    is_loading = BooleanProperty(False)

    def on_pre_enter(self):
        self.refresh_list()

    def show_loading(self):
        self.is_loading = True

    def hide_loading(self):
        self.is_loading = False

    def refresh_list(self):
        if 'property_list' in self.ids and self.ids.property_list:
            self.ids.property_list.clear_widgets()
        else:
            print("Error: 'property_list' widget not found in KV file.")
            return
        app = App.get_running_app()
        properties = [
            p for p in app.properties
            if not getattr(p, "sold", False)
            and getattr(p, "status", "active") == "active"
            and self.filter_min_price <= p.price <= self.filter_max_price
        ]
        properties = self.sort_properties(properties)
        if not properties:
            print("No properties found")
        for prop in properties:
            card = PropertyCard(
                location=prop.location,
                price=f"R{prop.price:,}",
                agency=prop.agency,
                link=prop.link,
                source=getattr(prop, "source", "")
            )
            self.ids.property_list.add_widget(card)
        self.populated = True

    def sort_properties(self, properties):
        if self.sort_option in ("No Sort", "", None):
            return properties
        elif self.sort_option == "Price High to Low":
            return sorted(properties, key=lambda x: x.price, reverse=True)
        elif self.sort_option == "Price Low to High":
            return sorted(properties, key=lambda x: x.price)
        elif self.sort_option == "A-Z":
            return sorted(properties, key=lambda x: x.location.lower())
        elif self.sort_option == "Z-A":
            return sorted(properties, key=lambda x: x.location.lower(), reverse=True)
        return properties

    def on_refresh(self):
        self.show_loading()
        def background_refresh():
            app = App.get_running_app()
            app.scrape_and_update()
            Clock.schedule_once(lambda dt: self.finish_refresh(), 0)
        threading.Thread(target=background_refresh, daemon=True).start()

    def finish_refresh(self):
        self.refresh_list()
        # app = App.get_running_app()
        # if hasattr(app.root, "get_screen") and app.root.has_screen('sold'):
        #     app.root.get_screen('sold').refresh_list()
        self.hide_loading()

    def on_sort_option(self, instance, value):
        self.sort_option = value
        self.refresh_list()

    def on_min_slider_value(self, value):
        self.filter_min_price = min(int(value), self.filter_max_price)

    def on_max_slider_value(self, value):
        self.filter_max_price = max(int(value), self.filter_min_price)

    def apply_filter(self):
        self.refresh_list()
        self.filter_section_open = False

    def toggle_filter_section(self):
        self.filter_section_open = not self.filter_section_open

    def undo_filters(self):
        self.filter_min_price = 10000
        self.filter_max_price = 8000000
        self.apply_filter()

# class SoldScreen(Screen): 
#     ... (entire SoldScreen class commented out) ...

class PropertyCard(BoxLayout):
    location = StringProperty("")
    price = StringProperty("")
    agency = StringProperty("")
    link = StringProperty("")
    source = StringProperty("")
    gbp_price = StringProperty()

    def open_url(self, url):
        import webbrowser
        webbrowser.open(url)

    def on_price(self, instance, value):
        # Update GBP price when ZAR price changes
        app = App.get_running_app()
        try:
            zar_value = float(value.replace("R", "").replace(",", ""))
            gbp_value = zar_value * app.gbp_rate if app.gbp_rate else 0
            self.gbp_price = f"£{gbp_value:,.2f}"
        except Exception:
            self.gbp_price = "£0.00"

class PropertyApp(App):
    blocked_sources = []
    gbp_rate = 0.0

    def build(self):
        # Responsive window size for desktop/mobile
        from kivy.utils import platform
        if platform == "win" or platform == "linux" or platform == "macosx":
            Window.size = (400, 700)
        # On mobile, Window.size is managed by the OS/app
        self.properties = load_previous_properties()
        self.blocked_sources = []
        return Builder.load_file("property_app.kv")

    def scrape_and_update(self):
        old_props = self.properties
        try:
            new_props, successful_sources = fetch_all_properties()
        except Exception as e:
            print(f"Scraping failed: {e}")
            self.blocked_sources = []
            return

        all_sources = {"property24", "privateproperty", "pamgolding", "sahometraders"}
        self.blocked_sources = list(all_sources - set(successful_sources))

        self.properties = merge_properties(new_props, old_props, successful_sources)
        save_properties(self.properties)

    def on_start(self):
        self.refresh_exchange_rate()
        self.root.get_screen('property_list').refresh_list()
        # if hasattr(self.root, "get_screen") and self.root.has_screen('sold'):
        #     self.root.get_screen('sold').refresh_list()

    def refresh_exchange_rate(self):
        rate = fetch_gbp_exchange_rate()
        if rate:
            self.gbp_rate = rate
        else:
            self.gbp_rate = 0.0

    def open_url(self, url):
        import webbrowser
        webbrowser.open(url)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
