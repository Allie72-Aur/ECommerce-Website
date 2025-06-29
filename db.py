import sqlite3

def init_db():
    conn = sqlite3.connect('products.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            desc TEXT,
            img TEXT
        )
    ''')
    # Insert initial data if table is empty
    c.execute('SELECT COUNT(*) FROM products')
    if c.fetchone()[0] == 0:
        products = [
            (1, 'Smartphone', 299.99, 'Latest model smartphone', 'https://via.placeholder.com/150'),
            (2, 'Laptop', 799.99, 'Lightweight laptop', 'https://via.placeholder.com/150'),
            (3, 'Headphones', 49.99, 'Noise-cancelling headphones', 'https://via.placeholder.com/150'),
            (4, 'Charger', 19.99, 'Fast USB charger', 'https://via.placeholder.com/150'),
        ]
        c.executemany('INSERT INTO products VALUES (?, ?, ?, ?, ?)', products)
    conn.commit()
    conn.close()

def get_all_products():
    conn = sqlite3.connect('products.db')
    c = conn.cursor()
    c.execute('SELECT id, name, price, desc, img FROM products')
    products = [
        {'id': row[0], 'name': row[1], 'price': row[2], 'desc': row[3], 'img': row[4]}
        for row in c.fetchall()
    ]
    conn.close()
    return products

def get_product_by_id(pid):
    conn = sqlite3.connect('products.db')
    c = conn.cursor()
    c.execute('SELECT id, name, price, desc, img FROM products WHERE id=?', (pid,))
    row = c.fetchone()
    conn.close()
    if row:
        return {'id': row[0], 'name': row[1], 'price': row[2], 'desc': row[3], 'img': row[4]}
    return None
