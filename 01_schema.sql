-- Normalised schema (SQLite / also valid in PostgreSQL with minor type changes)
DROP TABLE IF EXISTS orders; DROP TABLE IF EXISTS products; DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id      TEXT PRIMARY KEY,
    first_order_date TEXT,
    last_order_date  TEXT
);
CREATE TABLE products (
    product_id       INTEGER PRIMARY KEY,
    product_name     TEXT UNIQUE,
    product_category TEXT
);
CREATE TABLE orders (
    order_id       TEXT PRIMARY KEY,
    customer_id    TEXT REFERENCES customers(customer_id),
    product_id     INTEGER REFERENCES products(product_id),
    order_date     TEXT,
    order_month    TEXT,
    region         TEXT,
    payment_method TEXT,
    order_status   TEXT,
    quantity       INTEGER,
    unit_price     REAL,
    discount_pct   REAL,
    revenue        REAL,
    total_cost     REAL,
    profit         REAL
);
