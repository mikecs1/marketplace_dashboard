# Customer Order Management System
### DBII Project — Database Systems II

---

## Overview

A web-based Customer Order Management System built with Python and Flask.
The application allows a business to manage customers, products, and orders
through a fully relational SQLite database with four interconnected tables.

---

## Technologies Used

| Layer     | Technology              |
|-----------|-------------------------|
| Language  | Python 3                |
| Framework | Flask                   |
| Database  | SQLite (app.db)         |
| ORM       | SQLAlchemy              |
| Frontend  | HTML, CSS, Jinja2       |

---

## Project Structure

```
DBII/
├── app.py                      ← Flask application and all routes
├── models.py                   ← Database models (SQLAlchemy)
├── requirements.txt            ← Python dependencies
├── app.db                      ← SQLite database (auto-created)
│
├── static/
│   └── style.css               ← Application stylesheet
│
└── templates/
    ├── base.html               ← Master layout (sidebar, nav)
    ├── index.html              ← Dashboard
    ├── customers.html          ← Customer list
    ├── customer_form.html      ← Add / Edit customer
    ├── customer_detail.html    ← Single customer + their orders
    ├── orders.html             ← Order list
    ├── order_form.html         ← Add / Edit order
    ├── products.html           ← Product list
    ├── product_form.html       ← Add / Edit product
    └── reports.html            ← SQL JOIN query results
```

---

## Database Schema

### Tables

**CUSTOMERS** (Strong Entity)
- id — INTEGER, PRIMARY KEY, AUTOINCREMENT
- name — TEXT, NOT NULL
- email — TEXT, NOT NULL, UNIQUE
- phone — TEXT

**PRODUCTS** (Strong Entity)
- id — INTEGER, PRIMARY KEY, AUTOINCREMENT
- name — TEXT, NOT NULL
- price — REAL, NOT NULL
- stock — INTEGER, DEFAULT 0
- category — TEXT

**ORDERS** (Strong Entity, depends on CUSTOMERS)
- id — INTEGER, PRIMARY KEY, AUTOINCREMENT
- customer_id — INTEGER, FOREIGN KEY → customers.id
- date — TEXT, NOT NULL
- total_price — REAL, NOT NULL
- status — TEXT, DEFAULT 'pending'

**ORDER_ITEMS** (Weak Entity)
- id — INTEGER, PRIMARY KEY, AUTOINCREMENT (surrogate)
- order_id — INTEGER, FOREIGN KEY → orders.id
- product_id — INTEGER, FOREIGN KEY → products.id
- quantity — INTEGER, NOT NULL
- unit_price — REAL, NOT NULL

### Relationships
- CUSTOMERS  ||--o{  ORDERS       (one customer places zero or many orders)
- ORDERS     ||--o{  ORDER_ITEMS  (one order contains one or many items)
- PRODUCTS   ||--o{  ORDER_ITEMS  (one product appears in zero or many items)

---

## How to Run

### Step 1 — Install dependencies
```bash
pip install flask flask-sqlalchemy
```

### Step 2 — Start the application
```bash
python app.py
```

### Step 3 — Open the browser
```
http://127.0.0.1:5000
```

The database file (app.db) is created automatically on first run.
No manual database setup is required.

---

## Application Pages

| Page              | Route                  | Description                                  |
|-------------------|------------------------|----------------------------------------------|
| Dashboard         | /                      | Live stats: customers, orders, revenue       |
| Customers         | /customers             | List all customers                           |
| Add Customer      | /customers/new         | Create a new customer                        |
| Edit Customer     | /customers/edit/<id>   | Update an existing customer                  |
| Customer Detail   | /customers/<id>        | View one customer and all their orders       |
| Orders            | /orders                | List all orders                              |
| Add Order         | /orders/new            | Create an order with dynamic product rows    |
| Edit Order        | /orders/edit/<id>      | Update an existing order                     |
| Products          | /products              | List all products with stock badges          |
| Add Product       | /products/new          | Create a new product                         |
| Edit Product      | /products/edit/<id>    | Update an existing product                   |
| Reports           | /reports               | Three raw SQL JOIN query results             |

---

## CRUD Operations

All four CRUD operations are implemented for every entity:
- Create — add new customers, orders, products
- Read   — list pages, detail pages, dashboard stats
- Update — edit forms pre-filled with existing data
- Delete — delete with confirmation dialog, cascade on related records

---

## SQL JOIN Queries (Reports Page)

Three raw SQL JOIN queries are demonstrated on the /reports page:

1. **2-table JOIN** — Orders joined with Customers
   Shows every order alongside the customer who placed it.

2. **4-table JOIN** — Order Items joined with Orders, Customers, and Products
   Full breakdown of every line item across all four tables.

3. **LEFT JOIN + GROUP BY** — Product Sales Summary
   Aggregates total units sold and revenue per product.
   Uses LEFT JOIN so products with zero orders still appear.

---

## Notes

- Do NOT run models.py directly. It is imported by app.py automatically.
- The app.db file can be inspected with DB Browser for SQLite.
- Deleting a customer automatically deletes their orders and order items (cascade).
- Order item prices are snapshotted at time of purchase — changing a product
  price later does not affect historical orders.
