import sqlite3
import hashlib

DB_FILENAME = "database.db"


def init_db():
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            desc TEXT,
            img TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            payment_info TEXT,
            items TEXT NOT NULL,
            total REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    # Insert initial data
    products = [
        (
            1,
            "Smartphone",
            299.99,
            "Latest model smartphone",
            "/static/images/latest-model-smartphone.webp",
        ),
        (
            2,
            "Laptop",
            799.99,
            "Lightweight laptop",
            "/static/images/lightweight-laptop.jpg",
        ),
        (
            3,
            "Headphones",
            49.99,
            "Noise-cancelling headphones",
            "/static/images/noise-cancelling-headphones.jpg",
        ),
        (
            4,
            "Charger",
            19.99,
            "Fast USB charger",
            "/static/images/fast-usb-charger.png",
        ),
    ]
    c.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?)", products)
    conn.commit()
    conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(username, password):
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, hash_password(password)),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def authenticate_user(username, password):
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row and row[0] == hash_password(password):
        return True
    return False


def get_user_id(username):
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return row[0]
    return None


def get_user_info(username):
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    c.execute("SELECT id, username FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "username": row[1]}
    return None


def get_all_products():
    with sqlite3.connect(DB_FILENAME) as conn:
        c = conn.cursor()
        c.execute("SELECT id, name, price, desc, img FROM products")
        products = [
            {
                "id": row[0],
                "name": row[1],
                "price": row[2],
                "desc": row[3],
                "img": row[4],
            }
            for row in c.fetchall()
        ]
    return products


def get_product_by_id(pid):
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    c.execute("SELECT id, name, price, desc, img FROM products WHERE id=?", (pid,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0],
            "name": row[1],
            "price": row[2],
            "desc": row[3],
            "img": row[4],
        }
    return None


def save_order(name, address, payment_method, payment_info, items, total, user_id=None):
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO orders (user_id, name, address, payment_method, payment_info, items, total)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (user_id, name, address, payment_method, payment_info, items, total),
    )
    conn.commit()
    conn.close()
