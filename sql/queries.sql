-- Cosmetic Inventory System: проверенные запросы предметной области

-- 1. Список всех средств с брендами и категориями
SELECT
    products.id,
    products.name,
    brands.name AS brand,
    categories.name AS category,
    products.quantity,
    products.expiry_date
FROM products
JOIN brands ON products.brand_id = brands.id
JOIN categories ON products.category_id = categories.id
ORDER BY products.expiry_date, products.name;

-- 2. Подробная информация о средстве по идентификатору
SELECT
    products.id,
    products.name,
    brands.name AS brand,
    categories.name AS category,
    products.quantity,
    products.expiry_date
FROM products
JOIN brands ON products.brand_id = brands.id
JOIN categories ON products.category_id = categories.id
WHERE products.id = ?;

-- 3. Поиск по названию средства, бренду или категории
SELECT
    products.id,
    products.name,
    brands.name AS brand,
    categories.name AS category,
    products.quantity,
    products.expiry_date
FROM products
JOIN brands ON products.brand_id = brands.id
JOIN categories ON products.category_id = categories.id
WHERE (
    products.name LIKE ?
    OR brands.name LIKE ?
    OR categories.name LIKE ?
)
AND (? = '' OR categories.name = ?)
ORDER BY products.name;

-- 4. Список средств выбранной категории
SELECT
    products.id,
    products.name,
    brands.name AS brand,
    categories.name AS category,
    products.quantity,
    products.expiry_date
FROM products
JOIN brands ON products.brand_id = brands.id
JOIN categories ON products.category_id = categories.id
WHERE categories.name = ?
ORDER BY products.name;

-- 5. Средства с остатком не выше заданного
SELECT
    products.id,
    products.name,
    brands.name AS brand,
    categories.name AS category,
    products.quantity,
    products.expiry_date
FROM products
JOIN brands ON products.brand_id = brands.id
JOIN categories ON products.category_id = categories.id
WHERE products.quantity <= ?
ORDER BY products.quantity, products.name;

-- 6. Средства, срок годности которых истекает до выбранной даты
SELECT
    products.id,
    products.name,
    brands.name AS brand,
    categories.name AS category,
    products.quantity,
    products.expiry_date
FROM products
JOIN brands ON products.brand_id = brands.id
JOIN categories ON products.category_id = categories.id
WHERE products.expiry_date <= ?
ORDER BY products.expiry_date, products.name;

-- 7. Общие показатели инвентаря
SELECT
    COUNT(products.id) AS products_count,
    COALESCE(SUM(products.quantity), 0) AS total_quantity,
    COUNT(DISTINCT products.brand_id) AS brands_count,
    COUNT(DISTINCT products.category_id) AS categories_count
FROM products;

-- 8. Количество средств, требующих пополнения или замены
SELECT
    COUNT(products.id) AS attention_count
FROM products
WHERE products.quantity <= ?
   OR products.expiry_date <= ?;

-- 9. Статистика запасов по категориям
SELECT
    categories.id,
    categories.name AS category,
    COUNT(products.id) AS products_count,
    COALESCE(SUM(products.quantity), 0) AS total_quantity
FROM categories
LEFT JOIN products ON categories.id = products.category_id
GROUP BY categories.id, categories.name
ORDER BY categories.name;

-- 10. Статистика запасов по брендам
SELECT
    brands.id,
    brands.name AS brand,
    COUNT(products.id) AS products_count,
    COALESCE(SUM(products.quantity), 0) AS total_quantity
FROM brands
LEFT JOIN products ON brands.id = products.brand_id
GROUP BY brands.id, brands.name
ORDER BY brands.name;

-- 11. Категории с заданным минимальным количеством позиций
SELECT
    categories.id,
    categories.name AS category,
    COUNT(products.id) AS products_count
FROM categories
JOIN products ON categories.id = products.category_id
GROUP BY categories.id, categories.name
HAVING COUNT(products.id) >= ?
ORDER BY products_count DESC, categories.name;

-- 12. Бренды, у которых есть средства с низким остатком
SELECT
    brands.id,
    brands.name AS brand,
    COUNT(products.id) AS low_stock_count
FROM brands
JOIN products ON brands.id = products.brand_id
WHERE products.quantity <= ?
GROUP BY brands.id, brands.name
HAVING COUNT(products.id) > 0
ORDER BY low_stock_count DESC, brands.name;
