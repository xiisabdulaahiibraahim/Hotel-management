from datetime import datetime
from app.models import db

class MaintenanceTicket(db.Model):
    __tablename__ = 'maintenance_tickets'

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id', ondelete='SET NULL'), nullable=True)
    reported_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    issue_title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default='Medium') # Low, Medium, High, Emergency
    status = db.Column(db.String(30), default='Open') # Open, In Progress, Resolved, Closed
    estimated_cost = db.Column(db.Float, default=0.0)
    actual_cost = db.Column(db.Float, default=0.0)
    resolution_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

    room = db.relationship('Room', back_populates='maintenance_tickets')
    reporter = db.relationship('User', foreign_keys=[reported_by])
    technician = db.relationship('User', foreign_keys=[assigned_to])

    @property
    def status_badge(self):
        badges = {
            'Open': 'badge bg-danger',
            'In Progress': 'badge bg-warning text-dark',
            'Resolved': 'badge bg-success',
            'Closed': 'badge bg-secondary'
        }
        return badges.get(self.status, 'badge bg-info')

    @property
    def priority_badge(self):
        badges = {
            'Emergency': 'badge bg-danger',
            'High': 'badge bg-warning text-dark',
            'Medium': 'badge bg-primary',
            'Low': 'badge bg-info'
        }
        return badges.get(self.priority, 'badge bg-secondary')

    def to_dict(self):
        return {
            'id': self.id,
            'room_number': self.room.room_number if self.room else 'General Hotel Facility',
            'issue_title': self.issue_title,
            'priority': self.priority,
            'status': self.status,
            'reporter': self.reporter.full_name if self.reporter else 'N/A',
            'technician': self.technician.full_name if self.technician else 'Unassigned',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M')
        }

    def __repr__(self):
        return f'<MaintenanceTicket {self.issue_title} ({self.status})>'
