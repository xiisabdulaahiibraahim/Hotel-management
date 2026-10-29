from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import (
    db, RestaurantOrder, RestaurantOrderItem, MenuItem, MenuCategory, 
    Room, Booking, User, HotelSetting
)
from app.utils.helpers import log_audit
import json
from datetime import datetime

delivery_bp = Blueprint('delivery', __name__, url_prefix='/delivery')

import os
import time
from werkzeug.utils import secure_filename
from flask import current_app
from app.utils.decorators import role_required

@delivery_bp.route('/')
@login_required
@role_required('Super Admin', 'Manager', 'Restaurant/POS Staff', 'Receptionist')
def index():
    # Fetch all delivery orders
    status_filter = request.args.get('status')
    query = RestaurantOrder.query.filter(
        RestaurantOrder.order_type.in_(['Delivery', 'Online Delivery', 'Room Service'])
    )

    if status_filter:
        query = query.filter(RestaurantOrder.status == status_filter)

    delivery_orders = query.order_by(RestaurantOrder.created_at.desc()).all()
    menu_items = MenuItem.query.filter_by(is_available=True).all()
    occupied_rooms = Room.query.filter_by(status='Occupied').all()

    # Metrics
    total_deliveries = len(delivery_orders)
    pending_count = sum(1 for o in delivery_orders if o.status == 'Pending')
    in_kitchen_count = sum(1 for o in delivery_orders if o.status in ['In Kitchen', 'Ready'])
    in_transit_count = sum(1 for o in delivery_orders if o.status == 'Out for Delivery')
    delivered_count = sum(1 for o in delivery_orders if o.status == 'Delivered')
    total_delivery_revenue = sum(o.total_amount for o in delivery_orders if o.status == 'Delivered')

    return render_template(
        'delivery/index.html',
        delivery_orders=delivery_orders,
        menu_items=menu_items,
        occupied_rooms=occupied_rooms,
        status_filter=status_filter,
        total_deliveries=total_deliveries,
        pending_count=pending_count,
        in_kitchen_count=in_kitchen_count,
        in_transit_count=in_transit_count,
        delivered_count=delivered_count,
        total_delivery_revenue=total_delivery_revenue
    )

@delivery_bp.route('/create', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager', 'Restaurant/POS Staff', 'Receptionist')
def create_delivery():
    try:
        customer_name = request.form.get('customer_name', '').strip()
        customer_phone = request.form.get('customer_phone', '').strip()
        delivery_address = request.form.get('delivery_address', '').strip()
        delivery_rider = request.form.get('delivery_rider', '').strip()
        delivery_notes = request.form.get('delivery_notes', '').strip()
        room_id = request.form.get('room_id')
        items_json = request.form.get('items_json')

        if not items_json:
            flash('No items selected for delivery order.', 'danger')
            return redirect(url_for('delivery.index'))

        items_data = json.loads(items_json)
        if not items_data:
            flash('Delivery items list is empty.', 'danger')
            return redirect(url_for('delivery.index'))

        order_count = RestaurantOrder.query.count() + 1001
        order_num = f"DEL-{order_count}"

        # Handle delivery parcel image upload
        delivery_img_path = None
        delivery_file = request.files.get('delivery_image')
        if delivery_file and delivery_file.filename:
            ext = os.path.splitext(delivery_file.filename)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.webp', '.avif', '.gif']:
                filename = f"delivery_{order_num}_{int(time.time())}{ext}"
                upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads'), 'delivery')
                os.makedirs(upload_dir, exist_ok=True)
                delivery_file.save(os.path.join(upload_dir, filename))
                delivery_img_path = f"/static/uploads/delivery/{filename}"

        parsed_room_id = int(room_id) if room_id and str(room_id).isdigit() else None
        booking = None
        if parsed_room_id:
            booking = Booking.query.filter(
                Booking.status == 'Checked-in',
                Booking.booking_rooms.any(room_id=parsed_room_id)
            ).first()

        order = RestaurantOrder(
            order_number=order_num,
            order_type='Delivery',
            room_id=parsed_room_id,
            booking_id=booking.id if booking else None,
            customer_name=customer_name or (booking.guest.full_name if booking and booking.guest else 'Valued Customer'),
            customer_phone=customer_phone or (booking.guest.phone if booking and booking.guest else 'Direct Contact'),
            delivery_address=delivery_address or (f"Room {order.room.room_number}" if parsed_room_id else 'Front Desk Pickup'),
            delivery_rider=delivery_rider or 'Pending Assignment',
            delivery_notes=delivery_notes,
            delivery_image=delivery_img_path,
            status='Pending',
            created_by=current_user.id
        )
        db.session.add(order)
        db.session.flush()

        subtotal = 0.0
        for itm in items_data:
            m_id = int(itm['id'])
            qty = max(int(itm.get('qty', 1)), 1)
            menu_item = db.session.get(MenuItem, m_id) or MenuItem.query.get(m_id)
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

        db.session.commit()
        log_audit('CREATE_DELIVERY', 'RestaurantOrder', order.id, f"Delivery Order {order.order_number}: ${order.total_amount} to {order.delivery_address}")
        flash(f"Delivery order {order.order_number} created successfully! Total: ${order.total_amount:,.2f}", 'success')
        return redirect(url_for('delivery.index'))

    except Exception as e:
        db.session.rollback()
        flash(f"Error creating delivery order: {str(e)}", 'danger')
        return redirect(url_for('delivery.index'))

@delivery_bp.route('/<int:order_id>/update-status', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager', 'Restaurant/POS Staff', 'Receptionist')
def update_status(order_id):
    order = RestaurantOrder.query.get_or_404(order_id)
    new_status = request.form.get('status')
    rider = request.form.get('delivery_rider')

    if new_status:
        order.status = new_status
    if rider:
        order.delivery_rider = rider.strip()

    # Handle image update / proof of delivery
    delivery_file = request.files.get('delivery_image')
    if delivery_file and delivery_file.filename:
        ext = os.path.splitext(delivery_file.filename)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.webp', '.avif', '.gif']:
            filename = f"delivery_{order.order_number}_{int(time.time())}{ext}"
            upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads'), 'delivery')
            os.makedirs(upload_dir, exist_ok=True)
            delivery_file.save(os.path.join(upload_dir, filename))
            order.delivery_image = f"/static/uploads/delivery/{filename}"

    db.session.commit()
    log_audit('UPDATE_DELIVERY_STATUS', 'RestaurantOrder', order.id, f"Delivery {order.order_number} marked as {new_status} (Rider: {order.delivery_rider})")
    flash(f"Delivery {order.order_number} updated to status: {new_status}", 'success')
    return redirect(request.referrer or url_for('delivery.index'))


@delivery_bp.route('/<int:order_id>/delete', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager', 'Restaurant/POS Staff', 'Receptionist')
def delete_delivery(order_id):
    order = RestaurantOrder.query.get_or_404(order_id)
    order_num = order.order_number
    RestaurantOrderItem.query.filter_by(order_id=order.id).delete()
    db.session.delete(order)
    db.session.commit()
    log_audit('DELETE_DELIVERY_ORDER', 'RestaurantOrder', order_id, f"Delivery order {order_num} was deleted by {current_user.username}")
    flash(f"Delivery order {order_num} has been permanently deleted.", "warning")
    return redirect(request.referrer or url_for('delivery.index'))

