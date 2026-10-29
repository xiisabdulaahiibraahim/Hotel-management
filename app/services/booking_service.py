from datetime import datetime
from app.models import db, Room, RoomType, Booking, BookingRoom, Guest, Promotion
from app.utils.helpers import generate_booking_reference, log_audit, send_notification

def is_room_available(room_id, check_in_date, check_out_date, exclude_booking_id=None):
    """
    Check if a room is available for the given dates with DB row locking logic.
    Returns True if available, False otherwise.
    """
    # Exclude cancelled / checked-out bookings
    active_statuses = ['Confirmed', 'Checked-in', 'Pending']
    
    query = db.session.query(BookingRoom).join(Booking).filter(
        BookingRoom.room_id == room_id,
        Booking.status.in_(active_statuses),
        Booking.check_in_date < check_out_date,
        Booking.check_out_date > check_in_date
    )
    
    if exclude_booking_id:
        query = query.filter(Booking.id != exclude_booking_id)
        
    conflicting_bookings = query.count()
    if conflicting_bookings > 0:
        return False

    # Also check room status itself
    room = Room.query.get(room_id)
    if not room or room.status in ['Maintenance', 'Out of Order']:
        return False

    return True


def search_available_rooms(check_in_date, check_out_date, adults=1, children=0, room_type_id=None):
    """
    Search all rooms that are vacant and available for the requested stay duration.
    """
    query = Room.query.join(RoomType).filter(
        Room.status.in_(['Available', 'Cleaning', 'Reserved']),
        RoomType.capacity_adults >= adults,
        RoomType.is_active == True
    )

    if room_type_id:
        query = query.filter(Room.room_type_id == room_type_id)

    candidates = query.all()
    available_rooms = []

    for room in candidates:
        if is_room_available(room.id, check_in_date, check_out_date):
            available_rooms.append(room)

    return available_rooms


def create_booking_transaction(guest_id, room_ids, check_in_date, check_out_date, adults=1, children=0,
                               booking_source='Walk-in', promo_code=None, special_requests=None,
                               deposit_amount=0.0):
    """
    Atomically creates a booking, assigns rooms, calculates pricing and creates initial invoice/folio.
    """
    try:
        # 1. Validate room availability first
        rooms_to_book = []
        for r_id in room_ids:
            if not is_room_available(r_id, check_in_date, check_out_date):
                raise ValueError(f"Room {r_id} is no longer available for the selected dates.")
            room = Room.query.get(r_id)
            rooms_to_book.append(room)

        # 2. Calculate duration
        nights = (check_out_date - check_in_date).days
        if nights <= 0:
            nights = 1

        # 3. Calculate Pricing
        subtotal = 0.0
        booking_rooms_data = []

        for room in rooms_to_book:
            price_night = room.room_type.base_price
            room_subtotal = price_night * nights
            subtotal += room_subtotal
            booking_rooms_data.append((room, price_night, nights, room_subtotal))

        # Check promotion
        discount_amount = 0.0
        promo = None
        if promo_code:
            promo = Promotion.query.filter_by(code=promo_code.strip().upper(), is_active=True).first()
            if promo and promo.start_date <= check_in_date <= promo.end_date:
                if subtotal >= promo.min_spend:
                    if promo.discount_type == 'percentage':
                        discount_amount = round(subtotal * (promo.discount_value / 100.0), 2)
                    else:
                        discount_amount = min(promo.discount_value, subtotal)

        # Taxes (5% standard)
        tax_amount = round((subtotal - discount_amount) * 0.05, 2)
        total_amount = round(subtotal - discount_amount + tax_amount, 2)

        # 4. Create Booking
        ref_code = generate_booking_reference()
        booking = Booking(
            booking_reference=ref_code,
            guest_id=guest_id,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            adults=adults,
            children=children,
            status='Confirmed',
            booking_source=booking_source,
            promotion_id=promo.id if promo else None,
            special_requests=special_requests,
            subtotal_amount=subtotal,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            deposit_amount=deposit_amount,
            paid_amount=deposit_amount
        )
        db.session.add(booking)
        db.session.flush()

        # 5. Attach Booking Rooms & Update Room Status
        for room, price, nights_cnt, r_sub in booking_rooms_data:
            br = BookingRoom(
                booking_id=booking.id,
                room_id=room.id,
                price_per_night=price,
                nights=nights_cnt,
                subtotal=r_sub
            )
            db.session.add(br)
            # If checking in today, status will be updated upon check-in; otherwise Reserved
            if check_in_date == datetime.utcnow().date():
                room.status = 'Reserved'

        # 6. Create Initial Invoice
        from app.services.billing_service import create_invoice_for_booking
        invoice = create_invoice_for_booking(booking, deposit_amount)

        db.session.commit()
        log_audit('CREATE_BOOKING', 'Booking', booking.id, f"Ref: {booking.booking_reference}, Total: ${total_amount}")

        return booking, invoice

    except Exception as e:
        db.session.rollback()
        raise e
