from datetime import datetime
from app.models import db

class Supplier(db.Model):
    __tablename__ = 'suppliers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    contact_person = db.Column(db.String(80), nullable=True)
    phone = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.Text, nullable=True)

    items = db.relationship('InventoryItem', back_populates='supplier')

    def __repr__(self):
        return f'<Supplier {self.name}>'


class InventoryCategory(db.Model):
    __tablename__ = 'inventory_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

    items = db.relationship('InventoryItem', back_populates='category')

    def __repr__(self):
        return f'<InventoryCategory {self.name}>'


class InventoryItem(db.Model):
    __tablename__ = 'inventory_items'

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('inventory_categories.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id', ondelete='SET NULL'), nullable=True)
    name = db.Column(db.String(120), nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    unit = db.Column(db.String(30), default='pcs')
    quantity_in_stock = db.Column(db.Float, default=0.0)
    min_reorder_level = db.Column(db.Float, default=10.0)
    unit_cost = db.Column(db.Float, default=0.0)

    category = db.relationship('InventoryCategory', back_populates='items')
    supplier = db.relationship('Supplier', back_populates='items')
    movements = db.relationship('StockMovement', back_populates='item', cascade='all, delete-orphan')

    @property
    def is_low_stock(self):
        return self.quantity_in_stock <= self.min_reorder_level

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'sku': self.sku,
            'category': self.category.name if self.category else '',
            'stock': self.quantity_in_stock,
            'unit': self.unit,
            'unit_cost': self.unit_cost,
            'is_low_stock': self.is_low_stock
        }

    def __repr__(self):
        return f'<InventoryItem {self.name} ({self.quantity_in_stock} {self.unit})>'


class StockMovement(db.Model):
    __tablename__ = 'stock_movements'

    id = db.Column(db.Integer, primary_key=True)
    inventory_item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id', ondelete='CASCADE'), nullable=False)
    movement_type = db.Column(db.String(20), nullable=False) # IN, OUT, ADJUSTMENT
    quantity = db.Column(db.Float, nullable=False)
    unit_cost = db.Column(db.Float, nullable=True)
    reason = db.Column(db.String(255), nullable=False)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    item = db.relationship('InventoryItem', back_populates='movements')
    user = db.relationship('User')
