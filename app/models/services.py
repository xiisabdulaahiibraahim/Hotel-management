from datetime import datetime
from app.models import db

class HotelService(db.Model):
    __tablename__ = 'hotel_services'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    # Laundry, Spa & Wellness, Airport Transport, Tour & Excursion, Minibar
    price = db.Column(db.Float, nullable=False)
    unit_type = db.Column(db.String(50), default='per service')
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    orders = db.relationship('ServiceOrder', back_populates='service')

    def __repr__(self):
        return f'<HotelService {self.name} (${self.price})>'


class ServiceOrder(db.Model):
    __tablename__ = 'service_orders'

    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('hotel_services.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id', ondelete='SET NULL'), nullable=True)
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(30), default='Requested') # Requested, In Progress, Completed, Cancelled
    is_charged_to_folio = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    service = db.relationship('HotelService', back_populates='orders')
    booking = db.relationship('Booking', back_populates='service_orders')
    room = db.relationship('Room')
