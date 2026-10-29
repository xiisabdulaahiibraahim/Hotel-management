from datetime import datetime
from app.models import db

class Shift(db.Model):
    __tablename__ = 'shifts'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    employees = db.relationship('Employee', back_populates='shift')

    def __repr__(self):
        return f'<Shift {self.name}>'


class Employee(db.Model):
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), unique=True, nullable=True)
    employee_code = db.Column(db.String(30), unique=True, nullable=False)
    first_name = db.Column(db.String(60), nullable=False)
    last_name = db.Column(db.String(60), nullable=False)
    department = db.Column(db.String(60), nullable=False) 
    # Front Office, Housekeeping, Maintenance, Kitchen & Food, Accounting, Security, Management
    designation = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    shift_id = db.Column(db.Integer, db.ForeignKey('shifts.id', ondelete='SET NULL'), nullable=True)
    hire_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    basic_salary = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(30), default='Active') # Active, On Leave, Suspended, Terminated

    user = db.relationship('User', back_populates='employee_profile')
    shift = db.relationship('Shift', back_populates='employees')
    attendance_records = db.relationship('Attendance', back_populates='employee', cascade='all, delete-orphan')
    leave_requests = db.relationship('LeaveRequest', back_populates='employee', cascade='all, delete-orphan')

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.employee_code,
            'name': self.full_name,
            'department': self.department,
            'designation': self.designation,
            'phone': self.phone,
            'status': self.status,
            'salary': self.basic_salary
        }

    def __repr__(self):
        return f'<Employee {self.employee_code} - {self.full_name}>'


class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    check_in = db.Column(db.Time, nullable=True)
    check_out = db.Column(db.Time, nullable=True)
    status = db.Column(db.String(30), default='Present') # Present, Late, Absent, On Leave
    notes = db.Column(db.String(255), nullable=True)

    employee = db.relationship('Employee', back_populates='attendance_records')


class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    leave_type = db.Column(db.String(50), nullable=False) # Annual Leave, Sick Leave, Emergency
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default='Pending') # Pending, Approved, Rejected
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    employee = db.relationship('Employee', back_populates='leave_requests')
    reviewer = db.relationship('User')
