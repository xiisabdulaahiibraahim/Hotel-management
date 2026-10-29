from datetime import datetime
from app.models import db

class Guest(db.Model):
    __tablename__ = 'guests'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), unique=True, nullable=True)
    first_name = db.Column(db.String(60), nullable=False)
    last_name = db.Column(db.String(60), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    id_type = db.Column(db.String(40), default='Passport') # Passport, National ID, Driver License
    id_number = db.Column(db.String(60), nullable=False)
    nationality = db.Column(db.String(60), default='Somali')
    address = db.Column(db.Text, nullable=True)
    vip_tier = db.Column(db.String(30), default='Standard') # Standard, Silver, Gold, VIP Platinum
    is_blacklisted = db.Column(db.Boolean, default=False)
    loyalty_points = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text, nullable=True)
    avatar = db.Column(db.String(255), nullable=True)
    id_photo = db.Column(db.String(255), nullable=True) # Passport/ID scan or photo
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', back_populates='guest_profile')
    bookings = db.relationship('Booking', back_populates='guest', lazy=True, order_by='desc(Booking.created_at)')
    invoices = db.relationship('Invoice', back_populates='guest', lazy=True)
    reviews = db.relationship('Review', back_populates='guest', lazy=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'phone': self.phone,
            'id_type': self.id_type,
            'id_number': self.id_number,
            'nationality': self.nationality,
            'vip_tier': self.vip_tier,
            'is_blacklisted': self.is_blacklisted,
            'loyalty_points': self.loyalty_points,
            'total_bookings': len(self.bookings) if self.bookings else 0
        }

    def __repr__(self):
        return f'<Guest {self.full_name} ({self.vip_tier})>'
