"""
app.py - Main Flask application for ElectroShop e-commerce site.
Handles routing, user sessions, cart, checkout, and integrates with db.py.
"""

from db import (
    init_db,
    register_user,
    authenticate_user,
    get_user_id,
    get_user_info,
    get_all_products,
    get_product_by_id,
    save_order,
    update_stock,
)
import json
import re
from flask import Flask, render_template, redirect, url_for, request, session
from urllib.parse import urlparse, urljoin

app = Flask(__name__)
app.secret_key = "ercynpr-jvgu-n-frpher-xrl"

# Initialize database on app start (dev only)
init_db()


def get_product(pid):
    """
    Helper to fetch a product by its ID.
    """
    return get_product_by_id(pid)


def sanitize_text(text):
    """
    Remove unwanted characters from user input for basic sanitization.
    """
    return re.sub(r"[^\w\s@.-]", "", text.strip())


def is_safe_url(target):
    """
    Check if a redirect target is safe (same host, http/https).
    """
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


@app.route("/")
def index():
    """
    Home page: show all products in carousels.
    """
    return render_template("index.html", products=get_all_products())


@app.route("/product/<int:pid>")
def product_detail(pid):
    """
    Product detail page for a single product.
    """
    product = get_product(pid)
    if not product:
        return redirect(url_for("index"))
    return render_template("product.html", product=product)


@app.route("/add_to_cart/<int:pid>", methods=["GET"])
def add_to_cart(pid):
    """
    Add a product to the cart with a specified quantity (limited by stock).
    """
    cart = session.get("cart", {})
    product = get_product(pid)
    if not product or product.get("stock", 0) == 0:
        return redirect(url_for("cart"))
    try:
        qty = int(request.args.get("qty", 1))
    except (TypeError, ValueError):
        qty = 1
    # Clamp quantity to available stock
    qty = max(1, min(qty, product["stock"]))
    cart[str(pid)] = cart.get(str(pid), 0) + qty
    # Ensure cart quantity does not exceed stock
    if cart[str(pid)] > product["stock"]:
        cart[str(pid)] = product["stock"]
    session["cart"] = cart
    return redirect(url_for("cart"))


@app.route("/cart")
def cart():
    """
    Display the user's cart with all items and totals.
    """
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
    """
    Checkout page: requires login, validates form, saves order, updates stock.
    """
    if "user" not in session:
        # Redirect to login with next param if not logged in
        return redirect(url_for("login", next=request.url))
    user_info = get_user_info(session["user"])
    name = user_info["username"] if user_info else ""
    address = ""
    if request.method == "POST":
        # Get and sanitize form fields
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
            payment_info = json.dumps(
                {"cc_number": cc_number, "cc_expiry": cc_expiry, "cc_cvc": cc_cvc}
            )
        elif payment_method == "paypal":
            paypal_email = sanitize_text(request.form.get("paypal_email", ""))
            if not paypal_email:
                errors.append("PayPal email is required.")
            payment_info = json.dumps({"paypal_email": paypal_email})
        # Prepare cart items and check stock
        cart = session.get("cart", {})
        items = []
        total = 0
        for pid, qty in cart.items():
            product = get_product(int(pid))
            if product:
                if product.get("stock", 0) < qty:
                    errors.append(f"Not enough stock for {product['name']}.")
                subtotal = product["price"] * qty
                items.append({"product": product, "qty": qty, "subtotal": subtotal})
                total += subtotal
        if not items:
            errors.append("Cart is empty.")
        if errors:
            return render_template(
                "checkout.html",
                success=False,
                errors=errors,
                name=name,
                address=address,
            )
        # Save order with user_id
        user_id = get_user_id(session["user"])
        save_order(
            name,
            address,
            payment_method,
            payment_info,
            json.dumps(items),
            total,
            user_id=user_id,
        )
        # Update stock for each product
        for pid, qty in cart.items():
            update_stock(int(pid), qty)
        session.pop("cart", None)
        return render_template("checkout.html", success=True)
    return render_template(
        "checkout.html", success=False, errors=None, name=name, address=address
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    """
    User registration page. Registers user, logs them in, and redirects to next or home.
    """
    errors = []
    next_url = request.args.get("next")
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        form_next = request.form.get("next")
        if not username or not password:
            errors.append("Username and password are required.")
        elif register_user(username, password):
            session["user"] = username  # Log in the user automatically
            # Redirect to next_url if safe, else home
            if form_next and is_safe_url(form_next):
                return redirect(form_next)
            elif next_url and is_safe_url(next_url):
                return redirect(next_url)
            return redirect(url_for("index"))
        else:
            errors.append("Username already exists.")
    return render_template("register.html", errors=errors, next=next_url)


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    User login page. Authenticates and redirects to next or home.
    """
    errors = []
    next_url = request.args.get("next")
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if authenticate_user(username, password):
            session["user"] = username
            next_page = request.form.get("next")
            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            return redirect(url_for("index"))
        else:
            errors.append("Invalid username or password.")
    return render_template("login.html", errors=errors, next=next_url)


@app.route("/logout")
def logout():
    """
    Log out the current user and redirect to home.
    """
    session.pop("user", None)
    return redirect(url_for("index"))


if __name__ == "__main__":
    # Run the Flask development server
    app.run(debug=True)
