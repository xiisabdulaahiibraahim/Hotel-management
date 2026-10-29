-- ========================================================
-- HOTEL MANAGEMENT SYSTEM (HMS) - SEED DATA
-- Complete Initial & Sample Data for Production / Demo
-- ========================================================

USE `hotel_management`;

-- 1. ROLES
INSERT INTO `roles` (`id`, `name`, `description`) VALUES
(1, 'Super Admin', 'Full system access and configurations'),
(2, 'Manager', 'Operations oversight, reports, staff management, approvals'),
(3, 'Receptionist', 'Front desk check-in, bookings, guest profiles, billing'),
(4, 'Housekeeping', 'Room cleaning status, housekeeping tasks, lost and found'),
(5, 'Accountant', 'Financial reports, billing folios, expense audits, cash registers'),
(6, 'Restaurant/POS Staff', 'Kitchen orders, restaurant billing, room service delivery'),
(7, 'Guest', 'Customer portal booking, order viewing, reviews');

-- 2. PERMISSIONS
INSERT INTO `permissions` (`id`, `code`, `name`, `module`) VALUES
(1, 'view_dashboard', 'View Dashboard Analytics', 'Dashboard'),
(2, 'manage_rooms', 'Create and Edit Rooms', 'Rooms'),
(3, 'view_rooms', 'View Room Status', 'Rooms'),
(4, 'manage_bookings', 'Create and Manage Bookings', 'Bookings'),
(5, 'manage_checkin', 'Perform Check-in and Check-out', 'FrontDesk'),
(6, 'manage_billing', 'Issue Invoices and Process Payments', 'Billing'),
(7, 'manage_housekeeping', 'Assign and Update Cleaning Tasks', 'Housekeeping'),
(8, 'manage_maintenance', 'Create and Resolve Tickets', 'Maintenance'),
(9, 'manage_restaurant', 'POS Orders and Kitchen Management', 'Restaurant'),
(10, 'manage_inventory', 'Manage Stock and Suppliers', 'Inventory'),
(11, 'manage_staff', 'Manage Staff, Shifts, Attendance', 'HR'),
(12, 'manage_expenses', 'Record Expenses and Cash Closings', 'Accounting'),
(13, 'view_reports', 'Generate and Export Reports', 'Reports'),
(14, 'manage_settings', 'Modify Hotel Settings & Policies', 'Settings');

-- 3. USERS (Default password for all demo accounts: Admin123! - hashed via pbkdf2/sha256)
-- pbkdf2:sha256:600000$h6eO7kS29nQz3ZtA$8e1a14a7940cecfbdc40139b4b9b6574fef0052745cf58f5043bf72fc3e887f5
-- We will also support dynamic seed through python run.py to ensure werkzeug generate_password_hash matches exactly!
INSERT INTO `users` (`id`, `role_id`, `username`, `email`, `password_hash`, `full_name`, `phone`, `is_active`) VALUES
(1, 1, 'admin', 'admin@grandhorizon.com', 'scrypt:32768:8:1$xPzV6uQhL3hG$dbb2b3b8c6a0c2738749a2a909a34da465dc4f71a94371fa79326b5e0c5218dbe1595fc3b92cb1bf2fb8848db2c3f8e58a741364d9551c6c59c5d18d45ba800f', 'Ahmed Cali Warsame', '+252 61 555 1000', 1),
(2, 2, 'manager', 'manager@grandhorizon.com', 'scrypt:32768:8:1$xPzV6uQhL3hG$dbb2b3b8c6a0c2738749a2a909a34da465dc4f71a94371fa79326b5e0c5218dbe1595fc3b92cb1bf2fb8848db2c3f8e58a741364d9551c6c59c5d18d45ba800f', 'Farhiya Maxamed Cilmi', '+252 61 555 2000', 1),
(3, 3, 'reception', 'reception@grandhorizon.com', 'scrypt:32768:8:1$xPzV6uQhL3hG$dbb2b3b8c6a0c2738749a2a909a34da465dc4f71a94371fa79326b5e0c5218dbe1595fc3b92cb1bf2fb8848db2c3f8e58a741364d9551c6c59c5d18d45ba800f', 'Khadra Cabdi Nuur', '+252 61 555 3000', 1),
(4, 4, 'housekeeping', 'clean@grandhorizon.com', 'scrypt:32768:8:1$xPzV6uQhL3hG$dbb2b3b8c6a0c2738749a2a909a34da465dc4f71a94371fa79326b5e0c5218dbe1595fc3b92cb1bf2fb8848db2c3f8e58a741364d9551c6c59c5d18d45ba800f', 'Maryan Xasan Jaamac', '+252 61 555 4000', 1),
(5, 5, 'accountant', 'finance@grandhorizon.com', 'scrypt:32768:8:1$xPzV6uQhL3hG$dbb2b3b8c6a0c2738749a2a909a34da465dc4f71a94371fa79326b5e0c5218dbe1595fc3b92cb1bf2fb8848db2c3f8e58a741364d9551c6c59c5d18d45ba800f', 'Guuleed Cumar Faarax', '+252 61 555 5000', 1),
(6, 6, 'pos', 'restaurant@grandhorizon.com', 'scrypt:32768:8:1$xPzV6uQhL3hG$dbb2b3b8c6a0c2738749a2a909a34da465dc4f71a94371fa79326b5e0c5218dbe1595fc3b92cb1bf2fb8848db2c3f8e58a741364d9551c6c59c5d18d45ba800f', 'Liibaan Cabdullaahi', '+252 61 555 6000', 1),
(7, 7, 'guest1', 'guest@example.com', 'scrypt:32768:8:1$xPzV6uQhL3hG$dbb2b3b8c6a0c2738749a2a909a34da465dc4f71a94371fa79326b5e0c5218dbe1595fc3b92cb1bf2fb8848db2c3f8e58a741364d9551c6c59c5d18d45ba800f', 'Dr. Jamaal Maxamuud', '+252 61 555 7777', 1);

