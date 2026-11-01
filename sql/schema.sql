-- Cosmetic Inventory System: структура базы данных

CREATE TABLE IF NOT EXISTS brands (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    brand_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    expiry_date TEXT NOT NULL,
    FOREIGN KEY (brand_id) REFERENCES brands(id),
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE INDEX IF NOT EXISTS idx_products_brand_id
ON products(brand_id);

CREATE INDEX IF NOT EXISTS idx_products_category_id
ON products(category_id);

CREATE INDEX IF NOT EXISTS idx_products_expiry_date
ON products(expiry_date);
