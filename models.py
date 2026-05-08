from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email    = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role     = db.Column(db.String(20), default='user')

    def is_admin(self):
        return self.role == 'admin'

class Customer(db.Model):
    __tablename__ = 'customers'
    id    = db.Column(db.Integer, primary_key=True)
    name  = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    orders = db.relationship('Order', backref='customer', lazy=True, cascade='all, delete-orphan')

class Order(db.Model):
    __tablename__ = 'orders'
    id          = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    date        = db.Column(db.Date, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status      = db.Column(db.String(50), default='pending')
    items       = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

class Product(db.Model):
    __tablename__ = 'products'
    id       = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.String(100), nullable=False)
    price    = db.Column(db.Float, nullable=False)
    stock    = db.Column(db.Integer, default=0)
    category = db.Column(db.String(50))
    order_items = db.relationship('OrderItem', backref='product', lazy=True)

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id         = db.Column(db.Integer, primary_key=True)
    order_id   = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity   = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)