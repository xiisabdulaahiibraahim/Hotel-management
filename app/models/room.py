from datetime import datetime
from app.models import db

class Amenity(db.Model):
    __tablename__ = 'amenities'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    icon = db.Column(db.String(60), default='fa-check')
    category = db.Column(db.String(50), default='General')

    room_types = db.relationship('RoomType', secondary='room_amenities', back_populates='amenities')

    def __repr__(self):
        return f'<Amenity {self.name}>'


class RoomAmenity(db.Model):
    __tablename__ = 'room_amenities'

    room_type_id = db.Column(db.Integer, db.ForeignKey('room_types.id', ondelete='CASCADE'), primary_key=True)
    amenity_id = db.Column(db.Integer, db.ForeignKey('amenities.id', ondelete='CASCADE'), primary_key=True)


class RoomType(db.Model):
    __tablename__ = 'room_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    slug = db.Column(db.String(60), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    base_price = db.Column(db.Float, nullable=False)
    weekend_price = db.Column(db.Float, nullable=False)
    capacity_adults = db.Column(db.Integer, default=2)
    capacity_children = db.Column(db.Integer, default=1)
    bed_type = db.Column(db.String(50), default='1 King Bed')
    size_sqm = db.Column(db.Integer, default=35)
    primary_image = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    rooms = db.relationship('Room', back_populates='room_type', lazy=True)
    amenities = db.relationship('Amenity', secondary='room_amenities', back_populates='room_types')
    images = db.relationship('RoomImage', back_populates='room_type', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'base_price': self.base_price,
            'weekend_price': self.weekend_price,
            'capacity_adults': self.capacity_adults,
            'capacity_children': self.capacity_children,
            'bed_type': self.bed_type,
            'size_sqm': self.size_sqm,
            'primary_image': self.primary_image,
            'amenities': [a.name for a in self.amenities],
            'total_rooms': len(self.rooms) if self.rooms else 0,
            'available_rooms': sum(1 for r in self.rooms if r.status == 'Available') if self.rooms else 0
        }

    def __repr__(self):
        return f'<RoomType {self.name} (${self.base_price})>'


class Room(db.Model):
    __tablename__ = 'rooms'

    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(20), unique=True, nullable=False)
    floor = db.Column(db.Integer, nullable=False, default=1)
    room_type_id = db.Column(db.Integer, db.ForeignKey('room_types.id'), nullable=False)
    status = db.Column(db.String(30), default='Available') 
    # Statuses: Available, Occupied, Reserved, Cleaning, Maintenance, Out of Order
    clean_status = db.Column(db.String(30), default='Clean') 
    # Clean, Dirty, In Progress, Inspected
    key_card_code = db.Column(db.String(50), nullable=True)
    is_smoking = db.Column(db.Boolean, default=False)
    image = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    room_type = db.relationship('RoomType', back_populates='rooms')
    booking_rooms = db.relationship('BookingRoom', back_populates='room', lazy=True)
    housekeeping_tasks = db.relationship('HousekeepingTask', back_populates='room', lazy=True)
    maintenance_tickets = db.relationship('MaintenanceTicket', back_populates='room', lazy=True)

    @property
    def status_badge_class(self):
        badges = {
            'Available': 'bg-success',
            'Occupied': 'bg-danger',
            'Reserved': 'bg-primary',
            'Cleaning': 'bg-warning text-dark',
            'Maintenance': 'bg-secondary',
            'Out of Order': 'bg-dark'
        }
        return badges.get(self.status, 'bg-secondary')

    @property
    def display_image(self):
        if self.image:
            return self.image
        if self.room_type and self.room_type.primary_image:
            return self.room_type.primary_image
        return '/static/img/room_default.jpg'

    def to_dict(self):
        return {
            'id': self.id,
            'room_number': self.room_number,
            'floor': self.floor,
            'type_name': self.room_type.name if self.room_type else None,
            'base_price': self.room_type.base_price if self.room_type else 0.0,
            'status': self.status,
            'clean_status': self.clean_status,
            'status_class': self.status_badge_class,
            'key_card_code': self.key_card_code,
            'image': self.display_image,
            'notes': self.notes
        }

    def __repr__(self):
        return f'<Room {self.room_number} ({self.status})>'


class RoomImage(db.Model):
    __tablename__ = 'room_images'

    id = db.Column(db.Integer, primary_key=True)
    room_type_id = db.Column(db.Integer, db.ForeignKey('room_types.id', ondelete='CASCADE'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    caption = db.Column(db.String(100), nullable=True)
    is_cover = db.Column(db.Boolean, default=False)

    room_type = db.relationship('RoomType', back_populates='images')


class Promotion(db.Model):
    __tablename__ = 'promotions'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    discount_type = db.Column(db.String(20), default='percentage') # percentage or fixed
    discount_value = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    min_spend = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)

    bookings = db.relationship('Booking', back_populates='promotion')

    def __repr__(self):
        return f'<Promotion {self.code} ({self.discount_value})>'
