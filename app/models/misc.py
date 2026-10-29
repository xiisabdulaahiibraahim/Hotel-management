from datetime import datetime
from app.models import db

class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='SET NULL'), nullable=True)
    guest_id = db.Column(db.Integer, db.ForeignKey('guests.id', ondelete='CASCADE'), nullable=False)
    rating = db.Column(db.Integer, nullable=False) # 1 - 5
    title = db.Column(db.String(120), nullable=True)
    comment = db.Column(db.Text, nullable=False)
    is_approved = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    guest = db.relationship('Guest', back_populates='reviews')

    def __repr__(self):
        return f'<Review {self.rating}* by {self.guest.full_name if self.guest else "Anon"}>'


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default='info') # info, success, warning, danger
    is_read = db.Column(db.Boolean, default=False)
    link = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'type': self.type,
            'is_read': self.is_read,
            'link': self.link,
            'time_ago': self.created_at.strftime('%H:%M %b %d')
        }

    def __repr__(self):
        return f'<Notification {self.title}>'


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    entity_name = db.Column(db.String(80), nullable=False)
    entity_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User')

    def __repr__(self):
        return f'<AuditLog {self.action} on {self.entity_name}:{self.entity_id}>'


class HotelSetting(db.Model):
    __tablename__ = 'hotel_settings'

    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(80), unique=True, nullable=False)
    setting_value = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default='General')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get_value(cls, key, default=None):
        setting = cls.query.filter_by(setting_key=key).first()
        return setting.setting_value if setting else default

    @classmethod
    def get_all_as_dict(cls):
        settings = cls.query.all()
        return {s.setting_key: s.setting_value for s in settings}

    @classmethod
    def set_value(cls, key, value, category='General'):
        setting = cls.query.filter_by(setting_key=key).first()
        if setting:
            setting.setting_value = str(value)
            setting.category = category
        else:
            setting = cls(setting_key=key, setting_value=str(value), category=category)
            db.session.add(setting)
        db.session.commit()
        return setting

    def __repr__(self):
        return f'<HotelSetting {self.setting_key}={self.setting_value}>'


class CommunicationLog(db.Model):
    __tablename__ = 'communication_logs'

    id = db.Column(db.Integer, primary_key=True)
    channel = db.Column(db.String(20), default='WhatsApp') # WhatsApp, SMS, Email
    recipient_name = db.Column(db.String(100), nullable=False)
    recipient_phone = db.Column(db.String(50), nullable=False)
    template_type = db.Column(db.String(50), default='General') # Booking Confirmation, Check-in Key, Folio Receipt, Table Booking
    message_content = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default='Sent') # Sent, Delivered, Pending
    sent_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sent_by])

    def __repr__(self):
        return f'<CommunicationLog {self.channel} to {self.recipient_phone}>'
