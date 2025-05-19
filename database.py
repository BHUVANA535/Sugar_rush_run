import sqlite3

# Connect to database (or create it)
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Create table if it doesn't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    high_score INTEGER DEFAULT 0
)
""")
conn.commit()

def register_user(username, password):
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Username already exists

def login_user(username, password):
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    return cursor.fetchone() is not None

def update_high_score(username, score):
    cursor.execute("SELECT high_score FROM users WHERE username=?", (username,))
    result = cursor.fetchone()
    if result and score > result[0]:
        cursor.execute("UPDATE users SET high_score=? WHERE username=?", (score, username))
        conn.commit()

def get_high_score(username):
    cursor.execute("SELECT high_score FROM users WHERE username=?", (username,))
    result = cursor.fetchone()
    return result[0] if result else 0

def get_top_players(limit=5):
    cursor.execute("SELECT username, high_score FROM users ORDER BY high_score DESC LIMIT ?", (limit,))
    return cursor.fetchall()