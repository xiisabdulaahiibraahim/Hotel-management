from datetime import datetime
from app.models import db

class ExpenseCategory(db.Model):
    __tablename__ = 'expense_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

    expenses = db.relationship('Expense', back_populates='category')

    def __repr__(self):
        return f'<ExpenseCategory {self.name}>'


class Expense(db.Model):
    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('expense_categories.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    expense_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    description = db.Column(db.Text, nullable=False)
    payment_method = db.Column(db.String(50), default='Cash') # Cash, Bank Transfer, Company Card, EVC Plus, Zaad
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    category = db.relationship('ExpenseCategory', back_populates='expenses')
    recorder = db.relationship('User')

    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category.name if self.category else '',
            'amount': self.amount,
            'date': self.expense_date.strftime('%Y-%m-%d'),
            'description': self.description,
            'method': self.payment_method,
            'recorded_by': self.recorder.full_name if self.recorder else 'N/A'
        }

    def __repr__(self):
        return f'<Expense {self.description[:20]} (${self.amount})>'


class DailyCashRegister(db.Model):
    __tablename__ = 'daily_cash_register'

    id = db.Column(db.Integer, primary_key=True)
    register_date = db.Column(db.Date, unique=True, nullable=False, default=datetime.utcnow().date)
    opening_cash = db.Column(db.Float, default=0.0)
    cash_collected = db.Column(db.Float, default=0.0)
    cash_paid_out = db.Column(db.Float, default=0.0)
    closing_cash = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='Open') # Open, Closed
    closed_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)

    cashier = db.relationship('User')

    def __repr__(self):
        return f'<DailyCashRegister {self.register_date} ({self.status})>'
