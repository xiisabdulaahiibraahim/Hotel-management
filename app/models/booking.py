from datetime import datetime
from app.models import db

class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    booking_reference = db.Column(db.String(30), unique=True, nullable=False)
    guest_id = db.Column(db.Integer, db.ForeignKey('guests.id'), nullable=False)
    check_in_date = db.Column(db.Date, nullable=False)
    check_out_date = db.Column(db.Date, nullable=False)
    adults = db.Column(db.Integer, default=1)
    children = db.Column(db.Integer, default=0)
    status = db.Column(db.String(30), default='Pending')
    # Statuses: Pending, Confirmed, Checked-in, Checked-out, Cancelled, No-show
    booking_source = db.Column(db.String(50), default='Walk-in')
    # Walk-in, Phone, Website, OTA Booking.com, OTA Expedia
    promotion_id = db.Column(db.Integer, db.ForeignKey('promotions.id', ondelete='SET NULL'), nullable=True)
    special_requests = db.Column(db.Text, nullable=True)
    subtotal_amount = db.Column(db.Float, default=0.0)
    tax_amount = db.Column(db.Float, default=0.0)
    discount_amount = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, default=0.0)
    deposit_amount = db.Column(db.Float, default=0.0)
    paid_amount = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    guest = db.relationship('Guest', back_populates='bookings')
    promotion = db.relationship('Promotion', back_populates='bookings')
    booking_rooms = db.relationship('BookingRoom', back_populates='booking', cascade='all, delete-orphan')
    checkin_record = db.relationship('CheckinRecord', back_populates='booking', uselist=False, cascade='all, delete-orphan')
    invoices = db.relationship('Invoice', back_populates='booking', cascade='all, delete-orphan')
    payments = db.relationship('Payment', back_populates='booking', cascade='all, delete-orphan')
    service_orders = db.relationship('ServiceOrder', back_populates='booking')
    restaurant_orders = db.relationship('RestaurantOrder', back_populates='booking')

    @property
    def nights_count(self):
        if self.check_in_date and self.check_out_date:
            delta = (self.check_out_date - self.check_in_date).days
            return max(delta, 1)
        return 1

    @property
    def balance_due(self):
        return max(self.total_amount - self.paid_amount, 0.0)

    @property
    def status_badge(self):
        badges = {
            'Confirmed': 'badge bg-success',
            'Checked-in': 'badge bg-primary',
            'Checked-out': 'badge bg-secondary',
            'Pending': 'badge bg-warning text-dark',
            'Cancelled': 'badge bg-danger',
            'No-show': 'badge bg-dark'
        }
        return badges.get(self.status, 'badge bg-info')

    def to_dict(self):
        return {
            'id': self.id,
            'booking_reference': self.booking_reference,
            'guest_name': self.guest.full_name if self.guest else 'Unknown',
            'check_in': self.check_in_date.strftime('%Y-%m-%d'),
            'check_out': self.check_out_date.strftime('%Y-%m-%d'),
            'nights': self.nights_count,
            'status': self.status,
            'status_badge': self.status_badge,
            'booking_source': self.booking_source,
            'total_amount': self.total_amount,
            'paid_amount': self.paid_amount,
            'balance_due': self.balance_due,
            'rooms': [br.room.room_number for br in self.booking_rooms if br.room]
        }

    def __repr__(self):
        return f'<Booking {self.booking_reference} ({self.status})>'


class BookingRoom(db.Model):
    __tablename__ = 'booking_rooms'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    price_per_night = db.Column(db.Float, nullable=False)
    nights = db.Column(db.Integer, default=1)
    subtotal = db.Column(db.Float, nullable=False)

    booking = db.relationship('Booking', back_populates='booking_rooms')
    room = db.relationship('Room', back_populates='booking_rooms')


class CheckinRecord(db.Model):
    __tablename__ = 'checkin_records'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='CASCADE'), unique=True, nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    actual_check_in = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    actual_check_out = db.Column(db.DateTime, nullable=True)
    key_card_number = db.Column(db.String(50), nullable=True)
    id_verified = db.Column(db.Boolean, default=True)
    early_checkin_fee = db.Column(db.Float, default=0.0)
    late_checkout_fee = db.Column(db.Float, default=0.0)
    deposit_collected = db.Column(db.Float, default=0.0)
    deposit_refunded = db.Column(db.Float, default=0.0)
    deposit_status = db.Column(db.String(30), default='None') # None, Held, Refunded, Applied to Folio
    checked_in_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    checked_out_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    booking = db.relationship('Booking', back_populates='checkin_record')
    room = db.relationship('Room')
    staff_checkin = db.relationship('User', foreign_keys=[checked_in_by])
    staff_checkout = db.relationship('User', foreign_keys=[checked_out_by])