-- 4. AMENITIES
INSERT INTO `amenities` (`id`, `name`, `icon`, `category`) VALUES
(1, 'Ultra High-Speed WiFi', 'fa-wifi', 'Connectivity'),
(2, 'Smart Climate Control', 'fa-snowflake', 'Comfort'),
(3, '65-inch 4K OLED TV', 'fa-tv', 'Entertainment'),
(4, 'Jacuzzi & Marble Tub', 'fa-hot-tub-person', 'Bathroom'),
(5, 'Fully Stocked Minibar', 'fa-wine-bottle', 'Refreshments'),
(6, 'Private Ocean Balcony', 'fa-water', 'Outdoor'),
(7, 'Electronic Digital Safe', 'fa-vault', 'Security'),
(8, 'Nespresso Luxury Machine', 'fa-mug-hot', 'Refreshments'),
(9, '24/7 Butler & Room Service', 'fa-bell-concierge', 'Service'),
(10, 'Luxury Spa Robe & Slippers', 'fa-shirt', 'Comfort');

-- 5. ROOM TYPES
INSERT INTO `room_types` (`id`, `name`, `slug`, `description`, `base_price`, `weekend_price`, `capacity_adults`, `capacity_children`, `bed_type`, `size_sqm`, `primary_image`) VALUES
(1, 'Single Deluxe', 'single-deluxe', 'Cozy, modern room designed for solo travelers with ergonomic work station and premium rain shower.', 65.00, 75.00, 1, 0, '1 Queen Bed', 28, '/static/img/rooms/single.jpg'),
(2, 'Double Executive', 'double-executive', 'Spacious executive room perfect for couples or business colleagues, with lounge seating and city view.', 110.00, 125.00, 2, 1, '1 King Bed or 2 Twins', 42, '/static/img/rooms/double.jpg'),
(3, 'Luxury Ocean Suite', 'luxury-ocean-suite', 'Spectacular panoramic ocean views, private walk-out balcony, living room parlor, and designer bath.', 180.00, 210.00, 2, 2, '1 Grand King Bed', 65, '/static/img/rooms/suite.jpg'),
(4, 'Family Grand Suite', 'family-grand-suite', 'Interconnected spacious luxury suite with two separate master bedrooms, dining table, and kids zone.', 240.00, 270.00, 4, 3, '2 King Beds + Sofa Bed', 95, '/static/img/rooms/family.jpg'),
(5, 'Presidential Royal Villa', 'presidential-royal-villa', 'The pinnacle of luxury: private butler service, jacuzzi, executive board dining table, and VIP airport escort.', 450.00, 520.00, 4, 2, 'Palatial King Master Suite', 160, '/static/img/rooms/presidential.jpg');

