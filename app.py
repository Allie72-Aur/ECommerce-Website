from flask import Flask, render_template, redirect, url_for, request, session
from db import init_db, get_all_products, get_product_by_id, save_order
import os
import json
import re

app = Flask(__name__)
app.secret_key = "replace-with-a-secure-key"

# Initialize database if not exists
if not os.path.exists('products.db'):
    init_db()


def get_product(pid):
    return get_product_by_id(pid)


def sanitize_text(text):
    return re.sub(r'[^\w\s@.-]', '', text.strip())


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
    if request.method == "POST":
        name = sanitize_text(request.form.get("name", ""))
        address = sanitize_text(request.form.get("address", ""))
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
            return render_template("checkout.html", success=False, errors=errors)
        # Save order
        save_order(name, address, payment_method, payment_info, json.dumps(items), total)
        session.pop("cart", None)
        return render_template("checkout.html", success=True)
    return render_template("checkout.html", success=False, errors=None)


if __name__ == "__main__":
    app.run(debug=True)
