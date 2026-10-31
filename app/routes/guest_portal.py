from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from datetime import datetime, date, timedelta
from app.models import (
    db, Room, RoomType, Amenity, Review, Booking, Guest, HotelSetting,
    MenuItem, MenuCategory, RestaurantOrder, RestaurantOrderItem
)
from app.services.booking_service import search_available_rooms, create_booking_transaction

guest_portal_bp = Blueprint('guest_portal', __name__)

@guest_portal_bp.after_request
def add_no_cache_headers(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@guest_portal_bp.route('/')
def index():
    room_types = RoomType.query.filter_by(is_active=True).all()
    amenities = Amenity.query.all()
    reviews = Review.query.filter_by(is_approved=True).order_by(Review.created_at.desc()).limit(6).all()
    hotel_name = HotelSetting.get_value('hotel_name', 'The Grand Horizon Luxury Hotel & Resort')
    hotel_tagline = HotelSetting.get_value('hotel_tagline', 'Excellence in Hospitality, Unrivaled Luxury')
    hotel_phone = HotelSetting.get_value('hotel_phone', '+252 61 555-0100')
    hotel_email = HotelSetting.get_value('hotel_email', 'reservations@grandhorizon.com')
    hotel_address = HotelSetting.get_value('hotel_address', 'Ocean Boulevard, Lido Coastline, Mogadishu, Somalia')

    tomorrow = date.today() + timedelta(days=1)
    day_after = date.today() + timedelta(days=3)

    # Live available rooms with uploaded photos and details
    available_rooms = Room.query.filter_by(status='Available').order_by(Room.floor.asc(), Room.room_number.asc()).all()

    return render_template(
        'portal/index.html',
        room_types=room_types,
        available_rooms=available_rooms,
        amenities=amenities,
        reviews=reviews,
        hotel_name=hotel_name,
        hotel_tagline=hotel_tagline,
        hotel_phone=hotel_phone,
        hotel_email=hotel_email,
        hotel_address=hotel_address,
        checkin_default=tomorrow,
        checkout_default=day_after
    )


@guest_portal_bp.route('/suites')
@guest_portal_bp.route('/portal/rooms')
def rooms_catalog():
    # Only show room types that have at least 1 available room
    all_types = RoomType.query.filter_by(is_active=True).all()
    # Get available rooms per type for live sync
    available_rooms = Room.query.filter_by(status='Available').order_by(Room.room_number.asc()).all()
    # Build a map: room_type_id -> list of available rooms
    rooms_by_type = {}
    for rm in available_rooms:
        rooms_by_type.setdefault(rm.room_type_id, []).append(rm)
    # Only include types that actually have available rooms
    room_types = [rt for rt in all_types if rooms_by_type.get(rt.id)]
    hotel_name = HotelSetting.get_value('hotel_name', 'The Grand Horizon Luxury Hotel & Resort')
    return render_template('portal/rooms.html',
                           room_types=room_types,
                           available_rooms=available_rooms,
                           rooms_by_type=rooms_by_type,
                           hotel_name=hotel_name)


@guest_portal_bp.route('/book', methods=['GET', 'POST'])
def book_online():
    if request.method == 'POST':
        try:
            check_in_str = request.form.get('check_in')
            check_out_str = request.form.get('check_out')
            room_type_id = int(request.form.get('room_type_id'))
            adults = int(request.form.get('adults', 1))
            children = int(request.form.get('children', 0))

            check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()

            # Find matching available room
            available_rooms = search_available_rooms(check_in, check_out, adults, children, room_type_id)
            if not available_rooms:
                flash('Selected room type is fully booked for those dates. Please choose another date or room type.', 'warning')
                return redirect(url_for('guest_portal.rooms_catalog'))

            selected_room = available_rooms[0]

            # Guest Info
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            promo_code = request.form.get('promo_code', '').strip()
            special_requests = request.form.get('special_requests', '').strip()

            # Guest CRM lookup or create
            id_type = request.form.get('id_type', 'Passport').strip()
            id_number = request.form.get('id_number', '').strip()

            guest = Guest.query.filter_by(email=email).first()
            if not guest:
                guest = Guest(
                    first_name=first_name,
                    last_name=last_name or 'Valued Guest',
                    email=email,
                    phone=phone,
                    id_type=id_type,
                    id_number=id_number or f"WEB-{int(datetime.utcnow().timestamp())}"
                )
                db.session.add(guest)
                db.session.flush()
            else:
                if id_number:
                    guest.id_number = id_number
                if id_type:
                    guest.id_type = id_type

            # Handle Online Passport / ID Photo upload
            if 'id_photo' in request.files:
                file = request.files['id_photo']
                if file and file.filename != '':
                    from werkzeug.utils import secure_filename
                    import os, time
                    ext = os.path.splitext(secure_filename(file.filename))[1].lower()
                    if ext in ['.jpg', '.jpeg', '.png', '.webp', '.pdf']:
                        fname = f"id_online_{guest.id}_{int(time.time())}{ext}"
                        upload_dir = os.path.join('app', 'static', 'uploads', 'ids')
                        os.makedirs(upload_dir, exist_ok=True)
                        file.save(os.path.join(upload_dir, fname))
                        guest.id_photo = f"uploads/ids/{fname}" 

            booking, invoice = create_booking_transaction(
                guest_id=guest.id,
                room_ids=[selected_room.id],
                check_in_date=check_in,
                check_out_date=check_out,
                adults=adults,
                children=children,
                booking_source='Website',
                promo_code=promo_code,
                special_requests=special_requests,
                deposit_amount=0.0
            )

            flash(f'Your reservation #{booking.booking_reference} is confirmed! Check your email for details.', 'success')
            return redirect(url_for('guest_portal.my_bookings', ref=booking.booking_reference))

        except Exception as e:
            flash(f'Booking error: {str(e)}', 'danger')
            return redirect(url_for('guest_portal.index'))

    return redirect(url_for('guest_portal.index'))


@guest_portal_bp.route('/my-bookings')
def my_bookings():
    ref = request.args.get('ref', '').strip()
    booking = None

    if ref:
        booking = Booking.query.filter_by(booking_reference=ref).first()
    elif current_user.is_authenticated and current_user.guest_profile:
        bookings = current_user.guest_profile.bookings
        return render_template('portal/my_bookings.html', bookings=bookings)

    return render_template('portal/my_bookings.html', booking=booking, ref=ref)


@guest_portal_bp.route('/delivery')
@guest_portal_bp.route('/order-delivery')
def delivery_page():
    categories = MenuCategory.query.order_by(MenuCategory.display_order.asc()).all()
    menu_items = MenuItem.query.filter_by(is_available=True).all()
    hotel_name = HotelSetting.get_value('hotel_name', 'The Grand Horizon Luxury Hotel & Resort')
    hotel_phone = HotelSetting.get_value('hotel_phone', '+252 61 555-0100')
    occupied_rooms = Room.query.filter_by(status='Occupied').all()

    return render_template(
        'portal/delivery.html',
        categories=categories,
        menu_items=menu_items,
        hotel_name=hotel_name,
        hotel_phone=hotel_phone,
        occupied_rooms=occupied_rooms
    )


@guest_portal_bp.route('/order-delivery/submit', methods=['POST'])
def submit_delivery_order():
    import json
    try:
        customer_name = request.form.get('customer_name', '').strip()
        customer_phone = request.form.get('customer_phone', '').strip()
        delivery_type = request.form.get('delivery_type', 'Room') # Room or City
        room_number = request.form.get('room_number', '').strip()
        street_address = request.form.get('street_address', '').strip()
        payment_method = request.form.get('payment_method', 'EVC Plus / Mobile')
        delivery_notes = request.form.get('delivery_notes', '').strip()
        items_json = request.form.get('items_json')

        if not items_json:
            flash('Your delivery basket is empty. Please select menu items before placing an order.', 'danger')
            return redirect(url_for('guest_portal.delivery_page'))

        items_data = json.loads(items_json)
        if not items_data:
            flash('Your delivery basket is empty.', 'danger')
            return redirect(url_for('guest_portal.delivery_page'))

        order_count = RestaurantOrder.query.count() + 1001
        order_num = f"DEL-{order_count}"

        # Resolve destination
        if delivery_type == 'Room' and room_number:
            destination = f"Hotel Room {room_number} (In-Suite Delivery)"
        else:
            destination = street_address or 'Lido Beachfront Residence'

        order = RestaurantOrder(
            order_number=order_num,
            order_type='Delivery',
            customer_name=customer_name or 'Online Guest',
            customer_phone=customer_phone,
            delivery_address=destination,
            delivery_notes=f"Payment: {payment_method} | Notes: {delivery_notes}" if delivery_notes else f"Payment: {payment_method}",
            delivery_rider='Awaiting Dispatch',
            status='In Kitchen'
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
                    subtotal=item_sub
                )
                db.session.add(roi)

        order.subtotal = subtotal
        order.tax_amount = round(subtotal * 0.05, 2)
        order.total_amount = round(subtotal + order.tax_amount, 2)

        db.session.commit()
        from app.utils.helpers import log_audit, send_notification
        log_audit('ONLINE_DELIVERY_PLACED', 'RestaurantOrder', order.id, f"Public online delivery order {order.order_number}: ${order.total_amount} to {order.delivery_address}")
        send_notification(
            user_id=None,
            title=f"Dalab Cusub oo Cunto ah (#{order.order_number})",
            message=f"Dalab cusub oo ah ${order.total_amount:,.2f} oo loo wado {order.delivery_address} ayaa toos loogu gudbiyay Jikada si loo kariyo.",
            notif_type='warning',
            link="/restaurant/kitchen"
        )
        flash(f'Your express delivery order #{order.order_number} has been received and forwarded to our kitchen brigade for culinary preparation.', 'success')
        return redirect(url_for('guest_portal.track_delivery', order_number=order.order_number))

    except Exception as e:
        db.session.rollback()
        flash(f'Error placing delivery order: {str(e)}', 'danger')
        return redirect(url_for('guest_portal.delivery_page'))


@guest_portal_bp.route('/delivery/track/<order_number>')
def track_delivery(order_number):
    order = RestaurantOrder.query.filter_by(order_number=order_number).first_or_404()
    hotel_name = HotelSetting.get_value('hotel_name', 'The Grand Horizon Luxury Hotel & Resort')
    hotel_phone = HotelSetting.get_value('hotel_phone', '+252 61 555-0100')
    return render_template(
        'portal/delivery_tracking.html',
        order=order,
        hotel_name=hotel_name,
        hotel_phone=hotel_phone
    )



@guest_portal_bp.route('/reserve-table', methods=['POST'])
def book_table_online():
    """Online Dining Table & Beach Cabana Reservation from Public Website"""
    try:
        from app.models.restaurant import TableReservation
        from app.utils.helpers import log_audit, send_notification
        import random, time

        guest_name = request.form.get('guest_name', '').strip()
        guest_phone = request.form.get('guest_phone', '').strip()
        guest_email = request.form.get('guest_email', '').strip()
        table_area = request.form.get('table_area', 'Lido Oceanfront Terrace').strip()
        res_date_str = request.form.get('reservation_date', '').strip()
        res_time = request.form.get('reservation_time', '19:30').strip()
        guests_count = int(request.form.get('guests_count', 2))
        special_requests = request.form.get('special_requests', '').strip()

        if not guest_name or not guest_phone:
            flash('Fadlan geli magacaaga iyo lambarkaaga taleefanka.', 'danger')
            return redirect(url_for('guest_portal.index') + '#diningTableSection')

        if res_date_str:
            res_date = datetime.strptime(res_date_str, '%Y-%m-%d').date()
        else:
            res_date = date.today()

        code_suffix = int(time.time()) % 10000
        res_code = f"TBL-{random.randint(10, 99)}{code_suffix}"

        reservation = TableReservation(
            reservation_code=res_code,
            guest_name=guest_name,
            guest_phone=guest_phone,
            guest_email=guest_email,
            table_number=table_area,
            reservation_date=res_date,
            reservation_time=res_time,
            guests_count=guests_count,
            special_requests=special_requests,
            status='Confirmed'
        )
        db.session.add(reservation)
        db.session.commit()

        log_audit('ONLINE_TABLE_RESERVED', 'TableReservation', reservation.id, f"Public table reservation {res_code}: {table_area} for {guest_name} ({guests_count} guests) on {res_date} at {res_time}")
        send_notification(
            user_id=None,
            title=f"Ballan Miis Cusub (#{res_code})",
            message=f"Martida {guest_name} ({guest_phone}) waxay qabsadeen miis/aagga {table_area} taariikhda {res_date.strftime('%d %b %Y')} saacadda {res_time} ({guests_count} qof).",
            notif_type='info',
            link="/restaurant/reservations"
        )

        flash(f"Ballantaada miiska makhaayadda #{res_code} ({table_area}) si guul leh ayaa loo xaqiijiyay! Waxaan kugu sugaynaa {res_date.strftime('%a, %d %b %Y')} saacadda {res_time}.", 'success')
        return redirect(url_for('guest_portal.index') + '#diningTableSection')

    except Exception as e:
        db.session.rollback()
        flash(f"Khalad ayaa dhacay markii miiska la qabsanayay: {str(e)}", 'danger')
        return redirect(url_for('guest_portal.index') + '#diningTableSection')


@guest_portal_bp.route('/contact-inquiry', methods=['POST'])
def submit_contact_inquiry():
    """Submit Concierge, VIP Transfer, Event & Meeting Inquiries"""
    try:
        from app.utils.helpers import log_audit, send_notification

        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        inquiry_type = request.form.get('inquiry_type', 'General Inquiry').strip()
        event_date = request.form.get('event_date', '').strip()
        message = request.form.get('message', '').strip()

        if not full_name or not phone:
            flash('Fadlan geli magacaaga iyo taleefankaaga.', 'danger')
            return redirect(url_for('guest_portal.index'))

        log_audit('PUBLIC_INQUIRY', 'Inquiry', None, f"Inquiry from {full_name} ({phone}): {inquiry_type} - {message[:80]}")
        send_notification(
            user_id=None,
            title=f"Su'aal / Ballan Xaflad ({inquiry_type})",
            message=f"Fariin ka timid {full_name} ({phone}, {email}). Nooca: {inquiry_type}. Taariikhda: {event_date or 'N/A'}. Faahfaahin: {message}",
            notif_type='warning',
            link="/communications/hub"
        )

        flash("Fariintaada iyo codsigaaga concierge-ka si guul leh ayaa loo helay! Kooxda hotelka ayaa kula soo xiriiraysa waqti yar gudihiis.", 'success')
        return redirect(url_for('guest_portal.index'))

    except Exception as e:
        flash(f"Khalad ayaa dhacay: {str(e)}", 'danger')
        return redirect(url_for('guest_portal.index'))


@guest_portal_bp.route('/submit-review', methods=['POST'])
def submit_review():
    """Submit Guest Review & Rating"""
    try:
        from app.models.misc import Review
        from app.models.guest import Guest
        from app.utils.helpers import log_audit

        guest_name = request.form.get('guest_name', '').strip()
        email = request.form.get('email', '').strip()
        rating = int(request.form.get('rating', 5))
        title = request.form.get('title', '').strip()
        comment = request.form.get('comment', '').strip()

        if not guest_name or not comment:
            flash("Fadlan buuxi magacaaga iyo ra'yigaaga.", "danger")
            return redirect(url_for('guest_portal.index') + '#reviews')

        # Find or create lightweight guest record
        guest = Guest.query.filter_by(email=email).first() if email else None
        if not guest:
            first_name = guest_name.split()[0] if guest_name else 'Valued'
            last_name = " ".join(guest_name.split()[1:]) if len(guest_name.split()) > 1 else 'Guest'
            guest = Guest(
                first_name=first_name,
                last_name=last_name,
                email=email or f"guest_{int(datetime.utcnow().timestamp())}@grandhorizon.com",
                phone="N/A",
                id_number=f"REV-{int(datetime.utcnow().timestamp())}"
            )
            db.session.add(guest)
            db.session.flush()

        review = Review(
            guest_id=guest.id,
            rating=min(max(rating, 1), 5),
            title=title or 'Exceptional Stay',
            comment=comment,
            is_approved=True
        )
        db.session.add(review)
        db.session.commit()

        log_audit('GUEST_REVIEW_SUBMITTED', 'Review', review.id, f"Review by {guest_name} ({rating} stars): {title}")
        flash("Waad ku mahadsan tahay ra'yigaaga iyo qiimeyntaada qiimaha leh! Waxay toos uga muuqanaysaa bogga hotelka.", "success")
        return redirect(url_for('guest_portal.index') + '#reviews')

    except Exception as e:
        db.session.rollback()
        flash(f"Khalad ayaa dhacay: {str(e)}", 'danger')
        return redirect(url_for('guest_portal.index') + '#reviews')