-- 6. ROOMS (20 Rooms across 4 floors)
INSERT INTO `rooms` (`id`, `room_number`, `floor`, `room_type_id`, `status`, `clean_status`, `key_card_code`, `is_smoking`, `notes`) VALUES
(1, '101', 1, 1, 'Available', 'Clean', 'KC-101-9821', 0, 'Near main garden terrace'),
(2, '102', 1, 1, 'Occupied', 'Clean', 'KC-102-4412', 0, 'Guest checked in early'),
(3, '103', 1, 1, 'Cleaning', 'Dirty', 'KC-103-1289', 0, 'Checkout pending inspection'),
(4, '104', 1, 2, 'Available', 'Clean', 'KC-104-6632', 0, 'Pool view facing'),
(5, '105', 1, 2, 'Reserved', 'Clean', 'KC-105-8819', 0, 'VIP arrival today 4:00 PM'),
(6, '201', 2, 2, 'Available', 'Clean', 'KC-201-3310', 0, 'Corner executive quiet room'),
(7, '202', 2, 2, 'Occupied', 'Clean', 'KC-202-5521', 0, 'Extended stay guest'),
(8, '203', 2, 2, 'Maintenance', 'Dirty', 'KC-203-9912', 0, 'AC coil maintenance in progress'),
(9, '204', 2, 3, 'Available', 'Clean', 'KC-204-7741', 0, 'High floor ocean breeze'),
(10, '205', 2, 3, 'Occupied', 'Clean', 'KC-205-2234', 0, 'Honeymoon couple setup'),
(11, '301', 3, 3, 'Available', 'Clean', 'KC-301-4431', 0, 'Ocean view sunrise view'),
(12, '302', 3, 3, 'Reserved', 'Clean', 'KC-302-8822', 0, 'Conference delegation booking'),
(13, '303', 3, 4, 'Occupied', 'Clean', 'KC-303-1190', 0, 'Family vacation 5 guests'),
(14, '304', 3, 4, 'Available', 'Clean', 'KC-304-6612', 0, 'Connected double suites'),
(15, '305', 3, 4, 'Cleaning', 'In Progress', 'KC-305-7788', 0, 'Housekeeping team actively cleaning'),
(16, '401', 4, 3, 'Available', 'Clean', 'KC-401-3349', 0, 'Top floor premium suite'),
(17, '402', 4, 4, 'Available', 'Clean', 'KC-402-9901', 0, 'Penthouse adjacent suite'),
(18, '403', 4, 5, 'Occupied', 'Clean', 'KC-403-0001', 0, 'VIP Foreign Ambassador stay'),
(19, '404', 4, 5, 'Available', 'Clean', 'KC-404-0002', 0, 'Presidential ready for booking'),
(20, '405', 4, 1, 'Out of Order', 'Dirty', 'KC-405-9999', 0, 'Full carpet replacement scheduled');

-- 7. GUESTS (10 Realistic Guest Profiles)
INSERT INTO `guests` (`id`, `user_id`, `first_name`, `last_name`, `email`, `phone`, `id_type`, `id_number`, `nationality`, `vip_tier`, `is_blacklisted`, `loyalty_points`, `notes`) VALUES
(1, 7, 'Dr. Jamaal', 'Maxamuud Cali', 'jamaal.m@somhealth.so', '+252 61 555 7777', 'Passport', 'P-SOM-992144', 'Somali', 'VIP Platinum', 0, 450, 'Prefers top-floor quiet suite, fresh fruit upon arrival'),
(2, NULL, 'Sarah', 'Jenkins', 's.jenkins@undp.org', '+254 712 345 678', 'Passport', 'P-GBR-782100', 'British', 'Gold', 0, 220, 'UN consultant, monthly repeat traveler'),
(3, NULL, 'Mustafe', 'Cabdikariin Warsame', 'mustafe.c@dalsan.com', '+252 61 700 8899', 'National ID', 'NID-SO-55102', 'Somali', 'Silver', 0, 110, 'Business entrepreneur, pays via EVC Plus'),
(4, NULL, 'Safiya', 'Xuseen Rooble', 'safiya.rooble@gmail.com', '+252 61 888 2233', 'Passport', 'P-SOM-441920', 'Somali', 'Standard', 0, 50, 'Family holiday trip'),
(5, NULL, 'Tariq', 'Al-Mansoor', 'tariq.mansoor@gulfinvest.ae', '+971 50 123 4567', 'Passport', 'P-ARE-119283', 'Emirati', 'VIP Platinum', 0, 890, 'Investment delegation leader, needs airport VIP pickup'),
(6, NULL, 'Amina', 'Ducaale Jaamac', 'amina.ducaale@telecom.so', '+252 63 444 9911', 'National ID', 'NID-SO-88219', 'Somali', 'Gold', 0, 310, 'Frequent corporate traveler from Hargeisa'),
(7, NULL, 'David', 'Kowalski', 'dkowalski@engineer.de', '+49 170 998877', 'Passport', 'P-DEU-882736', 'German', 'Standard', 0, 80, 'Infrastructure engineer, needs high-speed ethernet'),
(8, NULL, 'Hodman', 'Bashiir Nuur', 'hodan.bashiir@bank.so', '+252 61 999 4455', 'National ID', 'NID-SO-11928', 'Somali', 'Silver', 0, 160, 'Central Bank annual audit delegate'),
(9, NULL, 'Rashid', 'Omar Farah', 'rashid.farah@logistics.dj', '+253 77 88 99 00', 'Passport', 'P-DJI-556102', 'Djiboutian', 'Standard', 0, 40, 'Port logistics director'),
(10, NULL, 'Zahra', 'Axmed Shire', 'zahra.shire@diaspora.ca', '+1 416 555 0192', 'Passport', 'P-CAN-991204', 'Canadian', 'Gold', 0, 270, 'Diaspora homecoming visit, requires crib for infant');

