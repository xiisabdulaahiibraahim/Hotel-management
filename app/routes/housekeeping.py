from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from app.models import (
    db, HousekeepingTask, Room, User, LostAndFound, 
    Booking, HotelService, ServiceOrder, Invoice
)
from app.services.billing_service import add_item_to_folio
from app.utils.helpers import log_audit, send_notification
from app.utils.decorators import role_required

housekeeping_bp = Blueprint('housekeeping', __name__, url_prefix='/housekeeping')

@housekeeping_bp.route('/')
@login_required
@role_required('Super Admin', 'Manager', 'Housekeeping', 'Receptionist')
def index():
    status = request.args.get('status')
    query = HousekeepingTask.query

    if status:
        query = query.filter_by(status=status)

    tasks = query.order_by(HousekeepingTask.created_at.desc()).all()
    cleaners = User.query.join(User.role).filter(User.role.has(name='Housekeeping')).all()
    if not cleaners:
        cleaners = User.query.filter(User.is_active == True).all()

    rooms_need_clean = Room.query.filter(Room.status.in_(['Cleaning']) | (Room.clean_status.in_(['Dirty', 'In Progress']))).all()
    lost_items = LostAndFound.query.order_by(LostAndFound.created_at.desc()).limit(10).all()

    return render_template(
        'housekeeping/index.html',
        tasks=tasks,
        cleaners=cleaners,
        rooms_need_clean=rooms_need_clean,
        lost_items=lost_items,
        selected_status=status
    )


@housekeeping_bp.route('/task/<int:task_id>/update-status', methods=['POST'])
@login_required
def update_task_status(task_id):
    task = HousekeepingTask.query.get_or_404(task_id)
    new_status = request.form.get('status')

    task.status = new_status
    if new_status == 'In Progress':
        task.started_at = datetime.utcnow()
        task.room.clean_status = 'In Progress'
    elif new_status == 'Clean':
        task.completed_at = datetime.utcnow()
        task.room.clean_status = 'Clean'
    elif new_status == 'Inspected':
        task.inspected_by = current_user.id
        task.room.clean_status = 'Clean'
        # If room was in Cleaning state, transition to Available!
        if task.room.status == 'Cleaning':
            task.room.status = 'Available'

    db.session.commit()
    log_audit('HOUSEKEEPING_UPDATE', 'HousekeepingTask', task.id, f"Room {task.room.room_number} status -> {new_status}")
    flash(f"Room {task.room.room_number} housekeeping updated to {new_status}.", 'success')
    return redirect(url_for('housekeeping.index'))


@housekeeping_bp.route('/create-task', methods=['POST'])
@login_required
def create_task():
    room_id = int(request.form.get('room_id'))
    cleaner_id = request.form.get('assigned_to')
    priority = request.form.get('priority', 'Medium')
    cleaning_type = request.form.get('cleaning_type', 'Daily Tidy')
    notes = request.form.get('notes', '').strip()

    task = HousekeepingTask(
        room_id=room_id,
        assigned_to=int(cleaner_id) if cleaner_id else None,
        status='Dirty',
        priority=priority,
        cleaning_type=cleaning_type,
        notes=notes
    )
    db.session.add(task)
    db.session.commit()
    flash('Housekeeping task created and assigned.', 'success')
    return redirect(url_for('housekeeping.index'))


@housekeeping_bp.route('/lost-and-found/add', methods=['POST'])
@login_required
def add_lost_item():
    room_id = request.form.get('room_id')
    item_name = request.form.get('item_name', '').strip()
    category = request.form.get('category', 'Electronics')
    description = request.form.get('description', '').strip()
    location = request.form.get('storage_location', 'Main Safe').strip()

    item = LostAndFound(
        room_id=int(room_id) if room_id else None,
        item_name=item_name,
        category=category,
        description=description,
        found_by=current_user.id,
        storage_location=location,
        status='Found'
    )
    db.session.add(item)
    db.session.commit()
    flash(f'Lost item "{item_name}" registered.', 'info')
    return redirect(url_for('housekeeping.index'))


