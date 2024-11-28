-- Insert mock data for database
-- Drop database if it exists
DROP DATABASE IF EXISTS `hello`;
DROP DATABASE IF EXISTS `db-name-1`;
DROP DATABASE IF EXISTS `db-name-2`;
DROP DATABASE IF EXISTS `db-name-3`;
DROP DATABASE IF EXISTS `db-name-4`;
DROP DATABASE IF EXISTS `db-name-5`;

-- Create the database schema and users
CREATE DATABASE `hello`;
CREATE DATABASE `db-name-1`;
CREATE DATABASE `db-name-2`;
CREATE DATABASE `db-name-3`;
CREATE DATABASE `db-name-4`;
CREATE DATABASE `db-name-5`;

USE `db-name-1`;

CREATE TABLE `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(50) NOT NULL,
    `email` VARCHAR(100) UNIQUE NOT NULL,
    `password` VARCHAR(255) NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE `roles` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `role_name` VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE `user_roles` (
    `user_id` INT NOT NULL,
    `role_id` INT NOT NULL,
    PRIMARY KEY (`user_id`, `role_id`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`role_id`) REFERENCES `roles`(`id`) ON DELETE CASCADE
);

USE `db-name-2`;

CREATE TABLE `products` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL,
    `description` TEXT,
    `price` DECIMAL(10, 2) NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE `customers` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `first_name` VARCHAR(50) NOT NULL,
    `last_name` VARCHAR(50) NOT NULL,
    `email` VARCHAR(100) UNIQUE NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE `orders` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `customer_id` INT NOT NULL,
    `order_date` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`customer_id`) REFERENCES `customers`(`id`) ON DELETE CASCADE
);

USE `db-name-3`;

CREATE TABLE `posts` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `title` VARCHAR(255) NOT NULL,
    `content` TEXT NOT NULL,
    `author` VARCHAR(100) NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE `comments` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `post_id` INT NOT NULL,
    `comment_text` TEXT NOT NULL,
    `commenter` VARCHAR(100),
    `comment_date` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`post_id`) REFERENCES `posts`(`id`) ON DELETE CASCADE
);
USE `db-name-4`;

CREATE TABLE `items` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `item_name` VARCHAR(100) NOT NULL,
    `quantity` INT NOT NULL,
    `price_per_unit` DECIMAL(10, 2) NOT NULL,
    `last_updated` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE `suppliers` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `supplier_name` VARCHAR(100) NOT NULL,
    `contact_email` VARCHAR(100) UNIQUE
);

CREATE TABLE `item_suppliers` (
    `item_id` INT NOT NULL,
    `supplier_id` INT NOT NULL,
    PRIMARY KEY (`item_id`, `supplier_id`),
    FOREIGN KEY (`item_id`) REFERENCES `items`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`supplier_id`) REFERENCES `suppliers`(`id`) ON DELETE CASCADE
);
USE `db-name-5`;

CREATE TABLE `courses` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `course_name` VARCHAR(100) NOT NULL,
    `description` TEXT,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE `students` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `first_name` VARCHAR(50) NOT NULL,
    `last_name` VARCHAR(50) NOT NULL,
    `email` VARCHAR(100) UNIQUE NOT NULL,
    `enrollment_date` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE `enrollments` (
    `student_id` INT NOT NULL,
    `course_id` INT NOT NULL,
    `enrollment_date` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`student_id`, `course_id`),
    FOREIGN KEY (`student_id`) REFERENCES `students`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`course_id`) REFERENCES `courses`(`id`) ON DELETE CASCADE
);

USE `hello`;
-- Drop and recreate Users
DROP USER IF EXISTS 'network_admin'@'%';
DROP USER IF EXISTS 'network_sales'@'%';
DROP USER IF EXISTS 'network_dev'@'%';

-- Create Users
CREATE USER 'network_admin'@'%' IDENTIFIED BY 'admin_pass123';
CREATE USER 'network_sales'@'%' IDENTIFIED BY 'sales_pass123';
CREATE USER 'network_dev'@'%' IDENTIFIED BY 'dev_pass123';

-- Drop tables if they exist
DROP TABLE IF EXISTS `product_development`;
DROP TABLE IF EXISTS `inventory`;
DROP TABLE IF EXISTS `sales`;
DROP TABLE IF EXISTS `products`;
DROP TABLE IF EXISTS `users`;

-- Create Tables
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    product_category VARCHAR(100),
    launch_date DATE,
    price DECIMAL(10, 2),
    stock INT,
    cloud_integration BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sales (
    sale_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT,
    quantity_sold INT,
    sale_date DATE,
    region VARCHAR(50),
    revenue DECIMAL(10, 2),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE IF NOT EXISTS inventory (
    inventory_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT,
    warehouse_location VARCHAR(100),
    stock_quantity INT,
    last_stock_update DATE,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE IF NOT EXISTS product_development (
    development_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT,
    feature_name VARCHAR(255),
    status VARCHAR(50),
    assigned_dev VARCHAR(100),
    sprint_date DATE,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Grant Permissions
GRANT ALL PRIVILEGES ON `hello`.* TO 'network_admin'@'%';
GRANT SELECT ON products TO 'network_sales'@'%';
GRANT SELECT ON sales TO 'network_sales'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON .product_development TO 'network_dev'@'%';
GRANT SELECT ON sales TO 'network_dev'@'%';

-- Apply Changes
FLUSH PRIVILEGES;

-- Insert dummy users
INSERT INTO users (username, email, role, password)
VALUES 
('admin', 'admin@network.com', 'admin', 'password123'),
('user1', 'user1@network.com', 'user', 'password123'),
('user2', 'user2@network.com', 'user', 'password123');

-- Insert dummy products
INSERT INTO products (product_name, product_category, launch_date, price, stock, cloud_integration)
VALUES 
('Smart Router', 'Networking', '2023-01-15', 120.00, 1000, TRUE),
('Smart Thermostat', 'Smart Home', '2022-11-23', 250.00, 200, TRUE),
('WiFi Extender', 'Networking', '2021-07-05', 50.00, 1500, FALSE),
('Smart Light Bulb', 'Smart Home', '2020-05-18', 30.00, 800, TRUE),
('Smart Plug', 'Smart Home', '2024-08-20', 15.00, 1200, TRUE);

-- Insert data into Sales table
INSERT INTO sales (product_id, quantity_sold, sale_date, region, revenue)
VALUES 
(1, 300, '2023-01-10', 'North America', 59997),
(2, 120, '2023-01-15', 'Europe', 35998.80),
(3, 500, '2023-02-01', 'Asia', 49995),
(1, 200, '2023-02-05', 'North America', 39998),
(4, 150, '2023-02-15', 'South America', 13498.50);

-- Insert data into Product Development table
INSERT INTO product_development (product_id, feature_name, status, assigned_dev, sprint_date)
VALUES 
(1, 'Cloud Connectivity Enhancement', 'In Progress', 'John Doe', '2023-03-01'),
(2, '5G Support', 'Completed', 'Jane Smith', '2022-12-15'),
(3, 'Voice Command Integration', 'Not Started', 'Peter Parker', '2023-05-10'),
(4, 'Antenna Redesign', 'In Progress', 'Bruce Wayne', '2023-03-20'),
(5, 'Energy Saving Mode', 'Completed', 'Clark Kent', '2023-01-05');

-- Insert data into Inventory table
INSERT INTO inventory (product_id, warehouse_location, stock_quantity, last_stock_update)
VALUES 
(1, 'Warehouse A', 800, '2023-01-25'),
(2, 'Warehouse B', 400, '2023-02-01'),
(3, 'Warehouse A', 150, '2023-01-30'),
(4, 'Warehouse C', 850, '2023-01-28'),
(5, 'Warehouse D', 1750, '2023-02-10');