-- 8. PROMOTIONS
INSERT INTO `promotions` (`id`, `code`, `title`, `discount_type`, `discount_value`, `start_date`, `end_date`, `min_spend`, `is_active`) VALUES
(1, 'WELCOME10', 'New Guest Welcome 10% Off', 'percentage', 10.00, '2026-01-01', '2026-12-31', 100.00, 1),
(2, 'LUXURY20', 'VIP Ocean Suite 20% Discount', 'percentage', 20.00, '2026-01-01', '2026-12-31', 300.00, 1),
(3, 'EIDSPECIAL', 'Eid Festive Holiday Offer', 'fixed', 50.00, '2026-01-01', '2026-12-31', 200.00, 1);

-- 9. BOOKINGS
INSERT INTO `bookings` (`id`, `booking_reference`, `guest_id`, `check_in_date`, `check_out_date`, `adults`, `children`, `status`, `booking_source`, `subtotal_amount`, `tax_amount`, `discount_amount`, `total_amount`, `deposit_amount`, `paid_amount`) VALUES
(1, 'BK-2026-001', 1, '2026-10-25', '2026-10-30', 2, 0, 'Checked-in', 'Website', 900.00, 45.00, 90.00, 855.00, 300.00, 855.00),
(2, 'BK-2026-002', 2, '2026-10-26', '2026-10-29', 1, 0, 'Checked-in', 'Walk-in', 195.00, 9.75, 0.00, 204.75, 100.00, 204.75),
(3, 'BK-2026-003', 5, '2026-10-27', '2026-11-02', 2, 1, 'Checked-in', 'Phone', 2700.00, 135.00, 200.00, 2635.00, 1000.00, 2635.00),
(4, 'BK-2026-004', 3, '2026-10-28', '2026-10-31', 2, 0, 'Confirmed', 'OTA Booking.com', 330.00, 16.50, 0.00, 346.50, 100.00, 100.00),
(5, 'BK-2026-005', 4, '2026-10-28', '2026-11-03', 4, 2, 'Confirmed', 'Website', 1440.00, 72.00, 144.00, 1368.00, 500.00, 500.00),
(6, 'BK-2026-006', 6, '2026-10-20', '2026-10-24', 2, 0, 'Checked-out', 'Walk-in', 440.00, 22.00, 0.00, 462.00, 200.00, 462.00),
(7, 'BK-2026-007', 7, '2026-10-29', '2026-11-04', 1, 0, 'Pending', 'Website', 390.00, 19.50, 0.00, 409.50, 0.00, 0.00);

-- Booking rooms mapping
INSERT INTO `booking_rooms` (`id`, `booking_id`, `room_id`, `price_per_night`, `nights`, `subtotal`) VALUES
(1, 1, 10, 180.00, 5, 900.00),
(2, 2, 2, 65.00, 3, 195.00),
(3, 3, 18, 450.00, 6, 2700.00),
(4, 4, 5, 110.00, 3, 330.00),
(5, 5, 13, 240.00, 6, 1440.00),
(6, 6, 7, 110.00, 4, 440.00);

-- 10. CHECK-IN RECORDS
INSERT INTO `checkin_records` (`id`, `booking_id`, `room_id`, `actual_check_in`, `key_card_number`, `id_verified`, `checked_in_by`) VALUES
(1, 1, 10, '2026-10-25 14:15:00', 'KC-205-2234', 1, 3),
(2, 2, 2, '2026-10-26 11:30:00', 'KC-102-4412', 1, 3),
(3, 3, 18, '2026-10-27 15:45:00', 'KC-403-0001', 1, 3);

