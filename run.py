import os
from datetime import datetime, date, time
from app import create_app
from app.models import (
    db, Role, Permission, User, Guest, RoomType, Amenity, Room,
    Promotion, Booking, BookingRoom, CheckinRecord, Invoice, InvoiceItem,
    Payment, HousekeepingTask, LostAndFound, MaintenanceTicket,
    MenuCategory, MenuItem, RestaurantOrder, RestaurantOrderItem,
    HotelService, Supplier, InventoryCategory, InventoryItem, StockMovement,
    Shift, Employee, Attendance, ExpenseCategory, Expense, DailyCashRegister,
    Review, Notification, HotelSetting
)

app = create_app()

def seed_database():
    """Seed initial data if database is empty."""
    with app.app_context():
        db.create_all()

        # Check if roles exist
        if Role.query.count() == 0:
            print("Seeding Hotel Management System with demo & initial data...")

            # 1. Roles
            roles = {
                'Super Admin': 'Full system access and configurations',
                'Manager': 'Operations oversight, reports, staff management, approvals',
                'Receptionist': 'Front desk check-in, bookings, guest profiles, billing',
                'Housekeeping': 'Room cleaning status, housekeeping tasks, lost and found',
                'Accountant': 'Financial reports, billing folios, expense audits, cash registers',
                'Restaurant/POS Staff': 'Kitchen orders, restaurant billing, room service delivery',
                'Guest': 'Customer portal booking, order viewing, reviews'
            }
            role_objs = {}
            for name, desc in roles.items():
                r = Role(name=name, description=desc)
                db.session.add(r)
                role_objs[name] = r
            db.session.flush()

            # 2. Permissions
            perms = [
                ('view_dashboard', 'View Dashboard Analytics', 'Dashboard'),
                ('manage_rooms', 'Create and Edit Rooms', 'Rooms'),
                ('view_rooms', 'View Room Status', 'Rooms'),
                ('manage_bookings', 'Create and Manage Bookings', 'Bookings'),
                ('manage_checkin', 'Perform Check-in and Check-out', 'FrontDesk'),
                ('manage_billing', 'Issue Invoices and Process Payments', 'Billing'),
                ('manage_housekeeping', 'Assign and Update Cleaning Tasks', 'Housekeeping'),
                ('manage_maintenance', 'Create and Resolve Tickets', 'Maintenance'),
                ('manage_restaurant', 'POS Orders and Kitchen Management', 'Restaurant'),
                ('manage_inventory', 'Manage Stock and Suppliers', 'Inventory'),
                ('manage_staff', 'Manage Staff, Shifts, Attendance', 'HR'),
                ('manage_expenses', 'Record Expenses and Cash Closings', 'Accounting'),
                ('view_reports', 'Generate and Export Reports', 'Reports'),
                ('manage_settings', 'Modify Hotel Settings & Policies', 'Settings')
            ]
            for code, name, module in perms:
                p = Permission(code=code, name=name, module=module)
                db.session.add(p)
            db.session.flush()

            # 3. Default Users (Password: Admin123!)
            default_users = [
                ('admin', 'admin@grandhorizon.com', 'Ahmed Cali Warsame', '+252 61 555 1000', 'Super Admin'),
                ('manager', 'manager@grandhorizon.com', 'Farhiya Maxamed Cilmi', '+252 61 555 2000', 'Manager'),
                ('reception', 'reception@grandhorizon.com', 'Khadra Cabdi Nuur', '+252 61 555 3000', 'Receptionist'),
                ('housekeeping', 'clean@grandhorizon.com', 'Maryan Xasan Jaamac', '+252 61 555 4000', 'Housekeeping'),
                ('accountant', 'finance@grandhorizon.com', 'Guuleed Cumar Faarax', '+252 61 555 5000', 'Accountant'),
                ('pos', 'restaurant@grandhorizon.com', 'Liibaan Cabdullaahi', '+252 61 555 6000', 'Restaurant/POS Staff'),
                ('guest1', 'guest@example.com', 'Dr. Jamaal Maxamuud', '+252 61 555 7777', 'Guest')
            ]
            user_objs = {}
            for username, email, full_name, phone, role_name in default_users:
                u = User(
                    username=username,
                    email=email,
                    full_name=full_name,
                    phone=phone,
                    role_id=role_objs[role_name].id,
                    is_active=True
                )
                u.set_password('Admin123!')
                db.session.add(u)
                user_objs[username] = u
            db.session.flush()

            # 4. Amenities
            amenities_data = [
                ('Ultra High-Speed WiFi', 'fa-wifi', 'Connectivity'),
                ('Smart Climate Control', 'fa-snowflake', 'Comfort'),
                ('65-inch 4K OLED TV', 'fa-tv', 'Entertainment'),
                ('Jacuzzi & Marble Tub', 'fa-hot-tub-person', 'Bathroom'),
                ('Fully Stocked Minibar', 'fa-wine-bottle', 'Refreshments'),
                ('Private Ocean Balcony', 'fa-water', 'Outdoor'),
                ('Electronic Digital Safe', 'fa-vault', 'Security'),
                ('Nespresso Luxury Machine', 'fa-mug-hot', 'Refreshments'),
                ('24/7 Butler & Room Service', 'fa-bell-concierge', 'Service'),
                ('Luxury Spa Robe & Slippers', 'fa-shirt', 'Comfort')
            ]
            amenity_objs = []
            for name, icon, cat in amenities_data:
                a = Amenity(name=name, icon=icon, category=cat)
                db.session.add(a)
                amenity_objs.append(a)
            db.session.flush()

            # 5. Room Types
            room_types_data = [
                ('Single Deluxe', 'single-deluxe', 'Cozy, modern room designed for solo travelers with ergonomic work station and premium rain shower.', 65.0, 75.0, 1, 0, '1 Queen Bed', 28, 'https://images.unsplash.com/photo-1618773928121-c32242e63f39?w=800&auto=format&fit=crop'),
                ('Double Executive', 'double-executive', 'Spacious executive room perfect for couples or business colleagues, with lounge seating and city view.', 110.0, 125.0, 2, 1, '1 King Bed or 2 Twins', 42, 'https://images.unsplash.com/photo-1591088398332-8a7791972843?w=800&auto=format&fit=crop'),
                ('Luxury Ocean Suite', 'luxury-ocean-suite', 'Spectacular panoramic ocean views, private walk-out balcony, living room parlor, and designer bath.', 180.0, 210.0, 2, 2, '1 Grand King Bed', 65, 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=800&auto=format&fit=crop'),
                ('Family Grand Suite', 'family-grand-suite', 'Interconnected spacious luxury suite with two separate master bedrooms, dining table, and kids zone.', 240.0, 270.0, 4, 3, '2 King Beds + Sofa Bed', 95, 'https://images.unsplash.com/photo-1566665797739-1674de7a421a?w=800&auto=format&fit=crop'),
                ('Presidential Royal Villa', 'presidential-royal-villa', 'The pinnacle of luxury: private butler service, jacuzzi, executive board dining table, and VIP airport escort.', 450.0, 520.0, 4, 2, 'Palatial King Master Suite', 160, 'https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=800&auto=format&fit=crop')
            ]
            type_objs = []
            for name, slug, desc, base_p, wk_p, ad, ch, bed, sz, img in room_types_data:
                rt = RoomType(
                    name=name, slug=slug, description=desc,
                    base_price=base_p, weekend_price=wk_p,
                    capacity_adults=ad, capacity_children=ch,
                    bed_type=bed, size_sqm=sz, primary_image=img
                )
                rt.amenities.extend(amenity_objs[:6])
                db.session.add(rt)
                type_objs.append(rt)
            db.session.flush()

            # 6. 20 Rooms across 4 floors
            room_configs = [
                ('101', 1, 0, 'Available', 'Clean', 'KC-101-9821'),
                ('102', 1, 0, 'Occupied', 'Clean', 'KC-102-4412'),
                ('103', 1, 0, 'Cleaning', 'Dirty', 'KC-103-1289'),
                ('104', 1, 1, 'Available', 'Clean', 'KC-104-6632'),
                ('105', 1, 1, 'Reserved', 'Clean', 'KC-105-8819'),
                ('201', 2, 1, 'Available', 'Clean', 'KC-201-3310'),
                ('202', 2, 1, 'Occupied', 'Clean', 'KC-202-5521'),
                ('203', 2, 1, 'Maintenance', 'Dirty', 'KC-203-9912'),
                ('204', 2, 2, 'Available', 'Clean', 'KC-204-7741'),
                ('205', 2, 2, 'Occupied', 'Clean', 'KC-205-2234'),
                ('301', 3, 2, 'Available', 'Clean', 'KC-301-4431'),
                ('302', 3, 2, 'Reserved', 'Clean', 'KC-302-8822'),
                ('303', 3, 3, 'Occupied', 'Clean', 'KC-303-1190'),
                ('304', 3, 3, 'Available', 'Clean', 'KC-304-6612'),
                ('305', 3, 3, 'Cleaning', 'In Progress', 'KC-305-7788'),
                ('401', 4, 2, 'Available', 'Clean', 'KC-401-3349'),
                ('402', 4, 3, 'Available', 'Clean', 'KC-402-9901'),
                ('403', 4, 4, 'Occupied', 'Clean', 'KC-403-0001'),
                ('404', 4, 4, 'Available', 'Clean', 'KC-404-0002'),
                ('405', 4, 0, 'Out of Order', 'Dirty', 'KC-405-9999'),
            ]
            room_objs = []
            for num, flr, type_idx, st, cst, kc in room_configs:
                r = Room(
                    room_number=num,
                    floor=flr,
                    room_type_id=type_objs[type_idx].id,
                    status=st,
                    clean_status=cst,
                    key_card_code=kc
                )
                db.session.add(r)
                room_objs.append(r)
            db.session.flush()

            # 7. 10 Guests (CRM)
            guests_data = [
                ('Dr. Jamaal', 'Maxamuud Cali', 'jamaal.m@somhealth.so', '+252 61 555 7777', 'Passport', 'P-SOM-992144', 'Somali', 'VIP Platinum', 450, user_objs['guest1'].id),
                ('Sarah', 'Jenkins', 's.jenkins@undp.org', '+254 712 345 678', 'Passport', 'P-GBR-782100', 'British', 'Gold', 220, None),
                ('Mustafe', 'Cabdikariin Warsame', 'mustafe.c@dalsan.com', '+252 61 700 8899', 'National ID', 'NID-SO-55102', 'Somali', 'Silver', 110, None),
                ('Safiya', 'Xuseen Rooble', 'safiya.rooble@gmail.com', '+252 61 888 2233', 'Passport', 'P-SOM-441920', 'Somali', 'Standard', 50, None),
                ('Tariq', 'Al-Mansoor', 'tariq.mansoor@gulfinvest.ae', '+971 50 123 4567', 'Passport', 'P-ARE-119283', 'Emirati', 'VIP Platinum', 890, None),
                ('Amina', 'Ducaale Jaamac', 'amina.ducaale@telecom.so', '+252 63 444 9911', 'National ID', 'NID-SO-88219', 'Somali', 'Gold', 310, None),
                ('David', 'Kowalski', 'dkowalski@engineer.de', '+49 170 998877', 'Passport', 'P-DEU-882736', 'German', 'Standard', 80, None),
                ('Hodman', 'Bashiir Nuur', 'hodan.bashiir@bank.so', '+252 61 999 4455', 'National ID', 'NID-SO-11928', 'Somali', 'Silver', 160, None),
                ('Rashid', 'Omar Farah', 'rashid.farah@logistics.dj', '+253 77 88 99 00', 'Passport', 'P-DJI-556102', 'Djiboutian', 'Standard', 40, None),
                ('Zahra', 'Axmed Shire', 'zahra.shire@diaspora.ca', '+1 416 555 0192', 'Passport', 'P-CAN-991204', 'Canadian', 'Gold', 270, None)
            ]
            guest_objs = []
            for fn, ln, em, ph, idt, idn, nat, vip, pts, uid in guests_data:
                g = Guest(
                    first_name=fn, last_name=ln, email=em, phone=ph,
                    id_type=idt, id_number=idn, nationality=nat,
                    vip_tier=vip, loyalty_points=pts, user_id=uid
                )
                db.session.add(g)
                guest_objs.append(g)
            db.session.flush()

            # 8. Promotions
            promo1 = Promotion(code='WELCOME10', title='Welcome 10% Off', discount_type='percentage', discount_value=10.0, start_date=date(2026, 1, 1), end_date=date(2026, 12, 31), min_spend=100.0)
            promo2 = Promotion(code='LUXURY20', title='Ocean Suite 20% Off', discount_type='percentage', discount_value=20.0, start_date=date(2026, 1, 1), end_date=date(2026, 12, 31), min_spend=300.0)
            db.session.add_all([promo1, promo2])
            db.session.flush()

            # 9. Bookings & Invoices
            # Booking 1: Checked-in
            b1 = Booking(
                booking_reference='BK-2026-001', guest_id=guest_objs[0].id,
                check_in_date=date(2026, 10, 25), check_out_date=date(2026, 10, 30),
                adults=2, children=0, status='Checked-in', booking_source='Website',
                subtotal_amount=900.0, tax_amount=45.0, discount_amount=90.0,
                total_amount=855.0, deposit_amount=300.0, paid_amount=855.0
            )
            db.session.add(b1)
            db.session.flush()
            br1 = BookingRoom(booking_id=b1.id, room_id=room_objs[9].id, price_per_night=180.0, nights=5, subtotal=900.0)
            ci1 = CheckinRecord(booking_id=b1.id, room_id=room_objs[9].id, actual_check_in=datetime(2026, 10, 25, 14, 15), key_card_number='KC-205-2234', checked_in_by=user_objs['reception'].id)
            inv1 = Invoice(
                invoice_number='INV-2026-0001', booking_id=b1.id, guest_id=guest_objs[0].id,
                issue_date=date(2026, 10, 25), due_date=date(2026, 10, 30),
                subtotal=955.0, tax_rate=5.0, tax_amount=47.75, discount_amount=90.0,
                total_amount=912.75, paid_amount=912.75, balance_due=0.0, status='Paid'
            )
            db.session.add_all([br1, ci1, inv1])
            db.session.flush()
            ii1 = InvoiceItem(invoice_id=inv1.id, category='Room Charge', description='Luxury Ocean Suite (5 Nights @ $180)', unit_price=180.0, quantity=5, total_price=900.0)
            ii2 = InvoiceItem(invoice_id=inv1.id, category='Restaurant', description='Seafood Platter & Smoothies', unit_price=55.0, quantity=1, total_price=55.0)
            p1 = Payment(payment_reference='PAY-2026-101', invoice_id=inv1.id, booking_id=b1.id, amount=300.0, payment_method='EVC Plus', transaction_reference='EVC-TRX-998811', received_by=user_objs['reception'].id)
            p2 = Payment(payment_reference='PAY-2026-102', invoice_id=inv1.id, booking_id=b1.id, amount=612.75, payment_method='Credit Card', transaction_reference='VISA-AUTH-441029', received_by=user_objs['reception'].id)
            db.session.add_all([ii1, ii2, p1, p2])

            # Booking 2: Confirmed Upcoming
            b2 = Booking(
                booking_reference='BK-2026-002', guest_id=guest_objs[2].id,
                check_in_date=date.today(), check_out_date=date.today(),
                adults=2, children=0, status='Confirmed', booking_source='OTA Booking.com',
                subtotal_amount=330.0, tax_amount=16.5, discount_amount=0.0,
                total_amount=346.5, deposit_amount=100.0, paid_amount=100.0
            )
            db.session.add(b2)
            db.session.flush()
            br2 = BookingRoom(booking_id=b2.id, room_id=room_objs[4].id, price_per_night=110.0, nights=3, subtotal=330.0)
            inv2 = Invoice(
                invoice_number='INV-2026-0002', booking_id=b2.id, guest_id=guest_objs[2].id,
                issue_date=date.today(), due_date=date.today(),
                subtotal=330.0, tax_rate=5.0, tax_amount=16.5, discount_amount=0.0,
                total_amount=346.5, paid_amount=100.0, balance_due=246.5, status='Partially Paid'
            )
            db.session.add_all([br2, inv2])
            db.session.flush()
            ii3 = InvoiceItem(invoice_id=inv2.id, category='Room Charge', description='Double Executive (3 Nights @ $110)', unit_price=110.0, quantity=3, total_price=330.0)
            p3 = Payment(payment_reference='PAY-2026-103', invoice_id=inv2.id, booking_id=b2.id, amount=100.0, payment_method='Zaad', transaction_reference='ZAAD-TX-332910', received_by=user_objs['reception'].id)
            db.session.add_all([ii3, p3])

            # 10. Housekeeping Tasks
            hk1 = HousekeepingTask(room_id=room_objs[2].id, assigned_to=user_objs['housekeeping'].id, status='Dirty', priority='High', cleaning_type='Check-out Deep Clean', notes='Guest checked out, change beddings and sanitize bath')
            hk2 = HousekeepingTask(room_id=room_objs[14].id, assigned_to=user_objs['housekeeping'].id, status='In Progress', priority='High', cleaning_type='Check-out Deep Clean', notes='Linen replaced, floor polishing')
            db.session.add_all([hk1, hk2])

            # 11. Maintenance Tickets
            mt1 = MaintenanceTicket(room_id=room_objs[7].id, reported_by=user_objs['reception'].id, assigned_to=user_objs['admin'].id, issue_title='Room 203 AC Low Cooling', description='Room temperature will not drop below 26C. Coolant recharge required.', priority='High', status='In Progress', estimated_cost=75.0)
            db.session.add(mt1)

            # 12. Restaurant Menu
            cat_bf = MenuCategory(name='Breakfast Specialties', icon='fa-egg', display_order=1)
            cat_main = MenuCategory(name='Gourmet Mains & Steaks', icon='fa-drumstick-bite', display_order=2)
            cat_sea = MenuCategory(name='Fresh Seafood & Grills', icon='fa-fish', display_order=3)
            cat_bev = MenuCategory(name='Beverages & Mocktails', icon='fa-martini-glass', display_order=4)
            db.session.add_all([cat_bf, cat_main, cat_sea, cat_bev])
            db.session.flush()

            m1 = MenuItem(category_id=cat_bf.id, name='Somali Traditional Royal Breakfast', description='Fresh Anjero with spiced liver/beef suqaar, wild organic honey, and aromatic spiced cardamom tea.', price=14.5, preparation_time=15)
            m2 = MenuItem(category_id=cat_main.id, name='Fragrant Goat Meat (Hilib Ari) with Saffron Rice', description='Tender slow-roasted Somali goat with seasoned saffron rice, fried onions, and banana.', price=24.0, preparation_time=20)
            m3 = MenuItem(category_id=cat_sea.id, name='Indian Ocean Jumbo Grilled Lobster', description='Fresh wild catch with garlic butter glaze, lemon zest, and seasoned Mediterranean couscous.', price=45.0, preparation_time=30)
            m4 = MenuItem(category_id=cat_bev.id, name='Fresh Tropical Mango-Passion Smoothie', description='100% natural pureed mango, passion fruit, fresh lime and mint leaves.', price=6.5, preparation_time=8)
            m5 = MenuItem(category_id=cat_bev.id, name='Signature Spiced Somali Shaah Cad', description='Signature spiced milk tea with cinnamon, cloves, cardamom and nutmeg.', price=4.0, preparation_time=5)
            db.session.add_all([m1, m2, m3, m4, m5])

            # 13. Extra Hotel Services
            s1 = HotelService(name='Express Laundry & Dry Cleaning', category='Laundry', price=25.0, unit_type='per bag')
            s2 = HotelService(name='Swedish Full Body Deep Tissue Massage', category='Spa & Wellness', price=80.0, unit_type='60 minutes')
            s3 = HotelService(name='VIP Luxury Airport Suburban Transfer', category='Airport Transport', price=60.0, unit_type='per trip')
            db.session.add_all([s1, s2, s3])

            # 14. Inventory & Suppliers
            sup1 = Supplier(name='Somali Linen & Textile Corp', contact_person='Cumar Shire', phone='+252 61 222 3344', address='KM4 Industrial Zone, Mogadishu')
            sup2 = Supplier(name='Gulf Hospitality Amenities FZE', contact_person='Kareem Mansoor', phone='+971 4 888 1234', address='Jebel Ali, Dubai')
            db.session.add_all([sup1, sup2])
            db.session.flush()

            icat1 = InventoryCategory(name='Housekeeping & Linens', description='Sheets, towels, duvets')
            icat2 = InventoryCategory(name='Guest Toiletries & Amenities', description='Shampoos, soaps, dental kits')
            db.session.add_all([icat1, icat2])
            db.session.flush()

            item1 = InventoryItem(category_id=icat1.id, supplier_id=sup1.id, name='Egyptian Cotton King Bed Sheets (400 TC)', sku='LIN-BED-K400', unit='sets', quantity_in_stock=48.0, min_reorder_level=20.0, unit_cost=35.0)
            item2 = InventoryItem(category_id=icat2.id, supplier_id=sup2.id, name='Luxury Botanical Shampoo 50ml Bottled', sku='TOI-SHMP-50', unit='bottles', quantity_in_stock=320.0, min_reorder_level=100.0, unit_cost=1.20)
            item3 = InventoryItem(category_id=icat1.id, supplier_id=sup1.id, name='Warm White LED Spotlights 7W', sku='MNT-LED-7W', unit='pcs', quantity_in_stock=6.0, min_reorder_level=15.0, unit_cost=4.50)
            db.session.add_all([item1, item2, item3])

            # 15. HR & Shifts
            shift1 = Shift(name='Morning Shift', start_time=time(7, 0), end_time=time(15, 30))
            shift2 = Shift(name='Evening Shift', start_time=time(15, 0), end_time=time(23, 30))
            db.session.add_all([shift1, shift2])
            db.session.flush()

            emp1 = Employee(employee_code='EMP-001', first_name='Ahmed', last_name='Warsame', department='Management', designation='General Manager', phone='+252 61 555 1000', email='admin@grandhorizon.com', shift_id=shift1.id, hire_date=date(2023, 1, 15), basic_salary=3500.0, user_id=user_objs['admin'].id)
            emp2 = Employee(employee_code='EMP-003', first_name='Khadra', last_name='Nuur', department='Front Office', designation='Senior Receptionist', phone='+252 61 555 3000', email='reception@grandhorizon.com', shift_id=shift1.id, hire_date=date(2023, 6, 10), basic_salary=950.0, user_id=user_objs['reception'].id)
            db.session.add_all([emp1, emp2])

            # 16. Expenses & Cash Register
            ecat1 = ExpenseCategory(name='Utilities & Generator Diesel')
            ecat2 = ExpenseCategory(name='Kitchen Provisions')
            db.session.add_all([ecat1, ecat2])
            db.session.flush()

            exp1 = Expense(category_id=ecat1.id, amount=850.0, expense_date=date.today(), description='Diesel fuel for backup 350KVA generator (1,000 Liters)', payment_method='Bank Transfer', recorded_by=user_objs['accountant'].id)
            db.session.add(exp1)

            dcr = DailyCashRegister(register_date=date.today(), opening_cash=500.0, cash_collected=300.0, cash_paid_out=0.0, closing_cash=800.0, status='Open')
            db.session.add(dcr)

            # 17. Reviews
            rev1 = Review(guest_id=guest_objs[0].id, rating=5, title='Exceptional 5-Star Luxury Experience', comment='The Grand Horizon is by far the finest luxury hotel in the region. Impeccable cleanliness, high-speed fiber internet, and delightful Somali cuisine!', is_approved=True)
            db.session.add(rev1)

            # 18. Settings
            settings = [
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
                ('cancellation_days', '2', 'Policies')
            ]
            for k, v, c in settings:
                s = HotelSetting(setting_key=k, setting_value=v, category=c)
                db.session.add(s)

            db.session.commit()
            print("Successfully initialized and seeded Hotel Management System database!")


if __name__ == '__main__':
    seed_database()
    print("\n" + "="*70)
    print(" THE GRAND HORIZON - HOTEL MANAGEMENT SYSTEM (HMS)")
    print(" Python 3.13 + Flask + SQLAlchemy + MySQL/SQLite")
    print("="*70)
    print(" Default Super Admin:  admin      / Admin123!")
    print(" Manager:              manager    / Admin123!")
    print(" Receptionist:         reception  / Admin123!")
    print(" Housekeeping:         clean      / Admin123!")
    print(" Accountant:           accountant / Admin123!")
    print(" Restaurant/POS Staff: pos        / Admin123!")
    print(" Guest Account:        guest1     / Admin123!")
    print("="*70)
    print(" Access URL: http://127.0.0.1:5000")
    print("="*70 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=True)
