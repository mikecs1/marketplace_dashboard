from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from models import db, User, Customer, Order, Product, OrderItem
from datetime import date
import os

app = Flask(__name__)


# Database path — works locally and on PythonAnywhere
# mihnea18.pythonanywhere.com
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "app.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')

db.init_app(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'error'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('You need admin privileges to access this page.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

with app.app_context():
    db.create_all()

# ─── HOME ───────────────────────────────────────────────
@app.route('/')
@login_required
def index():
    total_customers = Customer.query.count()
    total_orders    = Order.query.count()
    recent_orders   = Order.query.order_by(Order.id.desc()).limit(5).all()
    total_revenue   = db.session.query(db.func.sum(Order.total_price)).scalar() or 0
    return render_template('index.html',
                           total_customers=total_customers,
                           total_orders=total_orders,
                           recent_orders=recent_orders,
                           total_revenue=total_revenue)

# ─── AUTH ───────────────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        email    = request.form['email']
        password = request.form['password']

        existing_user  = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first()

        if existing_user:
            flash('Username already taken.', 'error')
            return redirect(url_for('register'))
        if existing_email:
            flash('Email already registered.', 'error')
            return redirect(url_for('register'))

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email,
                    password=hashed_pw, role='user')
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {username}! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        flash('Incorrect username or password.', 'error')
    return render_template('login.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# ─── CUSTOMERS ──────────────────────────────────────────
@app.route('/customers')
@login_required
def customers():
    all_customers = Customer.query.all()
    return render_template('customers.html', customers=all_customers)

@app.route('/customers/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_customer():
    if request.method == 'POST':
        name  = request.form['name']
        email = request.form['email']
        phone = request.form.get('phone', '')
        existing = Customer.query.filter_by(email=email).first()
        if existing:
            flash('A customer with that email already exists.', 'error')
            return redirect(url_for('new_customer'))
        customer = Customer(name=name, email=email, phone=phone)
        db.session.add(customer)
        db.session.commit()
        flash(f'Customer "{name}" added!', 'success')
        return redirect(url_for('customers'))
    return render_template('customer_form.html', customer=None)

@app.route('/customers/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_customer(id):
    customer = Customer.query.get_or_404(id)
    if request.method == 'POST':
        customer.name  = request.form['name']
        customer.email = request.form['email']
        customer.phone = request.form.get('phone', '')
        db.session.commit()
        flash(f'Customer "{customer.name}" updated!', 'success')
        return redirect(url_for('customers'))
    return render_template('customer_form.html', customer=customer)

@app.route('/customers/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    name = customer.name
    db.session.delete(customer)
    db.session.commit()
    flash(f'Customer "{name}" deleted.', 'info')
    return redirect(url_for('customers'))

@app.route('/customers/<int:id>')
def customer_detail(id):
    customer = Customer.query.get_or_404(id)
    return render_template('customer_detail.html', customer=customer)

# ─── ORDERS ─────────────────────────────────────────────
@app.route('/orders')
@login_required
def orders():
    all_orders = Order.query.order_by(Order.id.desc()).all()
    return render_template('orders.html', orders=all_orders)

@app.route('/orders/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_order():
    customers = Customer.query.all()
    products  = Product.query.all()
    if request.method == 'POST':
        customer_id = request.form['customer_id']
        status      = request.form.get('status', 'pending')
        date_str    = request.form.get('date')
        from datetime import datetime
        order_date  = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Create the order first with total 0 — we'll calculate it below
        order = Order(customer_id=customer_id, status=status,
                      date=order_date, total_price=0)
        db.session.add(order)
        db.session.flush()  # gives order an ID without fully committing

        # Read all product rows submitted from the form
        product_ids = request.form.getlist('product_id[]')
        quantities  = request.form.getlist('quantity[]')

        total = 0
        for pid, qty in zip(product_ids, quantities):
            if not pid or not qty or int(qty) < 1:
                continue  # skip empty rows
            product    = Product.query.get(pid)
            qty        = int(qty)
            unit_price = product.price
            line_total = qty * unit_price
            total     += line_total
            item = OrderItem(order_id=order.id, product_id=pid,
                             quantity=qty, unit_price=unit_price)
            db.session.add(item)

        order.total_price = round(total, 2)
        db.session.commit()
        flash('Order added!', 'success')
        return redirect(url_for('orders'))

    return render_template('order_form.html', order=None,
                           customers=customers, products=products)

@app.route('/orders/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_order(id):
    order     = Order.query.get_or_404(id)
    customers = Customer.query.all()
    products  = Product.query.all()
    if request.method == 'POST':
        order.customer_id = request.form['customer_id']
        order.status      = request.form.get('status', 'pending')
        date_str = request.form.get('date')
        from datetime import datetime
        order.date = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Delete old items and replace with new ones
        OrderItem.query.filter_by(order_id=order.id).delete()

        product_ids = request.form.getlist('product_id[]')
        quantities  = request.form.getlist('quantity[]')

        total = 0
        for pid, qty in zip(product_ids, quantities):
            if not pid or not qty or int(qty) < 1:
                continue
            product    = Product.query.get(pid)
            qty        = int(qty)
            unit_price = product.price
            line_total = qty * unit_price
            total     += line_total
            item = OrderItem(order_id=order.id, product_id=pid,
                             quantity=qty, unit_price=unit_price)
            db.session.add(item)

        order.total_price = round(total, 2)
        db.session.commit()
        flash('Order updated!', 'success')
        return redirect(url_for('orders'))

    return render_template('order_form.html', order=order,
                           customers=customers, products=products)

@app.route('/orders/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_order(id):
    order = Order.query.get_or_404(id)
    db.session.delete(order)
    db.session.commit()
    flash('Order deleted.', 'info')
    return redirect(url_for('orders'))

# ─── PRODUCTS ───────────────────────────────────────────
@app.route('/products')
@login_required
@admin_required
def products():
    all_products = Product.query.all()
    return render_template('products.html', products=all_products)

@app.route('/products/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_product():
    if request.method == 'POST':
        name     = request.form['name']
        price    = request.form['price']
        stock    = request.form.get('stock', 0)
        category = request.form.get('category', '')
        product  = Product(name=name, price=price, stock=stock, category=category)
        db.session.add(product)
        db.session.commit()
        flash(f'Product "{name}" added!', 'success')
        return redirect(url_for('products'))
    return render_template('product_form.html', product=None)

@app.route('/products/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    if request.method == 'POST':
        product.name     = request.form['name']
        product.price    = request.form['price']
        product.stock    = request.form.get('stock', 0)
        product.category = request.form.get('category', '')
        db.session.commit()
        flash(f'Product "{product.name}" updated!', 'success')
        return redirect(url_for('products'))
    return render_template('product_form.html', product=product)

@app.route('/products/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    name = product.name
    db.session.delete(product)
    db.session.commit()
    flash(f'Product "{name}" deleted.', 'info')
    return redirect(url_for('products'))

# ─── JOIN QUERIES ────────────────────────────────────────
@app.route('/reports')
@login_required
@admin_required
def reports():

    # JOIN 1 — Orders with their Customer name
    orders_with_customers = db.session.execute(db.text('''
        SELECT
            orders.id          AS order_id,
            customers.name     AS customer_name,
            customers.email    AS customer_email,
            orders.date        AS order_date,
            orders.total_price AS total_price,
            orders.status      AS status
        FROM orders
        JOIN customers ON orders.customer_id = customers.id
        ORDER BY orders.id DESC
    ''')).fetchall()

    # JOIN 2 — 4-table JOIN: order_items + orders + customers + products
    order_items_detail = db.session.execute(db.text('''
        SELECT
            order_items.id         AS item_id,
            customers.name         AS customer_name,
            orders.id              AS order_id,
            orders.date            AS order_date,
            products.name          AS product_name,
            products.category      AS category,
            order_items.quantity   AS quantity,
            order_items.unit_price AS unit_price,
            (order_items.quantity * order_items.unit_price) AS line_total
        FROM order_items
        JOIN orders    ON order_items.order_id   = orders.id
        JOIN customers ON orders.customer_id     = customers.id
        JOIN products  ON order_items.product_id = products.id
        ORDER BY orders.id DESC
    ''')).fetchall()

    # JOIN 3 — Product sales summary with LEFT JOIN + GROUP BY
    product_sales = db.session.execute(db.text('''
        SELECT
            products.name                                          AS product_name,
            products.category                                      AS category,
            products.price                                         AS unit_price,
            products.stock                                         AS stock,
            COUNT(order_items.id)                                  AS times_ordered,
            COALESCE(SUM(order_items.quantity), 0)                 AS total_units_sold,
            COALESCE(SUM(order_items.quantity * order_items.unit_price), 0) AS total_revenue
        FROM products
        LEFT JOIN order_items ON order_items.product_id = products.id
        GROUP BY products.id
        ORDER BY total_revenue DESC
    ''')).fetchall()

    return render_template('reports.html',
                           orders_with_customers=orders_with_customers,
                           order_items_detail=order_items_detail,
                           product_sales=product_sales)

if __name__ == '__main__':
    app.run(debug=False)