-- 11. INVOICES & PAYMENTS
INSERT INTO `invoices` (`id`, `invoice_number`, `booking_id`, `guest_id`, `issue_date`, `due_date`, `subtotal`, `tax_rate`, `tax_amount`, `discount_amount`, `total_amount`, `paid_amount`, `balance_due`, `status`) VALUES
(1, 'INV-2026-0001', 1, 1, '2026-10-25', '2026-10-30', 955.00, 5.00, 47.75, 90.00, 912.75, 912.75, 0.00, 'Paid'),
(2, 'INV-2026-0002', 2, 2, '2026-10-26', '2026-10-29', 245.00, 5.00, 12.25, 0.00, 257.25, 257.25, 0.00, 'Paid'),
(3, 'INV-2026-0003', 3, 5, '2026-10-27', '2026-11-02', 2900.00, 5.00, 145.00, 200.00, 2845.00, 2845.00, 0.00, 'Paid'),
(4, 'INV-2026-0004', 4, 3, '2026-10-28', '2026-10-31', 330.00, 5.00, 16.50, 0.00, 346.50, 100.00, 246.50, 'Partially Paid');

INSERT INTO `invoice_items` (`id`, `invoice_id`, `category`, `description`, `unit_price`, `quantity`, `total_price`, `date_incurred`) VALUES
(1, 1, 'Room Charge', 'Luxury Ocean Suite (5 Nights @ $180/night)', 180.00, 5, 900.00, '2026-10-25'),
(2, 1, 'Restaurant', 'Seafood Platter & Fresh Mango Smoothies', 55.00, 1, 55.00, '2026-10-26'),
(3, 2, 'Room Charge', 'Single Deluxe (3 Nights @ $65/night)', 65.00, 3, 195.00, '2026-10-26'),
(4, 2, 'Laundry', 'Executive Dry Cleaning (3 Suits)', 50.00, 1, 50.00, '2026-10-27'),
(5, 3, 'Room Charge', 'Presidential Royal Villa (6 Nights @ $450/night)', 450.00, 6, 2700.00, '2026-10-27'),
(6, 3, 'Airport Transfer', 'VIP Armored Luxury Suburban Escort Transfer', 200.00, 1, 200.00, '2026-10-27');

INSERT INTO `payments` (`id`, `payment_reference`, `invoice_id`, `booking_id`, `amount`, `payment_method`, `transaction_reference`, `status`, `received_by`) VALUES
(1, 'PAY-2026-101', 1, 1, 300.00, 'EVC Plus', 'EVC-TRX-998811', 'Completed', 3),
(2, 'PAY-2026-102', 1, 1, 612.75, 'Credit Card', 'VISA-AUTH-441029', 'Completed', 3),
(3, 'PAY-2026-103', 2, 2, 257.25, 'Credit Card', 'MC-AUTH-881290', 'Completed', 3),
(4, 'PAY-2026-104', 3, 5, 2845.00, 'Bank Transfer', 'SWIFT-AE-992100', 'Completed', 5),
(5, 'PAY-2026-105', 4, 4, 100.00, 'Zaad', 'ZAAD-TX-332910', 'Completed', 3);

-- 12. HOUSEKEEPING TASKS & LOST AND FOUND
INSERT INTO `housekeeping_tasks` (`id`, `room_id`, `assigned_to`, `status`, `priority`, `cleaning_type`, `notes`) VALUES
(1, 3, 4, 'Dirty', 'High', 'Check-out Deep Clean', 'Guest checked out 10:00 AM, replenish towels and soaps'),
(2, 15, 4, 'In Progress', 'High', 'Check-out Deep Clean', 'Linen changed, bathroom scrubbing ongoing'),
(3, 8, 4, 'Dirty', 'Medium', 'Disinfection', 'Waiting for AC technician to finish filter change');

INSERT INTO `lost_and_found` (`id`, `room_id`, `item_name`, `category`, `description`, `found_by`, `found_date`, `status`, `storage_location`) VALUES
(1, 7, 'Apple iPad Pro with Silver Case', 'Electronics', 'Found on executive desk drawer in Room 202', 4, '2026-10-24', 'Found', 'Front Desk Safe A');

-- 13. MAINTENANCE TICKETS
INSERT INTO `maintenance_tickets` (`id`, `room_id`, `reported_by`, `assigned_to`, `issue_title`, `description`, `priority`, `status`, `estimated_cost`) VALUES
(1, 8, 3, 1, 'Room 203 Air Conditioner Low Cooling', 'Guest reported room temperature will not cool below 26C. Needs coolant recharge.', 'High', 'In Progress', 75.00),
(2, 20, 2, 1, 'Room 405 Water Pressure Valve Replacement', 'Main shower valve leaking in master bath. Parts ordered.', 'Emergency', 'Open', 150.00);

