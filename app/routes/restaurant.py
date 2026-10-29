from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
import json
from datetime import datetime, date
from app.models import (
    db, MenuCategory, MenuItem, RestaurantOrder, RestaurantOrderItem, 
    Room, Booking, Invoice, HotelService, ServiceOrder,
    InventoryItem, StockMovement, RecipeIngredient, TableReservation
)
from app.utils.helpers import send_notification
from app.services.billing_service import add_item_to_folio
from app.utils.helpers import log_audit
from app.utils.decorators import role_required

restaurant_bp = Blueprint('restaurant', __name__, url_prefix='/restaurant')

@restaurant_bp.route('/pos')
@login_required
@role_required('Super Admin', 'Manager', 'Restaurant/POS Staff', 'Receptionist')
def pos():
    categories = MenuCategory.query.order_by(MenuCategory.display_order.asc()).all()
    menu_items = MenuItem.query.filter_by(is_available=True).all()
    occupied_rooms = Room.query.filter_by(status='Occupied').all()
    services = HotelService.query.filter_by(is_active=True).all()

    return render_template(
        'restaurant/pos.html',
        categories=categories,
        menu_items=menu_items,
        occupied_rooms=occupied_rooms,
        services=services
    )


@restaurant_bp.route('/orders')
@login_required
@role_required('Super Admin', 'Manager', 'Restaurant/POS Staff', 'Receptionist')
def orders():
    status = request.args.get('status')
    query = RestaurantOrder.query

    if status:
        query = query.filter_by(status=status)

    orders = query.order_by(RestaurantOrder.created_at.desc()).all()
    return render_template('restaurant/orders.html', orders=orders, selected_status=status)


@restaurant_bp.route('/kitchen')
@login_required
@role_required('Super Admin', 'Manager', 'Restaurant/POS Staff', 'Receptionist')
def kitchen():
    active_orders = RestaurantOrder.query.filter(
        RestaurantOrder.status.in_(['Pending', 'In Kitchen', 'Ready'])
    ).order_by(RestaurantOrder.created_at.asc()).all()

    return render_template('restaurant/kitchen.html', active_orders=active_orders)


