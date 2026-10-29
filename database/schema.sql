-- ========================================================
-- HOTEL MANAGEMENT SYSTEM (HMS) - COMPLETE MYSQL 8 SCHEMA
-- Production-Ready DDL with Foreign Keys, Indexes & Constraints
-- ========================================================

CREATE DATABASE IF NOT EXISTS `hotel_management` 
DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE `hotel_management`;

SET FOREIGN_KEY_CHECKS = 0;

-- 1. ROLES & PERMISSIONS
DROP TABLE IF EXISTS `role_permissions`;
DROP TABLE IF EXISTS `permissions`;
DROP TABLE IF EXISTS `roles`;
DROP TABLE IF EXISTS `users`;

CREATE TABLE `roles` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(50) NOT NULL UNIQUE,
    `description` VARCHAR(255) NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `permissions` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `code` VARCHAR(100) NOT NULL UNIQUE,
    `name` VARCHAR(100) NOT NULL,
    `module` VARCHAR(50) NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `role_permissions` (
    `role_id` INT NOT NULL,
    `permission_id` INT NOT NULL,
    PRIMARY KEY (`role_id`, `permission_id`),
    CONSTRAINT `fk_rp_role` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_rp_perm` FOREIGN KEY (`permission_id`) REFERENCES `permissions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `role_id` INT NOT NULL,
    `username` VARCHAR(60) NOT NULL UNIQUE,
    `email` VARCHAR(120) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `full_name` VARCHAR(120) NOT NULL,
    `phone` VARCHAR(30) NULL,
    `avatar` VARCHAR(255) DEFAULT 'default-avatar.png',
    `is_active` TINYINT(1) DEFAULT 1,
    `last_login` DATETIME NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_user_email` (`email`),
    INDEX `idx_user_role` (`role_id`),
    CONSTRAINT `fk_users_role` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. GUESTS (CRM)
DROP TABLE IF EXISTS `guests`;
CREATE TABLE `guests` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NULL UNIQUE,
    `first_name` VARCHAR(60) NOT NULL,
    `last_name` VARCHAR(60) NOT NULL,
    `email` VARCHAR(120) NOT NULL,
    `phone` VARCHAR(30) NOT NULL,
    `id_type` ENUM('Passport', 'National ID', 'Driver License') DEFAULT 'Passport',
    `id_number` VARCHAR(60) NOT NULL,
    `nationality` VARCHAR(60) DEFAULT 'Somali',
    `address` TEXT NULL,
    `vip_tier` ENUM('Standard', 'Silver', 'Gold', 'VIP Platinum') DEFAULT 'Standard',
    `is_blacklisted` TINYINT(1) DEFAULT 0,
    `loyalty_points` INT DEFAULT 0,
    `notes` TEXT NULL,
    `avatar` VARCHAR(255) NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_guest_phone` (`phone`),
    INDEX `idx_guest_id_number` (`id_number`),
    CONSTRAINT `fk_guest_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. ROOM TYPES, AMENITIES, ROOMS
DROP TABLE IF EXISTS `room_amenities`;
DROP TABLE IF EXISTS `amenities`;
DROP TABLE IF EXISTS `room_images`;
DROP TABLE IF EXISTS `rooms`;
DROP TABLE IF EXISTS `room_types`;

CREATE TABLE `room_types` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(60) NOT NULL UNIQUE,
    `slug` VARCHAR(60) NOT NULL UNIQUE,
    `description` TEXT NULL,
    `base_price` DECIMAL(10,2) NOT NULL,
    `weekend_price` DECIMAL(10,2) NOT NULL,
    `capacity_adults` INT NOT NULL DEFAULT 2,
    `capacity_children` INT NOT NULL DEFAULT 1,
    `bed_type` VARCHAR(50) DEFAULT '1 King Bed',
    `size_sqm` INT DEFAULT 35,
    `primary_image` VARCHAR(255) NULL,
    `is_active` TINYINT(1) DEFAULT 1,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `amenities` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(60) NOT NULL UNIQUE,
    `icon` VARCHAR(60) DEFAULT 'fa-check',
    `category` VARCHAR(50) DEFAULT 'General'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `room_amenities` (
    `room_type_id` INT NOT NULL,
    `amenity_id` INT NOT NULL,
    PRIMARY KEY (`room_type_id`, `amenity_id`),
    CONSTRAINT `fk_ra_type` FOREIGN KEY (`room_type_id`) REFERENCES `room_types` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_ra_amenity` FOREIGN KEY (`amenity_id`) REFERENCES `amenities` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `rooms` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `room_number` VARCHAR(20) NOT NULL UNIQUE,
    `floor` INT NOT NULL DEFAULT 1,
    `room_type_id` INT NOT NULL,
    `status` ENUM('Available', 'Occupied', 'Reserved', 'Cleaning', 'Maintenance', 'Out of Order') DEFAULT 'Available',
    `clean_status` ENUM('Clean', 'Dirty', 'In Progress', 'Inspected') DEFAULT 'Clean',
    `key_card_code` VARCHAR(50) NULL,
    `is_smoking` TINYINT(1) DEFAULT 0,
    `notes` TEXT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_room_status` (`status`),
    INDEX `idx_room_floor` (`floor`),
    CONSTRAINT `fk_room_type` FOREIGN KEY (`room_type_id`) REFERENCES `room_types` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `room_images` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `room_type_id` INT NOT NULL,
    `image_url` VARCHAR(255) NOT NULL,
    `caption` VARCHAR(100) NULL,
    `is_cover` TINYINT(1) DEFAULT 0,
    CONSTRAINT `fk_ri_type` FOREIGN KEY (`room_type_id`) REFERENCES `room_types` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. PROMOTIONS & SEASONAL PRICING
DROP TABLE IF EXISTS `promotions`;
CREATE TABLE `promotions` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `code` VARCHAR(30) NOT NULL UNIQUE,
    `title` VARCHAR(100) NOT NULL,
    `discount_type` ENUM('percentage', 'fixed') DEFAULT 'percentage',
    `discount_value` DECIMAL(10,2) NOT NULL,
    `start_date` DATE NOT NULL,
    `end_date` DATE NOT NULL,
    `min_spend` DECIMAL(10,2) DEFAULT 0.00,
    `is_active` TINYINT(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. BOOKINGS & RESERVATIONS
DROP TABLE IF EXISTS `booking_rooms`;
DROP TABLE IF EXISTS `bookings`;

CREATE TABLE `bookings` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `booking_reference` VARCHAR(30) NOT NULL UNIQUE,
    `guest_id` INT NOT NULL,
    `check_in_date` DATE NOT NULL,
    `check_out_date` DATE NOT NULL,
    `adults` INT NOT NULL DEFAULT 1,
    `children` INT NOT NULL DEFAULT 0,
    `status` ENUM('Pending', 'Confirmed', 'Checked-in', 'Checked-out', 'Cancelled', 'No-show') DEFAULT 'Pending',
    `booking_source` ENUM('Walk-in', 'Phone', 'Website', 'OTA Booking.com', 'OTA Expedia') DEFAULT 'Walk-in',
    `promotion_id` INT NULL,
    `special_requests` TEXT NULL,
    `subtotal_amount` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `tax_amount` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `discount_amount` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `total_amount` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `deposit_amount` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `paid_amount` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_booking_dates` (`check_in_date`, `check_out_date`),
    INDEX `idx_booking_status` (`status`),
    CONSTRAINT `fk_booking_guest` FOREIGN KEY (`guest_id`) REFERENCES `guests` (`id`) ON DELETE RESTRICT,
    CONSTRAINT `fk_booking_promo` FOREIGN KEY (`promotion_id`) REFERENCES `promotions` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `booking_rooms` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `booking_id` INT NOT NULL,
    `room_id` INT NOT NULL,
    `price_per_night` DECIMAL(10,2) NOT NULL,
    `nights` INT NOT NULL DEFAULT 1,
    `subtotal` DECIMAL(10,2) NOT NULL,
    CONSTRAINT `fk_br_booking` FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_br_room` FOREIGN KEY (`room_id`) REFERENCES `rooms` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. CHECK-IN / CHECK-OUT RECORDS
DROP TABLE IF EXISTS `checkin_records`;
CREATE TABLE `checkin_records` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `booking_id` INT NOT NULL UNIQUE,
    `room_id` INT NOT NULL,
    `actual_check_in` DATETIME NOT NULL,
    `actual_check_out` DATETIME NULL,
    `key_card_number` VARCHAR(50) NULL,
    `id_verified` TINYINT(1) DEFAULT 1,
    `early_checkin_fee` DECIMAL(10,2) DEFAULT 0.00,
    `late_checkout_fee` DECIMAL(10,2) DEFAULT 0.00,
    `checked_in_by` INT NULL,
    `checked_out_by` INT NULL,
    `notes` TEXT NULL,
    CONSTRAINT `fk_ci_booking` FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_ci_room` FOREIGN KEY (`room_id`) REFERENCES `rooms` (`id`) ON DELETE RESTRICT,
    CONSTRAINT `fk_ci_staff_in` FOREIGN KEY (`checked_in_by`) REFERENCES `users` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_ci_staff_out` FOREIGN KEY (`checked_out_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. BILLING, INVOICES & PAYMENTS
DROP TABLE IF EXISTS `payments`;
DROP TABLE IF EXISTS `invoice_items`;
DROP TABLE IF EXISTS `invoices`;

CREATE TABLE `invoices` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `invoice_number` VARCHAR(40) NOT NULL UNIQUE,
    `booking_id` INT NOT NULL,
    `guest_id` INT NOT NULL,
    `issue_date` DATE NOT NULL,
    `due_date` DATE NOT NULL,
    `subtotal` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `tax_rate` DECIMAL(5,2) DEFAULT 5.00,
    `tax_amount` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `discount_amount` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `total_amount` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `paid_amount` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `balance_due` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `status` ENUM('Draft', 'Unpaid', 'Partially Paid', 'Paid', 'Refunded', 'Void') DEFAULT 'Unpaid',
    `notes` TEXT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_invoice_status` (`status`),
    CONSTRAINT `fk_inv_booking` FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_inv_guest` FOREIGN KEY (`guest_id`) REFERENCES `guests` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `invoice_items` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `invoice_id` INT NOT NULL,
    `category` ENUM('Room Charge', 'Restaurant', 'Laundry', 'Spa', 'Minibar', 'Airport Transfer', 'Other Fee') DEFAULT 'Room Charge',
    `description` VARCHAR(255) NOT NULL,
    `unit_price` DECIMAL(10,2) NOT NULL,
    `quantity` INT NOT NULL DEFAULT 1,
    `total_price` DECIMAL(10,2) NOT NULL,
    `date_incurred` DATE NOT NULL,
    CONSTRAINT `fk_ii_invoice` FOREIGN KEY (`invoice_id`) REFERENCES `invoices` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `payments` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `payment_reference` VARCHAR(50) NOT NULL UNIQUE,
    `invoice_id` INT NOT NULL,
    `booking_id` INT NOT NULL,
    `amount` DECIMAL(10,2) NOT NULL,
    `payment_method` ENUM('Cash', 'Credit Card', 'EVC Plus', 'Zaad', 'Sahal', 'Bank Transfer') NOT NULL,
    `transaction_reference` VARCHAR(100) NULL,
    `status` ENUM('Completed', 'Pending', 'Failed', 'Refunded') DEFAULT 'Completed',
    `received_by` INT NULL,
    `payment_date` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_pay_inv` FOREIGN KEY (`invoice_id`) REFERENCES `invoices` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_pay_bk` FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_pay_user` FOREIGN KEY (`received_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. HOUSEKEEPING & LOST AND FOUND
DROP TABLE IF EXISTS `lost_and_found`;
DROP TABLE IF EXISTS `housekeeping_tasks`;

CREATE TABLE `housekeeping_tasks` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `room_id` INT NOT NULL,
    `assigned_to` INT NULL,
    `status` ENUM('Dirty', 'In Progress', 'Clean', 'Inspected') DEFAULT 'Dirty',
    `priority` ENUM('Low', 'Medium', 'High', 'Urgent') DEFAULT 'Medium',
    `cleaning_type` ENUM('Daily Tidy', 'Check-out Deep Clean', 'Disinfection', 'Turn Down') DEFAULT 'Check-out Deep Clean',
    `notes` TEXT NULL,
    `inspection_notes` TEXT NULL,
    `inspected_by` INT NULL,
    `started_at` DATETIME NULL,
    `completed_at` DATETIME NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_hk_room` FOREIGN KEY (`room_id`) REFERENCES `rooms` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_hk_staff` FOREIGN KEY (`assigned_to`) REFERENCES `users` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_hk_inspector` FOREIGN KEY (`inspected_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `lost_and_found` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `room_id` INT NULL,
    `item_name` VARCHAR(120) NOT NULL,
    `category` VARCHAR(50) DEFAULT 'Electronics',
    `description` TEXT NULL,
    `found_by` INT NULL,
    `found_date` DATE NOT NULL,
    `storage_location` VARCHAR(100) DEFAULT 'Main Safe',
    `status` ENUM('Found', 'Claimed', 'Donated', 'Disposed') DEFAULT 'Found',
    `claimant_name` VARCHAR(100) NULL,
    `claimant_phone` VARCHAR(50) NULL,
    `claimed_date` DATE NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_laf_room` FOREIGN KEY (`room_id`) REFERENCES `rooms` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_laf_staff` FOREIGN KEY (`found_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 9. MAINTENANCE
DROP TABLE IF EXISTS `maintenance_tickets`;
CREATE TABLE `maintenance_tickets` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `room_id` INT NULL,
    `reported_by` INT NOT NULL,
    `assigned_to` INT NULL,
    `issue_title` VARCHAR(150) NOT NULL,
    `description` TEXT NOT NULL,
    `priority` ENUM('Low', 'Medium', 'High', 'Emergency') DEFAULT 'Medium',
    `status` ENUM('Open', 'In Progress', 'Resolved', 'Closed') DEFAULT 'Open',
    `estimated_cost` DECIMAL(10,2) DEFAULT 0.00,
    `actual_cost` DECIMAL(10,2) DEFAULT 0.00,
    `resolution_notes` TEXT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `resolved_at` DATETIME NULL,
    CONSTRAINT `fk_mt_room` FOREIGN KEY (`room_id`) REFERENCES `rooms` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_mt_rep` FOREIGN KEY (`reported_by`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_mt_tech` FOREIGN KEY (`assigned_to`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 10. RESTAURANT & POS
DROP TABLE IF EXISTS `restaurant_order_items`;
DROP TABLE IF EXISTS `restaurant_orders`;
DROP TABLE IF EXISTS `menu_items`;
DROP TABLE IF EXISTS `menu_categories`;

CREATE TABLE `menu_categories` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(60) NOT NULL UNIQUE,
    `icon` VARCHAR(50) DEFAULT 'fa-utensils',
    `display_order` INT DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `menu_items` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `category_id` INT NOT NULL,
    `name` VARCHAR(100) NOT NULL,
    `description` TEXT NULL,
    `price` DECIMAL(10,2) NOT NULL,
    `is_available` TINYINT(1) DEFAULT 1,
    `preparation_time` INT DEFAULT 15,
    `image_url` VARCHAR(255) NULL,
    CONSTRAINT `fk_mi_cat` FOREIGN KEY (`category_id`) REFERENCES `menu_categories` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `restaurant_orders` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `order_number` VARCHAR(30) NOT NULL UNIQUE,
    `order_type` ENUM('Dine-In', 'Room Service', 'Takeaway') DEFAULT 'Dine-In',
    `room_id` INT NULL,
    `booking_id` INT NULL,
    `table_number` VARCHAR(20) NULL,
    `status` ENUM('Pending', 'In Kitchen', 'Ready', 'Delivered', 'Cancelled') DEFAULT 'Pending',
    `subtotal` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `tax_amount` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `total_amount` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `is_charged_to_room` TINYINT(1) DEFAULT 0,
    `created_by` INT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_ro_room` FOREIGN KEY (`room_id`) REFERENCES `rooms` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_ro_bk` FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_ro_staff` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `restaurant_order_items` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `order_id` INT NOT NULL,
    `menu_item_id` INT NOT NULL,
    `quantity` INT NOT NULL DEFAULT 1,
    `unit_price` DECIMAL(10,2) NOT NULL,
    `subtotal` DECIMAL(10,2) NOT NULL,
    `special_instructions` VARCHAR(255) NULL,
    CONSTRAINT `fk_roi_order` FOREIGN KEY (`order_id`) REFERENCES `restaurant_orders` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_roi_item` FOREIGN KEY (`menu_item_id`) REFERENCES `menu_items` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 11. EXTRA SERVICES (Laundry, Spa, Airport Transport, Tours)
DROP TABLE IF EXISTS `service_orders`;
DROP TABLE IF EXISTS `hotel_services`;

CREATE TABLE `hotel_services` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL,
    `category` ENUM('Laundry', 'Spa & Wellness', 'Airport Transport', 'Tour & Excursion', 'Minibar') NOT NULL,
    `price` DECIMAL(10,2) NOT NULL,
    `unit_type` VARCHAR(50) DEFAULT 'per service',
    `description` TEXT NULL,
    `is_active` TINYINT(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `service_orders` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `service_id` INT NOT NULL,
    `booking_id` INT NOT NULL,
    `room_id` INT NULL,
    `quantity` INT DEFAULT 1,
    `unit_price` DECIMAL(10,2) NOT NULL,
    `total_amount` DECIMAL(10,2) NOT NULL,
    `status` ENUM('Requested', 'In Progress', 'Completed', 'Cancelled') DEFAULT 'Requested',
    `is_charged_to_folio` TINYINT(1) DEFAULT 1,
    `notes` TEXT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_so_service` FOREIGN KEY (`service_id`) REFERENCES `hotel_services` (`id`) ON DELETE RESTRICT,
    CONSTRAINT `fk_so_bk` FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_so_room` FOREIGN KEY (`room_id`) REFERENCES `rooms` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 12. INVENTORY & SUPPLIERS
DROP TABLE IF EXISTS `stock_movements`;
DROP TABLE IF EXISTS `inventory_items`;
DROP TABLE IF EXISTS `inventory_categories`;
DROP TABLE IF EXISTS `suppliers`;

CREATE TABLE `suppliers` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(120) NOT NULL,
    `contact_person` VARCHAR(80) NULL,
    `phone` VARCHAR(30) NOT NULL,
    `email` VARCHAR(120) NULL,
    `address` TEXT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `inventory_categories` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(80) NOT NULL UNIQUE,
    `description` TEXT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `inventory_items` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `category_id` INT NOT NULL,
    `supplier_id` INT NULL,
    `name` VARCHAR(120) NOT NULL,
    `sku` VARCHAR(50) NOT NULL UNIQUE,
    `unit` VARCHAR(30) DEFAULT 'pcs',
    `quantity_in_stock` DECIMAL(10,2) DEFAULT 0.00,
    `min_reorder_level` DECIMAL(10,2) DEFAULT 10.00,
    `unit_cost` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    INDEX `idx_inv_sku` (`sku`),
    CONSTRAINT `fk_inv_cat` FOREIGN KEY (`category_id`) REFERENCES `inventory_categories` (`id`) ON DELETE RESTRICT,
    CONSTRAINT `fk_inv_sup` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `stock_movements` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `inventory_item_id` INT NOT NULL,
    `movement_type` ENUM('IN', 'OUT', 'ADJUSTMENT') NOT NULL,
    `quantity` DECIMAL(10,2) NOT NULL,
    `unit_cost` DECIMAL(10,2) NULL,
    `reason` VARCHAR(255) NOT NULL,
    `recorded_by` INT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_sm_item` FOREIGN KEY (`inventory_item_id`) REFERENCES `inventory_items` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_sm_user` FOREIGN KEY (`recorded_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 13. HR & STAFF MANAGEMENT
DROP TABLE IF EXISTS `leave_requests`;
DROP TABLE IF EXISTS `attendance`;
DROP TABLE IF EXISTS `shifts`;
DROP TABLE IF EXISTS `employees`;

CREATE TABLE `shifts` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(50) NOT NULL,
    `start_time` TIME NOT NULL,
    `end_time` TIME NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `employees` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NULL UNIQUE,
    `employee_code` VARCHAR(30) NOT NULL UNIQUE,
    `first_name` VARCHAR(60) NOT NULL,
    `last_name` VARCHAR(60) NOT NULL,
    `department` ENUM('Front Office', 'Housekeeping', 'Maintenance', 'Kitchen & Food', 'Accounting', 'Security', 'Management') NOT NULL,
    `designation` VARCHAR(80) NOT NULL,
    `phone` VARCHAR(30) NOT NULL,
    `email` VARCHAR(120) NOT NULL,
    `shift_id` INT NULL,
    `hire_date` DATE NOT NULL,
    `basic_salary` DECIMAL(10,2) NOT NULL,
    `status` ENUM('Active', 'On Leave', 'Suspended', 'Terminated') DEFAULT 'Active',
    CONSTRAINT `fk_emp_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_emp_shift` FOREIGN KEY (`shift_id`) REFERENCES `shifts` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `attendance` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `employee_id` INT NOT NULL,
    `date` DATE NOT NULL,
    `check_in` TIME NULL,
    `check_out` TIME NULL,
    `status` ENUM('Present', 'Late', 'Absent', 'On Leave') DEFAULT 'Present',
    `notes` VARCHAR(255) NULL,
    UNIQUE KEY `uk_emp_date` (`employee_id`, `date`),
    CONSTRAINT `fk_att_emp` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `leave_requests` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `employee_id` INT NOT NULL,
    `leave_type` ENUM('Annual Leave', 'Sick Leave', 'Emergency Leave', 'Maternity/Paternity') NOT NULL,
    `start_date` DATE NOT NULL,
    `end_date` DATE NOT NULL,
    `reason` TEXT NOT NULL,
    `status` ENUM('Pending', 'Approved', 'Rejected') DEFAULT 'Pending',
    `reviewed_by` INT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_lr_emp` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_lr_rev` FOREIGN KEY (`reviewed_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 14. EXPENSES & ACCOUNTING
DROP TABLE IF EXISTS `daily_cash_register`;
DROP TABLE IF EXISTS `expenses`;
DROP TABLE IF EXISTS `expense_categories`;

CREATE TABLE `expense_categories` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(80) NOT NULL UNIQUE,
    `description` TEXT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `expenses` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `category_id` INT NOT NULL,
    `amount` DECIMAL(10,2) NOT NULL,
    `expense_date` DATE NOT NULL,
    `description` TEXT NOT NULL,
    `payment_method` ENUM('Cash', 'Bank Transfer', 'Company Card', 'EVC Plus', 'Zaad') DEFAULT 'Cash',
    `recorded_by` INT NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_exp_cat` FOREIGN KEY (`category_id`) REFERENCES `expense_categories` (`id`) ON DELETE RESTRICT,
    CONSTRAINT `fk_exp_user` FOREIGN KEY (`recorded_by`) REFERENCES `users` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `daily_cash_register` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `register_date` DATE NOT NULL UNIQUE,
    `opening_cash` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `cash_collected` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `cash_paid_out` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `closing_cash` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `status` ENUM('Open', 'Closed') DEFAULT 'Open',
    `closed_by` INT NULL,
    `closed_at` DATETIME NULL,
    CONSTRAINT `fk_dcr_user` FOREIGN KEY (`closed_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 15. REVIEWS, NOTIFICATIONS, AUDIT LOGS, SETTINGS
DROP TABLE IF EXISTS `reviews`;
DROP TABLE IF EXISTS `notifications`;
DROP TABLE IF EXISTS `audit_logs`;
DROP TABLE IF EXISTS `hotel_settings`;

CREATE TABLE `reviews` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `booking_id` INT NULL,
    `guest_id` INT NOT NULL,
    `rating` INT NOT NULL CHECK (`rating` BETWEEN 1 AND 5),
    `title` VARCHAR(120) NULL,
    `comment` TEXT NOT NULL,
    `is_approved` TINYINT(1) DEFAULT 1,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_rev_bk` FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_rev_guest` FOREIGN KEY (`guest_id`) REFERENCES `guests` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `notifications` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NULL,
    `title` VARCHAR(150) NOT NULL,
    `message` TEXT NOT NULL,
    `type` ENUM('info', 'success', 'warning', 'danger') DEFAULT 'info',
    `is_read` TINYINT(1) DEFAULT 0,
    `link` VARCHAR(255) NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_notif_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `audit_logs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NULL,
    `action` VARCHAR(100) NOT NULL,
    `entity_name` VARCHAR(80) NOT NULL,
    `entity_id` INT NULL,
    `details` TEXT NULL,
    `ip_address` VARCHAR(45) NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_al_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `hotel_settings` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `setting_key` VARCHAR(80) NOT NULL UNIQUE,
    `setting_value` TEXT NOT NULL,
    `category` VARCHAR(50) DEFAULT 'General',
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;