-- 14. RESTAURANT MENU & ORDERS
INSERT INTO `menu_categories` (`id`, `name`, `icon`, `display_order`) VALUES
(1, 'Breakfast Specialties', 'fa-egg', 1),
(2, 'Gourmet Mains & Steaks', 'fa-drumstick-bite', 2),
(3, 'Fresh Seafood & Grills', 'fa-fish', 3),
(4, 'Artisan Pastas & Pizzas', 'fa-pizza-slice', 4),
(5, 'Specialty Drinks & Mocktails', 'fa-martini-glass', 5),
(6, 'Desserts & Sweets', 'fa-cake-candles', 6);

INSERT INTO `menu_items` (`id`, `category_id`, `name`, `description`, `price`, `is_available`, `preparation_time`) VALUES
(1, 1, 'Somali Traditional Royal Breakfast', 'Fresh Anjero with spiced liver/beef suqaar, wild organic honey, and aromatic spiced cardamom tea.', 14.50, 1, 15),
(2, 1, 'American Continental Spread', 'Scrambled organic eggs, crispy turkey bacon, hash browns, grilled tomatoes, and bakery basket.', 16.00, 1, 15),
(3, 2, 'USDA Prime Ribeye Steak 350g', 'Charcoal-grilled to perfection with herb truffle butter, roasted asparagus, and potato puree.', 38.00, 1, 25),
(4, 2, 'Fragrant Goat Meat (Hilib Ari) with Spiced Rice', 'Tender slow-roasted Somali lamb/goat with seasoned saffron rice, fried onions, and banana.', 24.00, 1, 20),
(5, 3, 'Indian Ocean Jumbo Grilled Lobster', 'Fresh wild catch with garlic butter glaze, lemon zest, and seasoned Mediterranean couscous.', 45.00, 1, 30),
(6, 3, 'Kingfish Steak with Coconut Curry', 'Pan-seared ocean kingfish fillet served in velvety coconut lemongrass curry broth.', 28.00, 1, 20),
(7, 5, 'Fresh Tropical Mango-Passion Smoothie', '100% natural pureed mango, passion fruit, fresh lime and mint leaves.', 6.50, 1, 8),
(8, 5, 'Somali Spiced Somali Shaah Cad', 'Signature spiced milk tea with cinnamon, cloves, cardamom and nutmeg.', 4.00, 1, 5),
(9, 6, 'Belgian Lava Chocolate Souffle', 'Warm decadent dark chocolate cake with molten center and Tahitian vanilla bean gelato.', 11.00, 1, 15);

INSERT INTO `restaurant_orders` (`id`, `order_number`, `order_type`, `room_id`, `booking_id`, `status`, `subtotal`, `tax_amount`, `total_amount`, `is_charged_to_room`, `created_by`) VALUES
(1, 'ORD-2026-1001', 'Room Service', 10, 1, 'Delivered', 55.00, 2.75, 57.75, 1, 6),
(2, 'ORD-2026-1002', 'Dine-In', NULL, NULL, 'In Kitchen', 76.00, 3.80, 79.80, 0, 6);

INSERT INTO `restaurant_order_items` (`id`, `order_id`, `menu_item_id`, `quantity`, `unit_price`, `subtotal`) VALUES
(1, 1, 5, 1, 45.00, 45.00),
(2, 1, 7, 1, 6.50, 6.50),
(3, 1, 8, 1, 4.00, 4.00),
(4, 2, 3, 2, 38.00, 76.00);

-- 15. HOTEL EXTRA SERVICES
INSERT INTO `hotel_services` (`id`, `name`, `category`, `price`, `unit_type`, `description`) VALUES
(1, 'Express Laundry & Dry Cleaning', 'Laundry', 25.00, 'per bag', 'Same-day laundry and pressing service'),
(2, 'Swedish Full Body Deep Tissue Massage', 'Spa & Wellness', 80.00, '60 minutes', 'Therapeutic aromatic oil relaxation massage'),
(3, 'VIP Luxury Airport Suburban Transfer', 'Airport Transport', 60.00, 'per trip', 'Armored luxury SUV pickup from Aden Adde Airport'),
(4, 'Mogadishu Coastal & Historic City Tour', 'Tour & Excursion', 120.00, 'half day', 'Guided tour of Hamar Weyne old town, lighthouse, and Lido Beach');

