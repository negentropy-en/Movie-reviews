import secrets
from flask import Flask, redirect, render_template, request, session, abort, flash

import config
import users
import reviews
import db   # For teardown handler

app = Flask(__name__)
app.secret_key = config.secret_key

@app.teardown_appcontext    # Closing database connection after each request
def teardown_db(exception):
    db.close_db(exception)

@app.before_request
def before_request():
    ensure_csrf_token()
    
def ensure_csrf_token():    # Ensuring that CSRF token exists in session for all visitors
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)

def require_login():    # Not logged in
    if "user_id" not in session:
        abort(403)
        
def check_csrf():   # Checking CSRF token validity for POST requests
    form_token = request.form.get("csrf_token")
    if "csrf_token" not in session or not form_token:
        abort(403)
    if form_token != session["csrf_token"]:
        abort(403)

@app.route("/")
def index():    # Homepage showing all reviews
    all_reviews = reviews.get_all_reviews()
    categories = reviews.get_categories()
    return render_template("index.html", reviews=all_reviews, categories=categories)

@app.route("/register", methods=["GET"])
def register(): # Registration page
    return render_template("register.html", error=None, username="")

@app.route("/create_user", methods=["POST"])
def create_user():  # Handling user registration
    check_csrf()    # CSRF protection; same for all check_csrf below
    
    username = (request.form.get("username") or "").strip()
    password1 = request.form.get("password1") or ""
    password2 = request.form.get("password2") or ""
    
    if not username or not password1 or not password2:
        return render_template("register.html", error="All fields are required", username=username)
    
    error = users.create_user(username, password1, password2)
    if error:
        return render_template("register.html", error=error, username=username)
    
    flash("Account created successfully. Please log in.", "success")
    
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():  # Handling user login
    if request.method == "GET":
        return render_template("login.html", error=None, username="")
    
    check_csrf()
    
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    
    if not username or not password:
        return render_template("login.html", error="Please enter both username and password", username=username)
    
    user_id = users.check_login(username, password)
    if user_id is not None:
        session["user_id"] = user_id
        session["username"] = username
        session["csrf_token"] = secrets.token_hex(16)   # Refreshing CSRF token after login
        return redirect("/")
    else:
        return render_template("login.html", error="Error: wrong username or password", username=username)
    
@app.route("/logout", methods=["POST"])
def logout():   # Handling user logout
    check_csrf()
    session.clear()
    return redirect("/")

@app.route("/review/new", methods=["GET", "POST"])
def new_review():   # Creating a new review
    require_login()
    categories = reviews.get_categories()
    
    if request.method == "GET":
        return render_template("new_review.html", categories=categories, error=None, movie_title="", content="", selected_ids=[])
    
    check_csrf()
    
    movie_title = (request.form.get("movie_title") or "").strip()
    content = (request.form.get("content") or "").strip()
    user_id = session["user_id"]
    category_ids = request.form.getlist("category_ids") # Multiple selection for categories(bad, average, great, etc.)
    
    if not movie_title or not content:
        return render_template(
            "new_review.html",
            categories=categories,
            error="Title and content are required",
            movie_title=movie_title,
            content=content,
            selected_ids=category_ids
        )
    
    review_id = reviews.add_review(movie_title, content, user_id, category_ids)
    return redirect("/review/" + str(review_id))

@app.route("/review/<int:review_id>")
def show_review(review_id):  # Showing a single review with its comments
    review = reviews.get_review(review_id)
    if not review:
        abort(404)
        
    comments = reviews.get_comments(review_id)
    review_categories = reviews.get_review_categories(review_id)
    
    return render_template(
        "review.html",
        review=review,
        comments=comments,
        categories=review_categories,
        error=None,
        comment_text=""
    )
    
@app.route("/review/<int:review_id>/edit", methods=["GET", "POST"])
def edit_review(review_id):  # Editing an existing review
    require_login()
    review = reviews.get_review(review_id)
    if not review:
        abort(404)

    if review["user_id"] != session["user_id"]: # Only owner can edit
        abort(403)

    all_categories = reviews.get_categories()
    
    if request.method == "GET":
        selected_categories = reviews.get_review_categories(review_id)
        selected_ids = [str(c["id"]) for c in selected_categories]  # For pre-checked boxes
        return render_template(
            "edit_review.html",
            review=review,
            categories=all_categories,
            selected_ids=selected_ids,
            error=None
        )
    
    check_csrf()

    movie_title = (request.form.get("movie_title") or "").strip()
    content = (request.form.get("content") or "").strip()
    category_ids = request.form.getlist("categories")
    
    if not movie_title or not content:
        return render_template(
            "edit_review.html",
            review={"id": review_id, "movie_title": movie_title, "content": content},
            categories=all_categories,
            selected_ids=category_ids,
            error="Title and content can't be empty"
        )

    reviews.update_review(review_id, movie_title, content, category_ids)
    return redirect("/review/" + str(review_id))

