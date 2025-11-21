# User-related database operations; registration, login checks, and statistics on reviews
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import db

def create_user(username, password1, password2):
    if password1 != password2:  # Password match check
        return "Error: passwords do not match"
    
    if not username:    # Non-empty username check
        return "Error: username is required"
    
    if not password1:   # Non-empty password check
        return "Error: password is required"
    
    password_hash = generate_password_hash(password1)   # Hashing password
    
    try:
        sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
        db.execute(sql, [username, password_hash])  # Saving new user
    except sqlite3.IntegrityError:
        return "Error: username is already taken"   # If username is not unique
    
    return None

def check_login(username, password):
    sql = "SELECT id, password_hash FROM users where username = ?"
    rows = db.query(sql, [username])
    if not rows:    # No user found
        return None
    
    user = rows[0]
    if check_password_hash(user["password_hash"], password):    # Password verification
        return user["id"]
    else:
        return None
    
def get_user(user_id):  # Fetching a single user by ID
    sql = "SELECT id, username FROM users WHERE id = ?"
    result = db.query(sql, [user_id])
    return result[0] if result else None

def get_user_reviews(user_id):  # Fetching all reviews by a specific user with comment stats
    sql = """
        SELECT r.id,
               r.movie_title,
               r.created_at,
               COUNT(c.id) AS comment_count,
               ROUND(AVG(c.rating), 1) AS avg_rating
        FROM reviews r
        LEFT JOIN comments c ON c.review_id = r.id
        WHERE r.user_id = ?
        GROUP BY r.id
        ORDER BY r.created_at DESC
"""
    return db.query(sql, [user_id])

def get_user_stats(user_id):    # Fetching statistics about user's reviews
    sql = """
        SELECT COUNT(*) AS count,
                MIN(created_at) AS first_review,
                MAX(created_at) AS last_review
        FROM reviews
        WHERE user_id = ?
    """
    result = db.query(sql, [user_id])
    return result[0] if result else None