-- 16. INVENTORY & SUPPLIERS
INSERT INTO `suppliers` (`id`, `name`, `contact_person`, `phone`, `email`, `address`) VALUES
(1, 'Somali Linen & Textile Corp', 'Cumar Shire', '+252 61 222 3344', 'sales@somtextile.so', 'KM4 Industrial Zone, Mogadishu'),
(2, 'Gulf Hospitality Amenities FZE', 'Kareem Mansoor', '+971 4 888 1234', 'info@gulfhospitality.ae', 'Jebel Ali, Dubai'),
(3, 'Ocean Fresh Seafood Supplies', 'Axmed Geedi', '+252 61 777 5522', 'orders@oceanfresh.so', 'Fish Market Wharf, Mogadishu');

INSERT INTO `inventory_categories` (`id`, `name`, `description`) VALUES
(1, 'Housekeeping & Linens', 'Bed sheets, duvet covers, pillowcases, bath towels'),
(2, 'Bathroom Toiletries & Amenities', 'Soaps, shampoos, conditioners, dental kits, shaving kits'),
(3, 'Food & Beverage Provisions', 'Steaks, fresh seafood, dairy, tea, coffee beans, produce'),
(4, 'Maintenance & Hardware', 'Bulbs, electrical switches, plumbing pipes, AC gas cylinders');

INSERT INTO `inventory_items` (`id`, `category_id`, `supplier_id`, `name`, `sku`, `unit`, `quantity_in_stock`, `min_reorder_level`, `unit_cost`) VALUES
(1, 1, 1, 'Egyptian Cotton King Bed Sheets (400 TC)', 'LIN-BED-K400', 'sets', 48.00, 20.00, 35.00),
(2, 1, 1, 'Luxury Plush Bath Towel Set (White)', 'LIN-TWL-WHT', 'sets', 95.00, 30.00, 18.00),
(3, 2, 2, 'Luxury Botanical Shampoo 50ml Bottled', 'TOI-SHMP-50', 'bottles', 320.00, 100.00, 1.20),
(4, 2, 2, 'Bamboo Fiber Dental & Shave Kit', 'TOI-KIT-BAM', 'boxes', 180.00, 50.00, 0.95),
(5, 3, 3, 'Fresh Indian Ocean Lobster Catch', 'FNB-LOB-RAW', 'kg', 18.00, 10.00, 22.00),
(6, 4, 2, 'Philips Warm White LED Spotlights 7W', 'MNT-LED-7W', 'pcs', 6.00, 15.00, 4.50);

-- 17. HR, EMPLOYEES & SHIFTS
INSERT INTO `shifts` (`id`, `name`, `start_time`, `end_time`) VALUES
(1, 'Morning Shift', '07:00:00', '15:30:00'),
(2, 'Evening Shift', '15:00:00', '23:30:00'),
(3, 'Night Shift', '23:00:00', '07:30:00');

INSERT INTO `employees` (`id`, `user_id`, `employee_code`, `first_name`, `last_name`, `department`, `designation`, `phone`, `email`, `shift_id`, `hire_date`, `basic_salary`, `status`) VALUES
(1, 1, 'EMP-001', 'Ahmed', 'Warsame', 'Management', 'General Manager', '+252 61 555 1000', 'admin@grandhorizon.com', 1, '2023-01-15', 3500.00, 'Active'),
(2, 2, 'EMP-002', 'Farhiya', 'Cilmi', 'Front Office', 'Front Office Director', '+252 61 555 2000', 'manager@grandhorizon.com', 1, '2023-03-01', 2200.00, 'Active'),
(3, 3, 'EMP-003', 'Khadra', 'Nuur', 'Front Office', 'Senior Receptionist', '+252 61 555 3000', 'reception@grandhorizon.com', 1, '2023-06-10', 950.00, 'Active'),
(4, 4, 'EMP-004', 'Maryan', 'Jaamac', 'Housekeeping', 'Executive Housekeeper', '+252 61 555 4000', 'clean@grandhorizon.com', 1, '2023-08-01', 800.00, 'Active'),
(5, 5, 'EMP-005', 'Guuleed', 'Faarax', 'Accounting', 'Chief Financial Accountant', '+252 61 555 5000', 'finance@grandhorizon.com', 1, '2023-02-15', 2000.00, 'Active'),
(6, 6, 'EMP-006', 'Liibaan', 'Cabdullaahi', 'Kitchen & Food', 'Head Chef / POS Operator', '+252 61 555 6000', 'restaurant@grandhorizon.com', 2, '2023-09-01', 1200.00, 'Active');