@housekeeping_bp.route('/lost-and-found/<int:item_id>/claim', methods=['POST'])
@login_required
def claim_lost_item(item_id):
    item = LostAndFound.query.get_or_404(item_id)
    item.claimant_name = request.form.get('claimant_name', '').strip()
    item.claimant_phone = request.form.get('claimant_phone', '').strip()
    item.claimed_date = datetime.utcnow().date()
    item.status = 'Claimed'

    db.session.commit()
    flash(f'Item "{item.item_name}" marked as claimed by {item.claimant_name}.', 'success')
    return redirect(url_for('housekeeping.index'))


# ============================================================
# GUEST LAUNDRY SERVICE & VALET OPERATIONS
# ============================================================

def seed_default_laundry_services():
    default_items = [
        ("Men's / Women's Shirt (Wash & Iron)", 2.50, "per piece", "Thorough laundering, steam pressing and hanger delivery."),
        ("Trousers / Jeans (Wash & Iron)", 3.00, "per piece", "Stain removal, crease ironing and protective bag packaging."),
        ("Full Suit 2-Piece (Dry Clean & Press)", 8.50, "per set", "Professional dry cleaning with gentle garment care."),
        ("Somali Khamiis / Dirac / Garbasaar", 4.00, "per piece", "Traditional delicate fabric washing, fragrance and gentle press."),
        ("Express Iron / Steam Press Only", 1.50, "per piece", "Immediate steam ironing without wash service."),
        ("Bedding / Blankets Extra Wash", 3.50, "per piece", "Heavy linen hygiene wash and sanitization.")
    ]
    for name, price, unit, desc in default_items:
        exists = HotelService.query.filter_by(name=name, category='Laundry').first()
        if not exists:
            svc = HotelService(
                name=name,
                category='Laundry',
                price=price,
                unit_type=unit,
                description=desc,
                is_active=True
            )
            db.session.add(svc)
    db.session.commit()


@housekeeping_bp.route('/laundry')
@login_required
@role_required('Super Admin', 'Manager', 'Housekeeping', 'Receptionist')
def laundry_hub():
    # Ensure default catalog exists
    if HotelService.query.filter_by(category='Laundry').count() == 0:
        seed_default_laundry_services()

    status_filter = request.args.get('status')
    query = ServiceOrder.query.join(HotelService).filter(HotelService.category == 'Laundry')
    if status_filter:
        query = query.filter(ServiceOrder.status == status_filter)

    orders = query.order_by(ServiceOrder.created_at.desc()).all()
    services = HotelService.query.filter_by(category='Laundry', is_active=True).all()
    in_house = Booking.query.filter_by(status='Checked-in').all()

    # Metrics
    total_orders = len(orders)
    in_wash = sum(1 for o in orders if o.status in ['Requested', 'In Progress'])
    ready_count = sum(1 for o in orders if o.status == 'Ready')
    delivered_count = sum(1 for o in orders if o.status == 'Delivered')
    total_revenue = sum(o.total_amount for o in orders if o.status != 'Cancelled')

    return render_template(
        'housekeeping/laundry.html',
        orders=orders,
        services=services,
        in_house=in_house,
        status_filter=status_filter,
        total_orders=total_orders,
        in_wash=in_wash,
        ready_count=ready_count,
        delivered_count=delivered_count,
        total_revenue=total_revenue
    )


