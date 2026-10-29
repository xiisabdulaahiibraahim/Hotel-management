from datetime import datetime
from app.models import db

class HousekeepingTask(db.Model):
    __tablename__ = 'housekeeping_tasks'

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id', ondelete='CASCADE'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    status = db.Column(db.String(30), default='Dirty') 
    # Dirty, In Progress, Clean, Inspected
    priority = db.Column(db.String(20), default='Medium') # Low, Medium, High, Urgent
    cleaning_type = db.Column(db.String(50), default='Check-out Deep Clean') 
    # Daily Tidy, Check-out Deep Clean, Disinfection, Turn Down
    notes = db.Column(db.Text, nullable=True)
    inspection_notes = db.Column(db.Text, nullable=True)
    inspected_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    room = db.relationship('Room', back_populates='housekeeping_tasks')
    cleaner = db.relationship('User', foreign_keys=[assigned_to])
    inspector = db.relationship('User', foreign_keys=[inspected_by])

    @property
    def status_badge(self):
        badges = {
            'Dirty': 'badge bg-danger',
            'In Progress': 'badge bg-warning text-dark',
            'Clean': 'badge bg-info',
            'Inspected': 'badge bg-success'
        }
        return badges.get(self.status, 'badge bg-secondary')

    def to_dict(self):
        return {
            'id': self.id,
            'room_number': self.room.room_number if self.room else 'N/A',
            'cleaner': self.cleaner.full_name if self.cleaner else 'Unassigned',
            'status': self.status,
            'status_badge': self.status_badge,
            'priority': self.priority,
            'cleaning_type': self.cleaning_type,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M')
        }

    def __repr__(self):
        return f'<HousekeepingTask Room {self.room.room_number if self.room else "?"} ({self.status})>'


class LostAndFound(db.Model):
    __tablename__ = 'lost_and_found'

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id', ondelete='SET NULL'), nullable=True)
    item_name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(50), default='Electronics')
    description = db.Column(db.Text, nullable=True)
    found_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    found_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    storage_location = db.Column(db.String(100), default='Main Safe')
    status = db.Column(db.String(30), default='Found') # Found, Claimed, Donated, Disposed
    claimant_name = db.Column(db.String(100), nullable=True)
    claimant_phone = db.Column(db.String(50), nullable=True)
    claimed_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    room = db.relationship('Room')
    finder = db.relationship('User')

    def __repr__(self):
        return f'<LostAndFound {self.item_name} ({self.status})>'
