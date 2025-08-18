# SQLite database setup for property listings
import sqlite3
from contextlib import closing

import os
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'listings.db')

import os
DB_PATH = '/tmp/listings.db'

def init_db():
    try:
        with closing(sqlite3.connect(DB_PATH)) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS properties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    location TEXT,
                    price REAL,
                    agency TEXT,
                    link TEXT,
                    date TEXT,
                    source TEXT,
                    sold INTEGER,
                    status TEXT,
                    missing_count INTEGER
                )
            ''')
        print(f"[DB] Database initialized at {DB_PATH}")
    except Exception as e:
        print(f"[DB ERROR] Failed to initialize database: {e}")
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            conn.execute('DELETE FROM properties')

def save_property_to_db(prop):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            conn.execute('''
                INSERT INTO properties (title, location, price, agency, link, date, source, sold, status, missing_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                prop.get('title', ''),
                prop.get('location', ''),
                prop.get('price', 0),
                prop.get('agency', ''),
                prop.get('link', ''),
                prop.get('date', ''),
                prop.get('source', 'unknown'),
                int(prop.get('sold', False)),
                prop.get('status', 'active'),
                prop.get('missing_count', 0)
            ))

def load_properties_from_db():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute('SELECT * FROM properties')
        rows = cur.fetchall()
        return [dict(row) for row in rows]