INSERT INTO `attendance` (`id`, `employee_id`, `date`, `check_in`, `check_out`, `status`) VALUES
(1, 1, '2026-10-27', '07:15:00', '16:00:00', 'Present'),
(2, 2, '2026-10-27', '07:25:00', '15:35:00', 'Present'),
(3, 3, '2026-10-27', '07:00:00', '15:30:00', 'Present'),
(4, 4, '2026-10-27', '06:55:00', '15:40:00', 'Present'),
(5, 5, '2026-10-27', '08:00:00', '16:30:00', 'Present');

-- 18. EXPENSES
INSERT INTO `expense_categories` (`id`, `name`, `description`) VALUES
(1, 'Utilities & Electricity', 'Generator diesel, city power grid, municipal water'),
(2, 'Kitchen & Food Provisions', 'Daily grocery, meat, fresh seafood, dairy'),
(3, 'Maintenance & Repairs', 'Plumbing, AC repairs, painting, electrical fixtures'),
(4, 'Marketing & Advertising', 'Social media campaigns, billboards, brochures'),
(5, 'Staff Welfare & Training', 'Staff meals, hospitality certifications, uniforms');

INSERT INTO `expenses` (`id`, `category_id`, `amount`, `expense_date`, `description`, `payment_method`, `recorded_by`) VALUES
(1, 1, 850.00, '2026-10-25', 'Diesel fuel supply for backup 350KVA generator (1,000 Liters)', 'Bank Transfer', 5),
(2, 2, 420.00, '2026-10-26', 'Fresh weekly ocean seafood procurement (Lobster, Tuna, Kingfish)', 'EVC Plus', 5),
(3, 3, 115.00, '2026-10-27', 'Plumbing spares and high-pressure shower fittings for Floor 2', 'Cash', 5);

INSERT INTO `daily_cash_register` (`id`, `register_date`, `opening_cash`, `cash_collected`, `cash_paid_out`, `closing_cash`, `status`, `closed_by`) VALUES
('1', '2026-10-26', 500.00, 1420.00, 115.00, 1805.00, 'Closed', 5);

-- 19. REVIEWS & NOTIFICATIONS
INSERT INTO `reviews` (`id`, `booking_id`, `guest_id`, `rating`, `title`, `comment`, `is_approved`) VALUES
(1, 1, 1, 5, 'Exceptional 5-Star Experience & Unbeatable Ocean View', 'The Grand Horizon is by far the finest luxury hotel in the region. Impeccable cleanliness, high-speed fiber internet, and delightful Somali cuisine!', 1),
(2, 6, 6, 5, 'Top Class Hospitality and Seamless Check-in', 'Staff was extremely professional and courteous. Check-in was swift and the room was sparkling clean. Highly recommended for business travelers.', 1);

INSERT INTO `notifications` (`id`, `user_id`, `title`, `message`, `type`, `is_read`, `link`) VALUES
(1, 1, 'New VIP Booking Received', 'Dr. Jamaal Maxamuud booked Luxury Ocean Suite (BK-2026-001).', 'success', 1, '/bookings'),
(2, 1, 'Low Stock Alert: LED Spotlights', 'Phillips Warm White LED Spotlights stock (6 pcs) is below minimum threshold (15 pcs).', 'warning', 0, '/inventory'),
(3, 3, 'Room 203 Maintenance Alert', 'Technician assigned to inspect AC unit in Room 203.', 'info', 0, '/maintenance');

-- 20. SETTINGS
INSERT INTO `hotel_settings` (`setting_key`, `setting_value`, `category`) VALUES
('hotel_name', 'The Grand Horizon Luxury Hotel & Resort', 'General'),
('hotel_tagline', 'Excellence in Hospitality, Unrivaled Luxury', 'General'),
('hotel_email', 'reservations@grandhorizon.com', 'General'),
('hotel_phone', '+252 (61) 555-0100', 'General'),
('hotel_address', 'Ocean Boulevard, Lido Coastline, Mogadishu, Somalia', 'General'),
('currency_code', 'USD', 'Finance'),
('currency_symbol', '$', 'Finance'),
('secondary_currency', 'SOS', 'Finance'),
('exchange_rate_usd_sos', '26000', 'Finance'),
('tax_rate_percentage', '5.0', 'Finance'),
('service_charge_percentage', '3.0', 'Finance'),
('check_in_time', '14:00', 'Operations'),
('check_out_time', '11:00', 'Operations'),
('default_language', 'English', 'Localization'),
('theme_mode', 'dark', 'Appearance'),
('cancellation_days', '2', 'Policies');
