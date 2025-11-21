-- User table
CREATE TABLE users(
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);

-- Reviews table; main content (movie reviews)
CREATE TABLE reviews(
    id INTEGER PRIMARY KEY,
    movie_title TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES users
);

-- Categories table
CREATE TABLE categories(
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

-- Review-categories table; links reviews to one or more categories
CREATE TABLE review_categories(
    review_id INTEGER REFERENCES reviews,
    category_id INTEGER REFERENCES categories
);

-- Comments table
CREATE TABLE comments(
    id INTEGER PRIMARY KEY,
    content TEXT NOT NULL,
    rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES users,
    review_id INTEGER REFERENCES reviews
);

-- few example categories, subject to change
INSERT INTO categories (name) VALUES ('bad');
INSERT INTO categories (name) VALUES ('average');
INSERT INTO categories (name) VALUES ('great');