from flask import Flask, render_template, redirect, url_for, request, session

app = Flask(__name__)
app.secret_key = 'replace-with-a-secure-key'

# Sample product data
electronics = [
    {'id': 1, 'name': 'Smartphone', 'price': 299.99, 'desc': 'Latest model smartphone', 'img': 'https://via.placeholder.com/150'},
    {'id': 2, 'name': 'Laptop', 'price': 799.99, 'desc': 'Lightweight laptop', 'img': 'https://via.placeholder.com/150'},
    {'id': 3, 'name': 'Headphones', 'price': 49.99, 'desc': 'Noise-cancelling headphones', 'img': 'https://via.placeholder.com/150'},
    {'id': 4, 'name': 'Charger', 'price': 19.99, 'desc': 'Fast USB charger', 'img': 'https://via.placeholder.com/150'},
]

def get_product(pid):
    return next((item for item in electronics if item['id'] == pid), None)

@app.route('/')
def index():
    return render_template('index.html', products=electronics)

@app.route('/product/<int:pid>')
def product_detail(pid):
    product = get_product(pid)
    if not product:
        return redirect(url_for('index'))
    return render_template('product.html', product=product)

@app.route('/add_to_cart/<int:pid>')
def add_to_cart(pid):
    cart = session.get('cart', {})
    cart[str(pid)] = cart.get(str(pid), 0) + 1
    session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    items = []
    total = 0
    for pid, qty in cart.items():
        product = get_product(int(pid))
        if product:
            subtotal = product['price'] * qty
            items.append({'product': product, 'qty': qty, 'subtotal': subtotal})
            total += subtotal
    return render_template('cart.html', items=items, total=total)

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        session.pop('cart', None)
        return render_template('checkout.html', success=True)
    return render_template('checkout.html', success=False)

if __name__ == '__main__':
    app.run(debug=True)
