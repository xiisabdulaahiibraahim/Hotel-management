from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, InventoryItem, InventoryCategory, Supplier, StockMovement
from app.utils.helpers import log_audit
from app.utils.decorators import role_required

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

@inventory_bp.route('/')
@login_required
@role_required('Super Admin', 'Manager', 'Housekeeping', 'Receptionist')
def index():
    category_id = request.args.get('category')
    low_stock_only = bool(request.args.get('low_stock'))

    query = InventoryItem.query

    if category_id:
        query = query.filter_by(category_id=int(category_id))
    if low_stock_only:
        query = query.filter(InventoryItem.quantity_in_stock <= InventoryItem.min_reorder_level)

    items = query.order_by(InventoryItem.name.asc()).all()
    categories = InventoryCategory.query.all()
    suppliers = Supplier.query.all()
    recent_movements = StockMovement.query.order_by(StockMovement.created_at.desc()).limit(15).all()

    low_stock_count = sum(1 for i in items if i.is_low_stock)

    return render_template(
        'inventory/index.html',
        items=items,
        categories=categories,
        suppliers=suppliers,
        recent_movements=recent_movements,
        low_stock_count=low_stock_count,
        selected_category=category_id,
        low_stock_only=low_stock_only
    )


@inventory_bp.route('/add-item', methods=['POST'])
@login_required
def add_item():
    name = request.form.get('name', '').strip()
    sku = request.form.get('sku', '').strip()
    category_id = int(request.form.get('category_id'))
    supplier_id = request.form.get('supplier_id')
    unit = request.form.get('unit', 'pcs')
    initial_stock = float(request.form.get('quantity_in_stock', 0.0) or 0.0)
    reorder_level = float(request.form.get('min_reorder_level', 10.0) or 10.0)
    unit_cost = float(request.form.get('unit_cost', 0.0) or 0.0)

    if InventoryItem.query.filter_by(sku=sku).first():
        flash(f'SKU "{sku}" already exists.', 'danger')
        return redirect(url_for('inventory.index'))

    item = InventoryItem(
        name=name,
        sku=sku,
        category_id=category_id,
        supplier_id=int(supplier_id) if supplier_id else None,
        unit=unit,
        quantity_in_stock=initial_stock,
        min_reorder_level=reorder_level,
        unit_cost=unit_cost
    )
    db.session.add(item)
    db.session.flush()

    if initial_stock > 0:
        mov = StockMovement(
            inventory_item_id=item.id,
            movement_type='IN',
            quantity=initial_stock,
            unit_cost=unit_cost,
            reason='Initial Stock Setup',
            recorded_by=current_user.id
        )
        db.session.add(mov)

    db.session.commit()
    log_audit('CREATE_INVENTORY', 'InventoryItem', item.id, f"Created {item.name} ({item.sku})")
    flash(f'Inventory item "{name}" created successfully.', 'success')
    return redirect(url_for('inventory.index'))


@inventory_bp.route('/stock-movement', methods=['POST'])
@login_required
def stock_movement():
    item_id = int(request.form.get('item_id'))
    movement_type = request.form.get('movement_type') # IN, OUT, ADJUSTMENT
    quantity = float(request.form.get('quantity', 0.0) or 0.0)
    reason = request.form.get('reason', '').strip()

    if quantity <= 0:
        flash('Quantity must be greater than zero.', 'danger')
        return redirect(url_for('inventory.index'))

    item = InventoryItem.query.get_or_404(item_id)

    if movement_type == 'OUT' and item.quantity_in_stock < quantity:
        flash(f'Cannot dispense {quantity} {item.unit}. Only {item.quantity_in_stock} available.', 'danger')
        return redirect(url_for('inventory.index'))

    if movement_type == 'IN':
        item.quantity_in_stock += quantity
    elif movement_type == 'OUT':
        item.quantity_in_stock -= quantity
    elif movement_type == 'ADJUSTMENT':
        item.quantity_in_stock = quantity

    movement = StockMovement(
        inventory_item_id=item.id,
        movement_type=movement_type,
        quantity=quantity,
        reason=reason or f'Stock {movement_type}',
        recorded_by=current_user.id
    )
    db.session.add(movement)
    db.session.commit()

    flash(f'Stock updated for {item.name}. New balance: {item.quantity_in_stock} {item.unit}.', 'success')
    return redirect(url_for('inventory.index'))
