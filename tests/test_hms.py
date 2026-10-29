import unittest
from datetime import date, timedelta
from app import create_app
from app.models import db, User, Role, Room, RoomType, Booking, Invoice, Payment, HousekeepingTask
from app.services.booking_service import search_available_rooms, create_booking_transaction
from app.services.billing_service import process_folio_payment

class HMSTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()

        with self.app.app_context():
            from run import seed_database
            seed_database()

    def test_admin_authentication(self):
        with self.app.app_context():
            admin = User.query.filter_by(username='admin').first()
            self.assertIsNotNone(admin)
            self.assertTrue(admin.check_password('Admin123!'))
            self.assertTrue(admin.has_role('Super Admin'))

    def test_room_search_availability(self):
        with self.app.app_context():
            today = date.today()
            check_out = today + timedelta(days=2)
            avail_rooms = search_available_rooms(today, check_out, adults=1)
            self.assertGreater(len(avail_rooms), 0)

    def test_create_booking_and_folio(self):
        with self.app.app_context():
            avail_rooms = Room.query.filter_by(status='Available').all()
            self.assertGreater(len(avail_rooms), 0)
            target_room = avail_rooms[0]

            check_in = date.today() + timedelta(days=10)
            check_out = date.today() + timedelta(days=13)

            booking, invoice = create_booking_transaction(
                guest_id=1,
                room_ids=[target_room.id],
                check_in_date=check_in,
                check_out_date=check_out,
                adults=1,
                booking_source='Website',
                deposit_amount=50.0
            )

            self.assertIsNotNone(booking.id)
            self.assertEqual(booking.status, 'Confirmed')
            self.assertIsNotNone(invoice)
            self.assertEqual(invoice.paid_amount, 50.0)

    def test_payment_processing(self):
        with self.app.app_context():
            inv = Invoice.query.first()
            self.assertIsNotNone(inv)
            initial_balance = inv.balance_due

            if initial_balance > 0:
                payment = process_folio_payment(
                    invoice_id=inv.id,
                    amount=min(initial_balance, 100.0),
                    payment_method='EVC Plus',
                    tx_ref='TEST-EVC-123'
                )
                self.assertIsNotNone(payment.id)
                self.assertLess(inv.balance_due, initial_balance)

if __name__ == '__main__':
    unittest.main()
