from flask import Flask, render_template, redirect, url_for, request, session
from db import init_db, get_all_products, get_product_by_id
import os

app = Flask(__name__)
app.secret_key = "replace-with-a-secure-key"

# Initialize database if not exists
if not os.path.exists('products.db'):
    init_db()


def get_product(pid):
    return get_product_by_id(pid)


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
        session.pop("cart", None)
        return render_template("checkout.html", success=True)
    return render_template("checkout.html", success=False)


if __name__ == "__main__":
    app.run(debug=True)
