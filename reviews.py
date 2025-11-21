import db

def get_all_reviews():  # Fetching all reviews with author, comment stats, and average rating
    sql = """
        SELECT r.id,
               r.movie_title,
               substr(r.content, 1, 200) AS content_preview,
               r.created_at,
               u.username,
               u.id AS user_id,
               COUNT(c.id) AS comment_count,
               ROUND(AVG(c.rating), 1) AS avg_rating
        FROM reviews r
        JOIN users u ON u.id = r.user_id
        LEFT JOIN comments c ON c.review_id = r.id
        GROUP BY r.id
        ORDER BY r.id DESC
    """
    return db.query(sql)

def add_review(movie_title, content, user_id, category_ids):    # Adding a new review and linking it to category ids
    sql = """
        INSERT INTO reviews (movie_title, content, created_at, user_id)
        VALUES (?, ?, datetime('now'), ?)
    """
    review_id = db.insert(sql, [movie_title, content, user_id])
    
    for category_id in category_ids:
        if category_id:
            sql_link = """
                INSERT INTO review_categories (review_id, category_id)
                VALUES (?, ?)
            """
            db.execute(sql_link, [review_id, category_id])
            
    return review_id

def get_review(review_id):  # Returning a single review by ID with author, comment stats, and average rating 
    sql = """
        SELECT r.id,
               r.movie_title,
               r.content,
               r.created_at,
               r.user_id,
               u.username,
               COUNT(c.id) AS comment_count,
               ROUND(AVG(c.rating), 1) AS avg_rating
        FROM reviews r
        JOIN users u ON u.id = r.user_id
        LEFT JOIN comments c ON c.review_id = r.id
        WHERE r.id = ?
    """
    result = db.query(sql, [review_id])
    return result[0] if result else None

def get_review_categories(review_id):   # Returning all categories linked to a review
    sql = """
        SELECT c.id, c.name
        FROM categories c, review_categories rc
        WHERE rc.review_id = ? AND rc.category_id = c.id
        ORDER BY c.name
    """
    return db.query(sql, [review_id])

def update_review(review_id, movie_title, content, category_ids):   # Updating a review and its linked categories
    sql = "UPDATE reviews SET movie_title = ?, content = ? WHERE id = ?"
    db.execute(sql, [movie_title, content, review_id])
    
    # Removing old categories
    sql_delete = "DELETE FROM review_categories WHERE review_id = ?"
    db.execute(sql_delete, [review_id])
    
    # Re-inserting categories
    for category_id in category_ids:
        if category_id:
            sql_link = """
                INSERT INTO review_categories (review_id, category_id)
                VALUES (?, ?)
            """
            db.execute(sql_link, [review_id, category_id])
            
def delete_review(review_id):   # Deleting a review and its associated comments and category links
    db.execute("DELETE FROM comments WHERE review_id = ?", [review_id])
    db.execute("DELETE FROM review_categories WHERE review_id = ?", [review_id])
    db.execute("DELETE FROM reviews WHERE id = ?", [review_id])
    
def get_comments(review_id):    # Returning all comments for a given review
    sql = """
        SELECT c.id,
               c.content,
               c.rating,
               c.created_at,
               c.user_id,
               u.username
        FROM comments c, users u
        WHERE c.user_id = u.id AND c.review_id = ?
        ORDER BY c.created_at
    """
    return db.query(sql, [review_id])

def add_comment(content, rating, user_id, review_id):   # Adding a new comment to a review
    sql = """
        INSERT INTO comments (content, rating, created_at, user_id, review_id)
        VALUES (?, ?, datetime('now'), ?, ?)
    """
    db.execute(sql, [content, rating, user_id, review_id])
    
def get_comment(comment_id):    # Returning a single comment by id
    sql = """
        SELECT id, content, rating, user_id, review_id
        FROM comments
        WHERE id = ?
    """
    result = db.query(sql, [comment_id])
    return result[0] if result else None

def update_comment(comment_id, content, rating):    # Updating the content and rating of a comment
    sql = "UPDATE comments SET content = ?, rating = ? WHERE id = ?"
    db.execute(sql, [content, rating, comment_id])
    
def delete_comment(comment_id): # Deleting a comment by id
    sql = "DELETE FROM comments WHERE id = ?"
    db.execute(sql, [comment_id])
    
def search_reviews(query):  # Searching reviews by movie title or content
    sql = """
        SELECT r.id,
               r.movie_title,
               substr(r.content, 1, 200) AS content_preview,
               r.created_at,
               u.username,
               u.id AS user_id
        FROM reviews r, users u
        WHERE r.user_id = u.id
        AND (r.movie_title LIKE ? OR r.content LIKE ?)
        ORDER BY r.created_at DESC
    """
    like = "%" + query + "%"
    return db.query(sql, [like, like])

def get_categories():   # Returning all categories
    sql = "SELECT id, name FROM categories ORDER BY name"
    return db.query(sql)