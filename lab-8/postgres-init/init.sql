-- Create order system schema
CREATE SCHEMA IF NOT EXISTS order_system;

-- Inventory table
CREATE TABLE IF NOT EXISTS order_system.inventory (
    product_id VARCHAR(50) PRIMARY KEY,
    product_name VARCHAR(200) NOT NULL,
    available_quantity INTEGER NOT NULL DEFAULT 0,
    reserved_quantity INTEGER NOT NULL DEFAULT 0,
    price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE IF NOT EXISTS order_system.orders (
    order_id VARCHAR(50) PRIMARY KEY,
    customer_email VARCHAR(200) NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order items table
CREATE TABLE IF NOT EXISTS order_system.order_items (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(50) REFERENCES order_system.orders(order_id),
    product_id VARCHAR(50) REFERENCES order_system.inventory(product_id),
    quantity INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL
);

-- Stock reservations table
CREATE TABLE IF NOT EXISTS order_system.stock_reservations (
    reservation_id VARCHAR(50) PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL,
    product_id VARCHAR(50) REFERENCES order_system.inventory(product_id),
    quantity INTEGER NOT NULL,
    reserved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'active'
);

-- Insert sample inventory
INSERT INTO order_system.inventory (product_id, product_name, available_quantity, price) VALUES
    ('LAPTOP-001', 'Gaming Laptop', 10, 1299.99),
    ('MOUSE-001', 'Wireless Mouse', 50, 49.99),
    ('KEYBOARD-001', 'Mechanical Keyboard', 25, 149.99),
    ('MONITOR-001', '27" 4K Monitor', 15, 499.99),
    ('HEADSET-001', 'Gaming Headset', 30, 89.99)
ON CONFLICT (product_id) DO NOTHING; 