@housekeeping_bp.route('/laundry/create', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager', 'Housekeeping', 'Receptionist')
def create_laundry_order():
    booking_id = request.form.get('booking_id', type=int)
    service_id = request.form.get('service_id', type=int)
    quantity = max(request.form.get('quantity', 1, type=int), 1)
    notes = request.form.get('notes', '').strip()
    charge_folio = request.form.get('charge_folio') == 'on'

    booking = Booking.query.get_or_404(booking_id)
    service = HotelService.query.get_or_404(service_id)

    room = None
    if booking.checkin_record and booking.checkin_record.room:
        room = booking.checkin_record.room
    elif booking.booking_rooms:
        room = booking.booking_rooms[0].room

    total_amount = round(service.price * quantity, 2)

    order = ServiceOrder(
        service_id=service.id,
        booking_id=booking.id,
        room_id=room.id if room else None,
        quantity=quantity,
        unit_price=service.price,
        total_amount=total_amount,
        status='Requested',
        is_charged_to_folio=charge_folio,
        notes=notes
    )
    db.session.add(order)
    db.session.flush()

    room_str = f"Room {room.room_number}" if room else "In-House Suite"

    # Automatically charge to Room Folio if selected
    if charge_folio:
        inv = Invoice.query.filter_by(booking_id=booking.id).first()
        if inv:
            add_item_to_folio(
                invoice_id=inv.id,
                category='Laundry',
                description=f"Valet Laundry ({quantity}x {service.name}) - {room_str}",
                unit_price=service.price,
                quantity=quantity
            )

    db.session.commit()
    log_audit('CREATE_LAUNDRY_ORDER', 'ServiceOrder', order.id, f"Created Laundry Order for {booking.guest.full_name} ({room_str}): {quantity}x {service.name} (${total_amount:,.2f})")
    send_notification(
        user_id=None,
        title=f"Dalab Dhaqid Dhaar ah ({room_str})",
        message=f"Waxaa la diiwaangeliyay dalab dhar-dhaqid ah oo ka yimid {room_str} ({booking.guest.full_name}): {quantity}x {service.name}.",
        notif_type='info',
        link="/housekeeping/laundry"
    )

    flash(f"Dalabka dharka ({room_str} - {quantity}x {service.name}) si guul leh ayaa loo diiwaangeliyay!", 'success')
    return redirect(url_for('housekeeping.laundry_hub'))


@housekeeping_bp.route('/laundry/<int:order_id>/update-status', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager', 'Housekeeping', 'Receptionist')
def update_laundry_status(order_id):
    order = ServiceOrder.query.get_or_404(order_id)
    new_status = request.form.get('status', order.status)
    order.status = new_status
    db.session.commit()

    log_audit('UPDATE_LAUNDRY_STATUS', 'ServiceOrder', order.id, f"Updated Laundry #{order.id} status to {new_status}")
    flash(f"Xaaladda dalabka dharka #{order.id} waxaa loo beddelay: {new_status}", 'success')
    return redirect(request.referrer or url_for('housekeeping.laundry_hub'))


@housekeeping_bp.route('/laundry/<int:order_id>/delete', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager')
def delete_laundry_order(order_id):
    order = ServiceOrder.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    log_audit('DELETE_LAUNDRY_ORDER', 'ServiceOrder', order_id, f"Deleted Laundry Order #{order_id}")
    flash(f"Dalabka dharka #{order_id} waa la tirtiray.", 'warning')
    return redirect(url_for('housekeeping.laundry_hub'))



# ==========================================
# IN-ROOM MINIBAR BILLING & INSPECTION
# ==========================================

def seed_default_minibar_services():
    """Seed luxury in-room minibar items if not present"""
    defaults = [
        ("San Pellegrino Sparkling Mineral Water (500ml)", "Minibar", 3.50, "per bottle", "Chilled sparkling mineral water"),
        ("Imported Coca-Cola Zero (330ml Can)", "Minibar", 2.50, "per can", "Chilled soft drink"),
        ("Red Bull Energy Drink (250ml)", "Minibar", 4.50, "per can", "Premium energy drink"),
        ("Roasted Salted Cashews (100g Jar)", "Minibar", 5.00, "per jar", "Gourmet cashew nuts"),
        ("Swiss Premium Dark Chocolate Bar (100g)", "Minibar", 6.00, "per bar", "Lindt Swiss excellence 70% cocoa"),
        ("Pringles Potato Crisps (Original 110g)", "Minibar", 4.00, "per can", "Crispy snack"),
        ("Tropicana 100% Pure Orange Juice (300ml)", "Minibar", 3.00, "per bottle", "Chilled pure fruit juice"),
    ]
    for name, cat, price, unit, desc in defaults:
        if not HotelService.query.filter_by(name=name).first():
            svc = HotelService(name=name, category=cat, price=price, unit_type=unit, description=desc, is_active=True)
            db.session.add(svc)
    db.session.commit()


@housekeeping_bp.route('/minibar')
@login_required
@role_required('Super Admin', 'Manager', 'Housekeeping', 'Receptionist')
def minibar_hub():
    seed_default_minibar_services()
    
    occupied_bookings = Booking.query.filter_by(status='Checked-in').order_by(Booking.check_in_date.desc()).all()
    minibar_services = HotelService.query.filter_by(category='Minibar', is_active=True).order_by(HotelService.price.asc()).all()
    
    minibar_orders = ServiceOrder.query.join(HotelService).filter(
        HotelService.category == 'Minibar'
    ).order_by(ServiceOrder.created_at.desc()).all()

    total_sales = sum(o.total_amount for o in minibar_orders)
    total_items = sum(o.quantity for o in minibar_orders)

    return render_template(
        'housekeeping/minibar.html',
        occupied_bookings=occupied_bookings,
        minibar_services=minibar_services,
        minibar_orders=minibar_orders,
        total_sales=total_sales,
        total_items=total_items
    )


@housekeeping_bp.route('/minibar/record', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager', 'Housekeeping', 'Receptionist')
def record_minibar_consumption():
    booking_id = request.form.get('booking_id', type=int)
    service_id = request.form.get('service_id', type=int)
    quantity = request.form.get('quantity', 1, type=int)
    notes = request.form.get('notes', '').strip()
    post_to_folio = request.form.get('post_to_folio') == 'on'

    booking = Booking.query.get_or_404(booking_id)
    service = HotelService.query.get_or_404(service_id)

    if quantity <= 0:
        flash('Fadlan geli tirada saxda ah ee la isticmaalay.', 'danger')
        return redirect(url_for('housekeeping.minibar_hub'))

    total_amount = round(service.price * quantity, 2)
    room = booking.booking_rooms[0].room if booking.booking_rooms else None
    room_id = room.id if room else None
    room_str = f"Room {room.room_number}" if room else "In-House"

    order = ServiceOrder(
        service_id=service.id,
        booking_id=booking.id,
        room_id=room_id,
        quantity=quantity,
        unit_price=service.price,
        total_amount=total_amount,
        status='Completed',
        is_charged_to_folio=post_to_folio,
        notes=f"Minibar Restock & Audit: {notes}" if notes else "Minibar room inspection consumption"
    )
    db.session.add(order)

    # Post directly to Guest Folio
    if post_to_folio:
        invoice = Invoice.query.filter_by(booking_id=booking.id).first()
        if invoice:
            add_item_to_folio(
                invoice_id=invoice.id,
                category='Minibar',
                description=f"In-Room Minibar ({room_str}): {quantity}x {service.name}",
                unit_price=service.price,
                quantity=quantity
            )

    db.session.commit()
    log_audit('MINIBAR_BILLING', 'ServiceOrder', order.id, f"Billed Minibar for {booking.guest.full_name} ({room_str}): {quantity}x {service.name} (${total_amount:,.2f})")
    send_notification(
        user_id=None,
        title=f"Biilka Minibar-ka ({room_str})",
        message=f"Waxaa biilka {room_str} ({booking.guest.full_name}) lagu daray ${total_amount:,.2f} oo ah minibar: {quantity}x {service.name}.",
        notif_type='info',
        link="/housekeeping/minibar"
    )

    flash(f"Minibar-ka {room_str} ({quantity}x {service.name} - ${total_amount:,.2f}) toos ayaa loogu daray biilka martida!", 'success')
    return redirect(url_for('housekeeping.minibar_hub'))


@housekeeping_bp.route('/minibar/<int:order_id>/delete', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager')
def delete_minibar_order(order_id):
    order = ServiceOrder.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    log_audit('DELETE_MINIBAR_ORDER', 'ServiceOrder', order_id, f"Deleted Minibar record #{order_id}")
    flash(f"Diiwaanka minibar #{order_id} waa la tirtiray.", 'info')
    return redirect(url_for('housekeeping.minibar_hub'))
