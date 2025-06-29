from db import (
    init_db, register_user, authenticate_user, get_user_id, get_user_info,
    get_all_products, get_product_by_id, save_order
)
import os
import json
import re
from flask import Flask, render_template, redirect, url_for, request, session
from urllib.parse import urlparse, urljoin

app = Flask(__name__)
app.secret_key = "replace-with-a-secure-key"

# Initialize database if not exists
if not os.path.exists('database.db'):
    init_db()


def get_product(pid):
    return get_product_by_id(pid)


def sanitize_text(text):
    return re.sub(r'[^\w\s@.-]', '', text.strip())


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


@app.route("/")
def index():
    return render_template("index.html", products=get_all_products())


@app.route("/product/<int:pid>")
def product_detail(pid):
    product = get_product(pid)
    if not product:
        return redirect(url_for("index"))
    return render_template("product.html", product=product)


@app.route("/add_to_cart/<int:pid>")
def add_to_cart(pid):
    cart = session.get("cart", {})
    cart[str(pid)] = cart.get(str(pid), 0) + 1
    session["cart"] = cart
    return redirect(url_for("cart"))


@app.route("/cart")
def cart():
    cart = session.get("cart", {})
    items = []
    total = 0
    for pid, qty in cart.items():
        product = get_product(int(pid))
        if product:
            subtotal = product["price"] * qty
            items.append({"product": product, "qty": qty, "subtotal": subtotal})
            total += subtotal
    return render_template("cart.html", items=items, total=total)


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if 'user' not in session:
        return redirect(url_for('login', next=request.url))
    user_info = get_user_info(session['user'])
    name = user_info['username'] if user_info else ''
    address = ''
    if request.method == "POST":
        name = sanitize_text(request.form.get("name", name))
        address = sanitize_text(request.form.get("address", address))
        payment_method = sanitize_text(request.form.get("payment_method", ""))
        payment_info = ""
        errors = []
        # Validate required fields
        if not name:
            errors.append("Name is required.")
        if not address:
            errors.append("Address is required.")
        if payment_method not in ["credit_card", "paypal", "cod"]:
            errors.append("Invalid payment method.")
        # Payment info validation
        if payment_method == "credit_card":
            cc_number = sanitize_text(request.form.get("cc_number", ""))
            cc_expiry = sanitize_text(request.form.get("cc_expiry", ""))
            cc_cvc = sanitize_text(request.form.get("cc_cvc", ""))
            if not (cc_number and cc_expiry and cc_cvc):
                errors.append("All credit card fields are required.")
            payment_info = json.dumps({"cc_number": cc_number, "cc_expiry": cc_expiry, "cc_cvc": cc_cvc})
        elif payment_method == "paypal":
            paypal_email = sanitize_text(request.form.get("paypal_email", ""))
            if not paypal_email:
                errors.append("PayPal email is required.")
            payment_info = json.dumps({"paypal_email": paypal_email})
        # Prepare cart items
        cart = session.get("cart", {})
        items = []
        total = 0
        for pid, qty in cart.items():
            product = get_product(int(pid))
            if product:
                subtotal = product["price"] * qty
                items.append({"product": product, "qty": qty, "subtotal": subtotal})
                total += subtotal
        if not items:
            errors.append("Cart is empty.")
        if errors:
            return render_template("checkout.html", success=False, errors=errors, name=name, address=address)
        # Save order with user_id
        user_id = get_user_id(session['user'])
        save_order(name, address, payment_method, payment_info, json.dumps(items), total, user_id=user_id)
        session.pop("cart", None)
        return render_template("checkout.html", success=True)
    return render_template("checkout.html", success=False, errors=None, name=name, address=address)


@app.route('/register', methods=['GET', 'POST'])
def register():
    errors = []
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if not username or not password:
            errors.append('Username and password are required.')
        elif register_user(username, password):
            return redirect(url_for('login'))
        else:
            errors.append('Username already exists.')
    return render_template('register.html', errors=errors)


@app.route('/login', methods=['GET', 'POST'])
def login():
    errors = []
    next_url = request.args.get('next')
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if authenticate_user(username, password):
            session['user'] = username
            next_page = request.form.get('next')
            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            errors.append('Invalid username or password.')
    return render_template('login.html', errors=errors, next=next_url)


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)
