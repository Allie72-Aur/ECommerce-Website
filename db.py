"""
db.py - Database logic for ElectroShop Flask e-commerce app.
Handles database initialization, user authentication, product and order management.
"""

import sqlite3
import hashlib
import csv
import os

# Database filename and CSV file for initial product data
DB_FILENAME = "database.db"
PRODUCTS_CSV = "products.csv"


def init_db():
    """
    Initialize the SQLite database.
    - Drops and recreates the database (dev only)
    - Creates Products, Users, and Orders tables
    - Loads initial product data from products.csv
    """
    # If the database already exists, remove it for a fresh start (dev only)
    if os.path.exists(DB_FILENAME):
        os.remove(DB_FILENAME)  # Remove existing database file for fresh start
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    # Create Products table: stores all product info, including stock and image path
    c.execute("""
        CREATE TABLE Products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            desc TEXT,
            img TEXT,
            stock INTEGER NOT NULL DEFAULT 0
        )
    """)
    # Create Users table: stores user credentials (hashed passwords)
    c.execute("""
        CREATE TABLE Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    # Create Orders table: stores order details, links to user, stores items as JSON
    c.execute("""
        CREATE TABLE Orders (
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
    # Insert initial product data from CSV file
    if os.path.exists(PRODUCTS_CSV):
        with open(PRODUCTS_CSV, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            products = [
                (
                    int(row["id"]),
                    row["name"],
                    float(row["price"]),
                    row["desc"],
                    row["img"],
                    int(row["stock"]),
                )
                for row in reader
            ]
            # Bulk insert all products into the Products table
            c.executemany("INSERT INTO Products VALUES (?, ?, ?, ?, ?, ?)", products)
    conn.commit()
    conn.close()


def hash_password(password):
    """
    Hash the password using SHA-256 for secure storage.
    Returns the hex digest string.
    """
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(username, password):
    """
    Register a new user with a hashed password.
    Returns True if successful, False if username exists.
    """
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO Users (username, password_hash) VALUES (?, ?)",
            (username, hash_password(password)),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Username already exists
        return False
    finally:
        conn.close()


def authenticate_user(username, password):
    """
    Authenticate user by comparing hash of input password to stored hash.
    Returns True if credentials are valid, else False.
    """
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    c.execute("SELECT password_hash FROM Users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row and row[0] == hash_password(password):
        return True
    return False


def get_user_id(username):
    """
    Get user ID from username. Returns user id or None if not found.
    """
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    c.execute("SELECT id FROM Users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return row[0]
    return None


def get_user_info(username):
    """
    Get user info (id and username) as a dict. Returns None if not found.
    """
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    c.execute("SELECT id, username FROM Users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "username": row[1]}
    return None


def get_all_products():
    """
    Return all products as a list of dicts.
    """
    with sqlite3.connect(DB_FILENAME) as conn:
        c = conn.cursor()
        c.execute("SELECT id, name, price, desc, img, stock FROM Products")
        products = [
            {
                "id": row[0],
                "name": row[1],
                "price": row[2],
                "desc": row[3],
                "img": row[4],
                "stock": row[5],
            }
            for row in c.fetchall()
        ]
    return products


def get_product_by_id(pid):
    """
    Return a single product as a dict, or None if not found.
    """
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    c.execute(
        "SELECT id, name, price, desc, img, stock FROM Products WHERE id=?", (pid,)
    )
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0],
            "name": row[1],
            "price": row[2],
            "desc": row[3],
            "img": row[4],
            "stock": row[5],
        }
    return None


def save_order(name, address, payment_method, payment_info, items, total, user_id=None):
    """
    Save a new order to the Orders table. Items is a JSON string.
    """
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO Orders (user_id, name, address, payment_method, payment_info, items, total)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, name, address, payment_method, payment_info, items, total),
    )
    conn.commit()
    conn.close()


def update_stock(pid, qty):
    """
    Decrease the stock of a product by qty, only if enough stock is available.
    """
    with sqlite3.connect(DB_FILENAME) as conn:
        c = conn.cursor()
        c.execute(
            "UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?",
            (qty, pid, qty),
        )
        conn.commit()
