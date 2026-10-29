from datetime import datetime
from app.models import db

class MenuCategory(db.Model):
    __tablename__ = 'menu_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    icon = db.Column(db.String(50), default='fa-utensils')
    display_order = db.Column(db.Integer, default=0)

    items = db.relationship('MenuItem', back_populates='category', lazy=True)

    def __repr__(self):
        return f'<MenuCategory {self.name}>'


class MenuItem(db.Model):
    __tablename__ = 'menu_items'

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('menu_categories.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    preparation_time = db.Column(db.Integer, default=15) # minutes
    image_url = db.Column(db.String(255), nullable=True)

    category = db.relationship('MenuCategory', back_populates='items')
    order_items = db.relationship('RestaurantOrderItem', back_populates='menu_item')
    recipe_ingredients = db.relationship('RecipeIngredient', back_populates='menu_item', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category.name if self.category else '',
            'price': self.price,
            'description': self.description,
            'prep_time': self.preparation_time,
            'is_available': self.is_available
        }

    def __repr__(self):
        return f'<MenuItem {self.name} (${self.price})>'


class RestaurantOrder(db.Model):
    __tablename__ = 'restaurant_orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(30), unique=True, nullable=False)
    order_type = db.Column(db.String(30), default='Dine-In') # Dine-In, Room Service, Takeaway
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id', ondelete='SET NULL'), nullable=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='SET NULL'), nullable=True)
    table_number = db.Column(db.String(20), nullable=True)
    customer_name = db.Column(db.String(100), nullable=True)
    customer_phone = db.Column(db.String(50), nullable=True)
    delivery_address = db.Column(db.String(255), nullable=True)
    delivery_rider = db.Column(db.String(100), nullable=True)
    delivery_notes = db.Column(db.Text, nullable=True)
    delivery_image = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(30), default='Pending') 
    # Pending, In Kitchen, Out for Delivery, Delivered, Cancelled
    subtotal = db.Column(db.Float, default=0.0)
    tax_amount = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, default=0.0)
    is_charged_to_room = db.Column(db.Boolean, default=False)
    payment_status = db.Column(db.String(30), default='Pending Payment') # Pending Payment, Paid, Paid (Folio)
    payment_method = db.Column(db.String(50), default='Direct Cash/Card')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    room = db.relationship('Room')
    booking = db.relationship('Booking', back_populates='restaurant_orders')
    waiter = db.relationship('User')
    items = db.relationship('RestaurantOrderItem', back_populates='order', cascade='all, delete-orphan')

    def recalculate(self):
        self.subtotal = sum(i.subtotal for i in self.items)
        self.tax_amount = round(self.subtotal * 0.05, 2)
        self.total_amount = round(self.subtotal + self.tax_amount, 2)

    @property
    def status_badge(self):
        badges = {
            'Pending': 'badge bg-warning text-dark',
            'In Kitchen': 'badge bg-info',
            'Out for Delivery': 'badge bg-primary',
            'Ready': 'badge bg-info',
            'Delivered': 'badge bg-success',
            'Cancelled': 'badge bg-danger'
        }
        return badges.get(self.status, 'badge bg-secondary')

    def __repr__(self):
        return f'<RestaurantOrder {self.order_number} ({self.status})>'


class RestaurantOrderItem(db.Model):
    __tablename__ = 'restaurant_order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('restaurant_orders.id', ondelete='CASCADE'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    special_instructions = db.Column(db.String(255), nullable=True)

    order = db.relationship('RestaurantOrder', back_populates='items')
    menu_item = db.relationship('MenuItem', back_populates='order_items')


class RecipeIngredient(db.Model):
    __tablename__ = 'recipe_ingredients'

    id = db.Column(db.Integer, primary_key=True)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id', ondelete='CASCADE'), nullable=False)
    inventory_item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id', ondelete='CASCADE'), nullable=False)
    quantity_required = db.Column(db.Float, default=1.0) # Quantity of inventory unit per dish portion

    menu_item = db.relationship('MenuItem', back_populates='recipe_ingredients')
    inventory_item = db.relationship('InventoryItem')

    def __repr__(self):
        return f'<RecipeIngredient {self.menu_item_id} -> {self.inventory_item_id}: {self.quantity_required}>'


class TableReservation(db.Model):
    __tablename__ = 'table_reservations'

    id = db.Column(db.Integer, primary_key=True)
    reservation_code = db.Column(db.String(30), unique=True, nullable=False)
    guest_name = db.Column(db.String(100), nullable=False)
    guest_phone = db.Column(db.String(50), nullable=False)
    guest_email = db.Column(db.String(120), nullable=True)
    table_number = db.Column(db.String(30), nullable=False) # e.g. T-01, Lido Ocean 1, VIP Booth A
    reservation_date = db.Column(db.Date, nullable=False)
    reservation_time = db.Column(db.String(20), nullable=False) # e.g. 19:30
    guests_count = db.Column(db.Integer, default=2)
    special_requests = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), default='Confirmed') # Confirmed, Seated, Completed, Cancelled
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', foreign_keys=[created_by])

    @property
    def status_badge(self):
        badges = {
            'Confirmed': 'badge bg-primary text-white',
            'Seated': 'badge bg-success text-white',
            'Completed': 'badge bg-info text-white',
            'Cancelled': 'badge bg-danger text-white'
        }
        return badges.get(self.status, 'badge bg-secondary')

    def __repr__(self):
        return f'<TableReservation {self.reservation_code} Table {self.table_number}>'