@app.route("/review/<int:review_id>/delete", methods=["GET", "POST"])
def delete_review(review_id):   # Deleting a review
    require_login()
    review = reviews.get_review(review_id)
    if not review:
        abort(404)

    if review["user_id"] != session["user_id"]: # Only owner can delete
        abort(403)

    if request.method == "GET":
        return render_template("delete_review.html", review=review, error=None)

    check_csrf()

    if "confirm" in request.form:
        reviews.delete_review(review_id)
        return redirect("/")
    else:
        return render_template("delete_review.html", review=review, error="Please confirm deletion")


@app.route("/comment/new", methods=["POST"])
def new_comment():  # Creating a new comment to a review
    require_login()
    check_csrf()

    content = (request.form.get("content") or "").strip()
    review_id_raw = request.form.get("review_id") or "0"
    try:
        review_id = int(review_id_raw)
    except (TypeError, ValueError):
        review_id = 0
        
    try:
        rating = int(request.form.get("rating", ""))
    except (TypeError, ValueError):
        rating = 0
        
    error = None
    if not content:
        error = "Comment is required"
    elif rating < 1 or rating > 5:
        error = "Rating must be between 1 and 5"
        
    if error:
        review = reviews.get_review(review_id)
        if not review:
            abort(404)
        comments = reviews.get_comments(review_id)
        review_categories = reviews.get_review_categories(review_id)
        return render_template(
            "review.html",
            review=review,
            comments=comments,
            categories=review_categories,
            error=error,
            comment_text=content
        )
                
    user_id = session["user_id"]
    reviews.add_comment(content, rating, user_id, review_id)
    return redirect("/review/" + str(review_id))

@app.route("/comment/<int:comment_id>/edit", methods=["GET", "POST"])
def edit_comment(comment_id):   # Editing an existing comment
    require_login()
    comment = reviews.get_comment(comment_id)
    if not comment:
        abort(404)

    if comment["user_id"] != session["user_id"]:    # Only owner can edit
        abort(403)

    if request.method == "GET":
        return render_template("edit_comment.html", comment=comment, error=None)

    check_csrf()

    content = (request.form.get("content") or "").strip()
    try:
        rating = int(request.form.get("rating", ""))
    except (ValueError, TypeError):
        rating = 0
        
    if not content:
        return render_template("edit_comment.html", comment=comment, error="Comment is required")
    if rating < 1 or rating > 5:
        return render_template("edit_comment.html", comment=comment, error="Rating must be between 1 and 5")

    reviews.update_comment(comment_id, content, rating)
    return redirect("/review/" + str(comment["review_id"]))

@app.route("/comment/<int:comment_id>/delete", methods=["GET", "POST"])
def delete_comment(comment_id):  # Deleting a comment
    require_login()
    comment = reviews.get_comment(comment_id)
    if not comment:
        abort(404)

    if comment["user_id"] != session["user_id"]:    # Only owner can delete
        abort(403)

    if request.method == "GET":
        return render_template("delete_comment.html", comment=comment, error=None)

    check_csrf()

    review_id = comment["review_id"]
    if "confirm" in request.form:
        reviews.delete_comment(comment_id)
        return redirect("/review/" + str(review_id))
    else:
        return render_template("delete_comment.html", comment=comment, error="Please confirm deletion")

@app.route("/search")
def search():   # Searching reviews by query
    query = (request.args.get("query") or "").strip()
    results = reviews.search_reviews(query) if query else []
    return render_template("search.html", query=query, results=results)


@app.route("/user/<int:user_id>")
def show_user(user_id): # Showing user profile with their reviews and stats
    user = users.get_user(user_id)
    if not user:
        abort(404)

    stats = users.get_user_stats(user_id)
    user_reviews = users.get_user_reviews(user_id)

    return render_template(
        "user.html",
        user=user,
        stats=stats,
        reviews=user_reviews,
    )


if __name__ == "__main__":
    app.run(debug=True)
    
"""Static added for possible CSS styling in future if needed"""