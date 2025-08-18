# SQLite database setup for property listings
import sqlite3
from contextlib import closing

DB_PATH = 'listings.db'

def init_db():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
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

def save_properties_to_db(properties):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            conn.execute('DELETE FROM properties')
            for prop in properties:
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
