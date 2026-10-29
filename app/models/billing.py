from datetime import datetime
from app.models import db

class Invoice(db.Model):
    __tablename__ = 'invoices'

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(40), unique=True, nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False)
    guest_id = db.Column(db.Integer, db.ForeignKey('guests.id'), nullable=False)
    issue_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    due_date = db.Column(db.Date, nullable=False)
    subtotal = db.Column(db.Float, default=0.0)
    tax_rate = db.Column(db.Float, default=5.0)
    tax_amount = db.Column(db.Float, default=0.0)
    discount_amount = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, default=0.0)
    paid_amount = db.Column(db.Float, default=0.0)
    balance_due = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(30), default='Unpaid')
    # Statuses: Draft, Unpaid, Partially Paid, Paid, Refunded, Void
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    booking = db.relationship('Booking', back_populates='invoices')
    guest = db.relationship('Guest', back_populates='invoices')
    items = db.relationship('InvoiceItem', back_populates='invoice', cascade='all, delete-orphan')
    payments = db.relationship('Payment', back_populates='invoice', cascade='all, delete-orphan')

    def recalculate(self):
        self.subtotal = sum(item.total_price for item in self.items)
        self.tax_amount = round((self.subtotal * (self.tax_rate / 100.0)), 2)
        self.total_amount = round(self.subtotal + self.tax_amount - self.discount_amount, 2)
        self.paid_amount = sum(p.amount for p in self.payments if p.status == 'Completed')
        self.balance_due = max(round(self.total_amount - self.paid_amount, 2), 0.0)

        if self.paid_amount >= self.total_amount and self.total_amount > 0:
            self.status = 'Paid'
        elif self.paid_amount > 0:
            self.status = 'Partially Paid'
        else:
            self.status = 'Unpaid'

    @property
    def status_badge(self):
        badges = {
            'Paid': 'badge bg-success',
            'Partially Paid': 'badge bg-warning text-dark',
            'Unpaid': 'badge bg-danger',
            'Draft': 'badge bg-secondary',
            'Refunded': 'badge bg-info',
            'Void': 'badge bg-dark'
        }
        return badges.get(self.status, 'badge bg-secondary')

    def to_dict(self):
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'booking_ref': self.booking.booking_reference if self.booking else 'N/A',
            'guest_name': self.guest.full_name if self.guest else 'N/A',
            'issue_date': self.issue_date.strftime('%Y-%m-%d'),
            'total_amount': self.total_amount,
            'paid_amount': self.paid_amount,
            'balance_due': self.balance_due,
            'status': self.status,
            'status_badge': self.status_badge
        }

    def __repr__(self):
        return f'<Invoice {self.invoice_number} (${self.total_amount})>'


class InvoiceItem(db.Model):
    __tablename__ = 'invoice_items'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False)
    category = db.Column(db.String(50), default='Room Charge') 
    # Room Charge, Restaurant, Laundry, Spa, Minibar, Airport Transfer, Other Fee
    description = db.Column(db.String(255), nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, default=1)
    total_price = db.Column(db.Float, nullable=False)
    date_incurred = db.Column(db.Date, default=datetime.utcnow().date)

    invoice = db.relationship('Invoice', back_populates='items')


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    payment_reference = db.Column(db.String(50), unique=True, nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    # Payment methods: Cash, Credit Card, EVC Plus, Zaad, Sahal, Bank Transfer
    transaction_reference = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(30), default='Completed') # Completed, Pending, Failed, Refunded
    received_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)

    invoice = db.relationship('Invoice', back_populates='payments')
    booking = db.relationship('Booking', back_populates='payments')
    staff = db.relationship('User')

    def to_dict(self):
        return {
            'id': self.id,
            'reference': self.payment_reference,
            'amount': self.amount,
            'method': self.payment_method,
            'status': self.status,
            'date': self.payment_date.strftime('%Y-%m-%d %H:%M')
        }

    def __repr__(self):
        return f'<Payment {self.payment_reference} (${self.amount})>'


class NightAuditRecord(db.Model):
    __tablename__ = 'night_audit_records'

    id = db.Column(db.Integer, primary_key=True)
    audit_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    performed_at = db.Column(db.DateTime, default=datetime.utcnow)
    performed_by_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    occupied_rooms_count = db.Column(db.Integer, default=0)
    total_rooms_count = db.Column(db.Integer, default=0)
    occupancy_rate = db.Column(db.Float, default=0.0)
    room_charges_posted = db.Column(db.Float, default=0.0)
    restaurant_sales = db.Column(db.Float, default=0.0)
    service_sales = db.Column(db.Float, default=0.0)
    total_revenue = db.Column(db.Float, default=0.0)
    payments_collected = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text, nullable=True)

    performed_by = db.relationship('User')

    def __repr__(self):
        return f'<NightAuditRecord {self.audit_date} (${self.total_revenue})>'

