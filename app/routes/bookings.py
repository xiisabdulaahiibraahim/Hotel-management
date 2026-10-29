from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from datetime import datetime, date
from app.models import db, Booking, BookingRoom, Room, RoomType, Guest, Promotion, Invoice
from app.services.booking_service import search_available_rooms, create_booking_transaction
from app.utils.helpers import log_audit
from app.utils.decorators import role_required

bookings_bp = Blueprint('bookings', __name__, url_prefix='/bookings')

@bookings_bp.route('/')
@login_required
@role_required('Super Admin', 'Manager', 'Receptionist', 'Accountant')
def index():
    status = request.args.get('status')
    search_q = request.args.get('q', '').strip()

    query = Booking.query.join(Guest)

    if status:
        query = query.filter(Booking.status == status)
    if search_q:
        query = query.filter(
            (Booking.booking_reference.ilike(f'%{search_q}%')) |
            (Guest.first_name.ilike(f'%{search_q}%')) |
            (Guest.last_name.ilike(f'%{search_q}%')) |
            (Guest.phone.ilike(f'%{search_q}%'))
        )

    bookings = query.order_by(Booking.created_at.desc()).all()
    return render_template('bookings/index.html', bookings=bookings, selected_status=status, search_q=search_q)


@bookings_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        try:
            # 1. Guest Handling: existing or quick new
            guest_id = request.form.get('guest_id')
            if not guest_id or guest_id == 'new':
                first_name = request.form.get('first_name', '').strip()
                last_name = request.form.get('last_name', '').strip()
                phone = request.form.get('phone', '').strip()
                email = request.form.get('email', '').strip()
                id_number = request.form.get('id_number', '').strip()

                if not first_name or not phone:
                    flash('Guest name and phone number are required.', 'danger')
                    return redirect(url_for('bookings.new'))

                guest = Guest(
                    first_name=first_name,
                    last_name=last_name or 'Guest',
                    phone=phone,
                    email=email or f"{phone}@hotelguest.com",
                    id_number=id_number or 'ID-NOT-PROVIDED'
                )
                db.session.add(guest)
                db.session.flush()
                guest_id = guest.id
            else:
                guest_id = int(guest_id)

            # 2. Dates
            check_in_str = request.form.get('check_in_date')
            check_out_str = request.form.get('check_out_date')
            check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()

            if check_out <= check_in:
                flash('Check-out date must be after Check-in date.', 'danger')
                return redirect(url_for('bookings.new'))

            # 3. Selected Rooms
            room_ids = [int(rid) for rid in request.form.getlist('room_ids')]
            if not room_ids:
                flash('Please select at least one room.', 'danger')
                return redirect(url_for('bookings.new'))

            adults = int(request.form.get('adults', 1))
            children = int(request.form.get('children', 0))
            source = request.form.get('booking_source', 'Walk-in')
            promo_code = request.form.get('promo_code', '').strip()
            special_requests = request.form.get('special_requests', '').strip()
            deposit = float(request.form.get('deposit_amount', 0.0) or 0.0)

            # 4. Atomic Booking Execution
            booking, invoice = create_booking_transaction(
                guest_id=guest_id,
                room_ids=room_ids,
                check_in_date=check_in,
                check_out_date=check_out,
                adults=adults,
                children=children,
                booking_source=source,
                promo_code=promo_code,
                special_requests=special_requests,
                deposit_amount=deposit
            )

            flash(f'Reservation {booking.booking_reference} created successfully!', 'success')
            return redirect(url_for('bookings.show', booking_id=booking.id))

        except Exception as e:
            flash(f'Error creating booking: {str(e)}', 'danger')
            return redirect(url_for('bookings.new'))

    guests = Guest.query.order_by(Guest.first_name.asc()).all()
    room_types = RoomType.query.all()
    all_rooms = Room.query.filter_by(status='Available').order_by(Room.room_number.asc()).all()
    return render_template('bookings/new.html', guests=guests, room_types=room_types, all_rooms=all_rooms, today=date.today())


@bookings_bp.route('/<int:booking_id>')
@login_required
def show(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    invoice = Invoice.query.filter_by(booking_id=booking.id).first()
    return render_template('bookings/show.html', booking=booking, invoice=invoice)


@bookings_bp.route('/<int:booking_id>/cancel', methods=['POST'])
@login_required
def cancel(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    booking.status = 'Cancelled'
    
    # Release rooms
    for br in booking.booking_rooms:
        if br.room.status == 'Reserved':
            br.room.status = 'Available'

    db.session.commit()
    log_audit('CANCEL_BOOKING', 'Booking', booking.id, f"Cancelled booking {booking.booking_reference}")
    flash(f'Booking {booking.booking_reference} has been cancelled.', 'info')
    return redirect(url_for('bookings.show', booking_id=booking.id))


@bookings_bp.route('/calendar')
@login_required
def calendar():
    return render_template('bookings/calendar.html')