@restaurant_bp.route('/create-order', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager', 'Restaurant/POS Staff', 'Receptionist')
def create_order():
    try:
        order_type = request.form.get('order_type', 'Dine-In')
        room_id = request.form.get('room_id')
        table_number = request.form.get('table_number')
        charge_to_room = bool(request.form.get('charge_to_room'))
        items_json = request.form.get('items_json')

        if not items_json:
            flash('No items selected for order.', 'danger')
            return redirect(url_for('restaurant.pos'))

        items_data = json.loads(items_json)
        if not items_data:
            flash('Order cart is empty.', 'danger')
            return redirect(url_for('restaurant.pos'))

        order_count = RestaurantOrder.query.count() + 1001
        order_num = f"ORD-{order_count}"

        booking = None
        parsed_room_id = None
        if room_id and str(room_id).strip() and str(room_id).strip().isdigit():
            parsed_room_id = int(room_id)
            # Find active checked-in booking for room
            booking = Booking.query.filter(
                Booking.status == 'Checked-in',
                Booking.booking_rooms.any(room_id=parsed_room_id)
            ).first()

        order = RestaurantOrder(
            order_number=order_num,
            order_type=order_type,
            room_id=parsed_room_id,
            booking_id=booking.id if booking else None,
            table_number=table_number or ('Room Service' if parsed_room_id else 'Direct Order'),
            status='In Kitchen', # Sent directly to Kitchen!
            is_charged_to_room=charge_to_room,
            created_by=current_user.id
        )
        db.session.add(order)
        db.session.flush()

        subtotal = 0.0
        for itm in items_data:
            menu_item_id = int(itm['id'])
            qty = max(int(itm.get('qty', 1)), 1)
            menu_item = db.session.get(MenuItem, menu_item_id) or MenuItem.query.get(menu_item_id)
            if menu_item:
                item_sub = menu_item.price * qty
                subtotal += item_sub
                roi = RestaurantOrderItem(
                    order_id=order.id,
                    menu_item_id=menu_item.id,
                    quantity=qty,
                    unit_price=menu_item.price,
                    subtotal=item_sub,
                    special_instructions=itm.get('notes')
                )
                db.session.add(roi)

        order.subtotal = subtotal
        order.tax_amount = round(subtotal * 0.05, 2)
        order.total_amount = round(subtotal + order.tax_amount, 2)

        # If charge to room, automatically post to guest folio invoice!
        if charge_to_room and booking:
            invoice = Invoice.query.filter_by(booking_id=booking.id).first()
            if invoice:
                add_item_to_folio(
                    invoice_id=invoice.id,
                    category='Restaurant',
                    description=f"Dining ({order.order_number}) - Room Service",
                    unit_price=order.total_amount,
                    quantity=1
                )

        deplete_order_inventory(order)
        db.session.commit()
        from app.utils.helpers import send_notification
        log_audit('RESTAURANT_ORDER', 'RestaurantOrder', order.id, f"Order {order.order_number}: ${order.total_amount}")
        send_notification(
            user_id=None,
            title=f"Dalab Cusub oo Cunto ah (#{order.order_number})",
            message=f"Dalab cusub oo ah ${order.total_amount:,.2f} ({order.order_type}) ayaa toos loo gudbiyay Jikada si loo diyaariyo.",
            notif_type='warning',
            link="/restaurant/kitchen"
        )
        flash(f'Order {order.order_number} created and dispatched directly to the Kitchen brigade! Total: ${order.total_amount:,.2f}', 'success')
        return redirect(url_for('restaurant.orders'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error creating order: {str(e)}', 'danger')
        return redirect(url_for('restaurant.pos'))


@restaurant_bp.route('/order/<int:order_id>/status', methods=['POST'])
@login_required
def update_order_status(order_id):
    from app.utils.helpers import send_notification
    order = RestaurantOrder.query.get_or_404(order_id)
    new_status = request.form.get('status')
    order.status = new_status
    db.session.commit()
    log_audit('UPDATE_ORDER_STATUS', 'RestaurantOrder', order.id, f"Order {order.order_number} marked as {new_status}")
    
    dest_str = order.delivery_address or (f"Room {order.room.room_number}" if order.room else (order.table_number or 'Guest'))
    if new_status == 'Ready':
        send_notification(
            user_id=None,
            title=f"Cuntadii waa Diyaar (#{order.order_number})",
            message=f"Dalabka #{order.order_number} ee loo wado {dest_str} wuu ka diyaar yahay Jikada. Fadlan Reception-ku ha u qaado macmiilka!",
            notif_type='success',
            link="/restaurant/orders"
        )
    elif new_status == 'Out for Delivery':
        send_notification(
            user_id=None,
            title=f"Dalabka Waa Loo Qaaday (#{order.order_number})",
            message=f"Dalabka #{order.order_number} waxaa loo qaaday {dest_str}.",
            notif_type='info',
            link="/restaurant/orders"
        )
    elif new_status == 'Delivered':
        send_notification(
            user_id=None,
            title=f"Dalabka Waa La Gaarsiiyay (#{order.order_number})",
            message=f"Dalabka #{order.order_number} si guul ah ayaa loogu wareejiyay {dest_str}.",
            notif_type='success',
            link="/restaurant/orders"
        )

    flash(f'Order {order.order_number} status updated to {new_status}.', 'success')
    return redirect(request.referrer or url_for('restaurant.orders'))


@restaurant_bp.route('/order/<int:order_id>/send-to-kitchen', methods=['POST'])
@login_required
def send_to_kitchen(order_id):
    from app.utils.helpers import send_notification
    order = RestaurantOrder.query.get_or_404(order_id)
    order.status = 'In Kitchen'
    db.session.commit()
    log_audit('SEND_TO_KITCHEN', 'RestaurantOrder', order.id, f"Order {order.order_number} dispatched to kitchen")
    send_notification(
        user_id=None,
        title=f"Dalab loo Diray Jikada (#{order.order_number})",
        message=f"Dalabka #{order.order_number} waxaa loo gudbiyay Jikada si loo kariyo.",
        notif_type='warning',
        link="/restaurant/kitchen"
    )
    flash(f'Order {order.order_number} has been dispatched to the Kitchen (Jikada)!', 'success')
    return redirect(request.referrer or url_for('restaurant.orders'))


@restaurant_bp.route('/order/<int:order_id>/send-to-reception', methods=['POST'])
@login_required
def send_to_reception(order_id):
    from app.utils.helpers import send_notification
    order = RestaurantOrder.query.get_or_404(order_id)
    order.status = 'Ready'
    db.session.commit()
    dest_str = order.delivery_address or (f"Room {order.room.room_number}" if order.room else (order.table_number or 'Guest'))
    log_audit('SEND_TO_RECEPTION', 'RestaurantOrder', order.id, f"Order {order.order_number} ready and forwarded to reception")
    send_notification(
        user_id=None,
        title=f"Cuntadii waa Diyaar (#{order.order_number})",
        message=f"Dalabka #{order.order_number} ee loo wado {dest_str} wuu ka diyaar yahay Jikada. Reception-ku ha u qaado macmiilka!",
        notif_type='success',
        link="/restaurant/orders"
    )
    flash(f'Order {order.order_number} is ready and forwarded to Reception for delivery!', 'success')
    return redirect(request.referrer or url_for('restaurant.kitchen'))


@restaurant_bp.route('/order/<int:order_id>/dispatch', methods=['POST'])
@login_required
def dispatch_order(order_id):
    from app.utils.helpers import send_notification
    order = RestaurantOrder.query.get_or_404(order_id)
    order.status = 'Out for Delivery'
    db.session.commit()
    dest_str = order.delivery_address or (f"Room {order.room.room_number}" if order.room else (order.table_number or 'Guest'))
    log_audit('DISPATCH_ORDER', 'RestaurantOrder', order.id, f"Order {order.order_number} dispatched for delivery")
    send_notification(
        user_id=None,
        title=f"Dalabka Waa Loo Qaaday (#{order.order_number})",
        message=f"Dalabka #{order.order_number} waxaa loo qaaday {dest_str}.",
        notif_type='info',
        link="/restaurant/orders"
    )
    flash(f'Order {order.order_number} is now Out for Delivery to {dest_str}!', 'info')
    return redirect(request.referrer or url_for('restaurant.orders'))


@restaurant_bp.route('/order/<int:order_id>/delivered', methods=['POST'])
@login_required
def deliver_order(order_id):
    from app.utils.helpers import send_notification
    order = RestaurantOrder.query.get_or_404(order_id)
    order.status = 'Delivered'
    db.session.commit()
    dest_str = order.delivery_address or (f"Room {order.room.room_number}" if order.room else (order.table_number or 'Guest'))
    log_audit('DELIVER_ORDER', 'RestaurantOrder', order.id, f"Order {order.order_number} delivered successfully")
    send_notification(
        user_id=None,
        title=f"Dalabka Waa La Gaarsiiyay (#{order.order_number})",
        message=f"Dalabka #{order.order_number} si guul ah ayaa loogu wareejiyay {dest_str}.",
        notif_type='success',
        link="/restaurant/orders"
    )
    flash(f'Order {order.order_number} delivered successfully to {dest_str}!', 'success')
    return redirect(request.referrer or url_for('restaurant.orders'))


@restaurant_bp.route('/order/<int:order_id>/pay', methods=['POST'])
@login_required
def collect_payment(order_id):
    from app.utils.helpers import log_audit, send_notification
    order = RestaurantOrder.query.get_or_404(order_id)
    payment_method = request.form.get('payment_method', 'EVC Plus (Hormuud)').strip()
    is_folio = (payment_method == 'Post to Room Folio' or 'Folio' in payment_method)
    
    order.payment_method = payment_method
    if is_folio:
        order.is_charged_to_room = True
        order.payment_status = 'Paid (Folio)'
        # If order is linked to room or booking, post to guest invoice folio
        booking = order.booking
        if not booking and order.room_id:
            booking = Booking.query.filter(
                Booking.status == 'Checked-in',
                Booking.booking_rooms.any(room_id=order.room_id)
            ).first()
        if booking:
            invoice = Invoice.query.filter_by(booking_id=booking.id).first()
            if invoice:
                add_item_to_folio(
                    invoice_id=invoice.id,
                    category='Restaurant',
                    description=f"Dining ({order.order_number}) - Room Folio Charge",
                    unit_price=order.total_amount,
                    quantity=1
                )
    else:
        order.payment_status = 'Paid'

    db.session.commit()
    log_audit('COLLECT_ORDER_PAYMENT', 'RestaurantOrder', order.id, f"Payment of ${order.total_amount:,.2f} confirmed ({payment_method}) for {order.order_number}")
    send_notification(
        user_id=None,
        title=f"Lacagta Waa La Xaqiijiyay (#{order.order_number})",
        message=f"Waxaa la xaqiijiyay bixinta lacagta ${order.total_amount:,.2f} ({payment_method}) ee dalabka #{order.order_number}. Hadda cuntada waa la gaarsiin karaa.",
        notif_type='success',
        link="/restaurant/orders"
    )
    flash(f"Payment of ${order.total_amount:,.2f} successfully confirmed ({payment_method}) for Order {order.order_number}!", "success")
    return redirect(request.referrer or url_for('restaurant.orders'))


@restaurant_bp.route('/order/<int:order_id>/edit', methods=['POST'])
@login_required
def edit_order(order_id):
    order = RestaurantOrder.query.get_or_404(order_id)
    new_status = request.form.get('status', order.status)
    table_number = request.form.get('table_number', order.table_number)
    order_type = request.form.get('order_type', order.order_type)
    
    order.status = new_status
    order.table_number = table_number.strip() if table_number else None
    order.order_type = order_type
    
    db.session.commit()
    log_audit('EDIT_ORDER', 'RestaurantOrder', order.id, f"Order {order.order_number} details updated")
    flash(f'Order {order.order_number} details successfully updated.', 'success')
    return redirect(url_for('restaurant.orders'))


@restaurant_bp.route('/order/<int:order_id>/delete', methods=['POST'])
@login_required
def delete_order(order_id):
    order = RestaurantOrder.query.get_or_404(order_id)
    order_num = order.order_number
    
    # Delete order items first
    RestaurantOrderItem.query.filter_by(order_id=order.id).delete()
    db.session.delete(order)
    db.session.commit()
    
    log_audit('DELETE_ORDER', 'RestaurantOrder', order_id, f"Order {order_num} was deleted by {current_user.username}")
    flash(f'Order {order_num} has been permanently deleted.', 'warning')
    return redirect(url_for('restaurant.orders'))


@restaurant_bp.route('/order/<int:order_id>/kot')
@login_required
def kot_ticket(order_id):
    order = RestaurantOrder.query.get_or_404(order_id)
    from app.models import HotelSetting
    hotel_name = HotelSetting.get_value('hotel_name', 'The Grand Horizon Luxury Hotel & Resort')
    return render_template('restaurant/kot_ticket.html', order=order, hotel_name=hotel_name)


@restaurant_bp.route('/services/order', methods=['POST'])
@login_required
def order_extra_service():
    service_id = int(request.form.get('service_id'))
    room_id = int(request.form.get('room_id'))
    quantity = int(request.form.get('quantity', 1) or 1)
    notes = request.form.get('notes', '').strip()

    service = HotelService.query.get_or_404(service_id)
    booking = Booking.query.filter(
        Booking.status == 'Checked-in',
        Booking.booking_rooms.any(room_id=room_id)
    ).first()

    if not booking:
        flash('Selected room has no active checked-in guest booking.', 'danger')
        return redirect(url_for('restaurant.pos'))

    total = round(service.price * quantity, 2)
    s_order = ServiceOrder(
        service_id=service.id,
        booking_id=booking.id,
        room_id=room_id,
        quantity=quantity,
        unit_price=service.price,
        total_amount=total,
        status='Requested',
        is_charged_to_folio=True,
        notes=notes
    )
    db.session.add(s_order)

    # Post directly to guest folio
    invoice = Invoice.query.filter_by(booking_id=booking.id).first()
    if invoice:
        add_item_to_folio(
            invoice_id=invoice.id,
            category=service.category,
            description=f"{service.name} (x{quantity})",
            unit_price=service.price,
            quantity=quantity
        )

    db.session.commit()
    flash(f'{service.name} ordered and added to Room {room_id} folio (${total:,.2f}).', 'success')
    return redirect(url_for('restaurant.pos'))


import os
import time
from werkzeug.utils import secure_filename
from flask import current_app

@restaurant_bp.route('/menu/add', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager', 'Restaurant/POS Staff')
def add_menu_item():
    name = request.form.get('name', '').strip()
    category_id = int(request.form.get('category_id'))
    price = float(request.form.get('price', 0.0) or 0.0)
    description = request.form.get('description', '').strip()
    prep_time = int(request.form.get('preparation_time', 15) or 15)
    
    # Handle image upload
    img_url = None
    file = request.files.get('menu_image')
    if file and file.filename:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.webp', '.avif']:
            filename = f"menu_{int(time.time())}_{secure_filename(file.filename)}"
            upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads'), 'menu')
            os.makedirs(upload_dir, exist_ok=True)
            file.save(os.path.join(upload_dir, filename))
            img_url = f"/static/uploads/menu/{filename}"
            
    item = MenuItem(
        name=name,
        category_id=category_id,
        price=price,
        description=description,
        preparation_time=prep_time,
        image_url=img_url,
        is_available=True
    )
    db.session.add(item)
    db.session.commit()
    log_audit('CREATE_MENU_ITEM', 'MenuItem', item.id, f"Added dish {item.name}")
    flash(f"Dish '{item.name}' added to restaurant menu successfully.", 'success')
    return redirect(request.referrer or url_for('restaurant.pos'))


@restaurant_bp.route('/menu/<int:item_id>/edit', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager', 'Restaurant/POS Staff')
def edit_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    item.name = request.form.get('name', item.name).strip()
    item.category_id = int(request.form.get('category_id', item.category_id))
    item.price = float(request.form.get('price', item.price) or item.price)
    item.description = request.form.get('description', item.description).strip()
    item.preparation_time = int(request.form.get('preparation_time', item.preparation_time) or item.preparation_time)
    item.is_available = bool(request.form.get('is_available', True))

    file = request.files.get('menu_image')
    if file and file.filename:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.webp', '.avif']:
            filename = f"menu_{item.id}_{int(time.time())}{ext}"
            upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads'), 'menu')
            os.makedirs(upload_dir, exist_ok=True)
            file.save(os.path.join(upload_dir, filename))
            item.image_url = f"/static/uploads/menu/{filename}"

    db.session.commit()
    log_audit('UPDATE_MENU_ITEM', 'MenuItem', item.id, f"Updated dish {item.name}")
    flash(f"Dish '{item.name}' updated successfully.", 'success')
    return redirect(request.referrer or url_for('restaurant.pos'))


def deplete_order_inventory(order):
    """Auto-deduct raw materials from inventory based on dish recipes"""
    try:
        for roi in order.items:
            if not roi.menu_item:
                continue
            for ing in roi.menu_item.recipe_ingredients:
                inv_item = ing.inventory_item
                if inv_item:
                    qty_to_deduct = round(float(roi.quantity) * float(ing.quantity_required), 2)
                    inv_item.quantity_in_stock = max(0.0, round((inv_item.quantity_in_stock or 0.0) - qty_to_deduct, 2))
                    
                    movement = StockMovement(
                        inventory_item_id=inv_item.id,
                        movement_type='OUT',
                        quantity=qty_to_deduct,
                        unit_cost=inv_item.unit_cost,
                        reason=f"Kitchen Order #{order.order_number}: {roi.menu_item.name} x{roi.quantity}",
                        recorded_by=current_user.id if hasattr(current_user, 'id') and current_user.is_authenticated else None
                    )
                    db.session.add(movement)
                    
                    # Low stock warning
                    if inv_item.quantity_in_stock <= inv_item.min_reorder_level:
                        send_notification(
                            user_id=None,
                            title=f"Digniin: Alaab Gabaabsi ah ({inv_item.name})",
                            message=f"Alaabta {inv_item.name} waxaa bakhaarka ku hartay {inv_item.quantity_in_stock} {inv_item.unit}. Fadlan dib u dalbo.",
                            notif_type='warning',
                            link="/inventory/"
                        )
        db.session.commit()
    except Exception as e:
        print(f"Error depleting inventory for order #{order.id}: {e}")


# ==========================================
# RECIPE & INVENTORY STOCK DEPLETION ROUTES
# ==========================================

@restaurant_bp.route('/recipes')
@login_required
@role_required('Super Admin', 'Manager', 'Restaurant/POS Staff')
def recipes():
    menu_items = MenuItem.query.order_by(MenuItem.name.asc()).all()
    inventory_items = InventoryItem.query.order_by(InventoryItem.name.asc()).all()
    return render_template('restaurant/recipes.html', menu_items=menu_items, inventory_items=inventory_items)


@restaurant_bp.route('/recipes/<int:item_id>/add-ingredient', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager', 'Restaurant/POS Staff')
def add_recipe_ingredient(item_id):
    menu_item = MenuItem.query.get_or_404(item_id)
    inv_id = request.form.get('inventory_item_id', type=int)
    qty = request.form.get('quantity_required', type=float)

    if not inv_id or not qty or qty <= 0:
        flash('Fadlan dooro alaabta iyo cadadka saxda ah.', 'danger')
        return redirect(url_for('restaurant.recipes'))

    existing = RecipeIngredient.query.filter_by(menu_item_id=menu_item.id, inventory_item_id=inv_id).first()
    if existing:
        existing.quantity_required = qty
        flash(f"Qadarka alaabta ee cuntada '{menu_item.name}' waa la cusboonaysiiyay.", 'success')
    else:
        recipe = RecipeIngredient(
            menu_item_id=menu_item.id,
            inventory_item_id=inv_id,
            quantity_required=qty
        )
        db.session.add(recipe)
        flash(f"Alaab cusub ayaa lagu daray cuntada '{menu_item.name}'.", 'success')

    db.session.commit()
    log_audit('UPDATE_RECIPE', 'MenuItem', menu_item.id, f"Configured recipe for {menu_item.name}")
    return redirect(url_for('restaurant.recipes'))


@restaurant_bp.route('/recipes/ingredient/<int:recipe_id>/delete', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager', 'Restaurant/POS Staff')
def delete_recipe_ingredient(recipe_id):
    recipe = RecipeIngredient.query.get_or_404(recipe_id)
    dish_name = recipe.menu_item.name if recipe.menu_item else "Dish"
    db.session.delete(recipe)
    db.session.commit()
    flash(f"Alaabtii waa laga saaray cuntada '{dish_name}'.", 'info')
    return redirect(url_for('restaurant.recipes'))


# ==========================================
# TABLE RESERVATIONS (DINING TABLE BOOKINGS)
# ==========================================

@restaurant_bp.route('/reservations')
@login_required
@role_required('Super Admin', 'Manager', 'Restaurant/POS Staff', 'Receptionist')
def table_reservations():
    filter_date = request.args.get('date')
    status = request.args.get('status')
    
    query = TableReservation.query

    if filter_date:
        try:
            d = datetime.strptime(filter_date, '%Y-%m-%d').date()
            query = query.filter(TableReservation.reservation_date == d)
        except ValueError:
            pass
            
    if status:
        query = query.filter(TableReservation.status == status)

    reservations = query.order_by(TableReservation.reservation_date.desc(), TableReservation.reservation_time.asc()).all()
    today = date.today()
    
    today_count = TableReservation.query.filter(TableReservation.reservation_date == today).count()
    seated_count = TableReservation.query.filter(TableReservation.status == 'Seated').count()
    confirmed_count = TableReservation.query.filter(TableReservation.status == 'Confirmed').count()
    
    return render_template(
        'restaurant/reservations.html',
        reservations=reservations,
        today=today,
        today_count=today_count,
        seated_count=seated_count,
        confirmed_count=confirmed_count,
        selected_status=status,
        selected_date=filter_date
    )


@restaurant_bp.route('/reservations/create', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager', 'Restaurant/POS Staff', 'Receptionist')
def create_table_reservation():
    import random
    guest_name = request.form.get('guest_name', '').strip()
    guest_phone = request.form.get('guest_phone', '').strip()
    guest_email = request.form.get('guest_email', '').strip()
    table_num = request.form.get('table_number', '').strip()
    res_date_str = request.form.get('reservation_date')
    res_time = request.form.get('reservation_time', '').strip()
    guests_count = int(request.form.get('guests_count', 2) or 2)
    special_req = request.form.get('special_requests', '').strip()

    if not guest_name or not guest_phone or not table_num or not res_date_str or not res_time:
        flash('Fadlan buuxi dhammaan macluumaadka muhiimka ah ee miiska.', 'danger')
        return redirect(url_for('restaurant.table_reservations'))

    res_date = datetime.strptime(res_date_str, '%Y-%m-%d').date()
    code = f"RES-{random.randint(10000, 99999)}"

    res = TableReservation(
        reservation_code=code,
        guest_name=guest_name,
        guest_phone=guest_phone,
        guest_email=guest_email,
        table_number=table_num,
        reservation_date=res_date,
        reservation_time=res_time,
        guests_count=guests_count,
        special_requests=special_req,
        status='Confirmed',
        created_by=current_user.id
    )
    db.session.add(res)
    db.session.commit()

    log_audit('TABLE_RESERVATION', 'TableReservation', res.id, f"Booked table {table_num} for {guest_name} on {res_date} at {res_time}")
    send_notification(
        user_id=None,
        title=f"Ballan Miis Cusub: {table_num} ({guest_name})",
        message=f"Miiska {table_num} waxaa loo qabtay {guest_name} ({guests_count} qof) taariikhda {res_date.strftime('%d %b %Y')} saacadda {res_time}.",
        notif_type='info',
        link="/restaurant/reservations"
    )
    flash(f"Miiska {table_num} si guul leh ayaa loogu xafiday {guest_name} (Code: {code})!", 'success')
    return redirect(url_for('restaurant.table_reservations'))


@restaurant_bp.route('/reservations/<int:res_id>/status', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager', 'Restaurant/POS Staff', 'Receptionist')
def update_table_reservation_status(res_id):
    res = TableReservation.query.get_or_404(res_id)
    new_status = request.form.get('status', res.status)
    res.status = new_status
    db.session.commit()
    log_audit('UPDATE_TABLE_RESERVATION', 'TableReservation', res.id, f"Changed status to {new_status}")
    flash(f"Xaaladda ballanta miiska {res.table_number} waxaa loo bedelay '{new_status}'.", 'success')
    return redirect(url_for('restaurant.table_reservations'))


@restaurant_bp.route('/reservations/<int:res_id>/delete', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager')
def delete_table_reservation(res_id):
    res = TableReservation.query.get_or_404(res_id)
    table_num = res.table_number
    db.session.delete(res)
    db.session.commit()
    flash(f"Ballantii miiska {table_num} waa la tirtiray.", 'info')
    return redirect(url_for('restaurant.table_reservations'))
