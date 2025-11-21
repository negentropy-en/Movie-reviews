# Helper functions for database operations; flask.g to keep one connection per request (from course material)
import sqlite3
from flask import g

DATABASE = "database.db"    # Path to SQLite database file

def get_db():
    if "db" not in g:   # Creating connection only once per request
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db

def close_db(e=None):
    db = g.pop("db", None)  # Removing connection from g if it exists
    if db is not None:
        db.close()
        
def query(sql, params=None):
    if params is None:
        params = []
    db = get_db()
    result = db.execute(sql, params)
    rows = result.fetchall()
    return rows

def execute(sql, params=None):
    if params is None:
        params = []
    db = get_db()
    db.execute(sql, params)
    db.commit()
    
def insert(sql, params=None):
    if params is None:
        params = []
    db = get_db()
    cursor = db.execute(sql, params)
    db.commit()
    return cursor.lastrowid