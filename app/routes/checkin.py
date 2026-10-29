from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from app.models import db, Booking, Room, CheckinRecord, HousekeepingTask, Invoice
from app.services.billing_service import add_item_to_folio
from app.utils.helpers import log_audit
from app.utils.decorators import role_required

checkin_bp = Blueprint('checkin', __name__, url_prefix='/frontdesk')

@checkin_bp.route('/')
@login_required
@role_required('Super Admin', 'Manager', 'Receptionist')
def index():
    today = datetime.utcnow().date()
    # Expected arrivals today
    arrivals = Booking.query.filter(
        Booking.check_in_date <= today,
        Booking.status.in_(['Confirmed', 'Pending'])
    ).all()

    # In-house guests (eligible for check-out)
    in_house = Booking.query.filter_by(status='Checked-in').all()
    available_rooms = Room.query.filter_by(status='Available').order_by(Room.room_number.asc()).all()

    return render_template('checkin/index.html', arrivals=arrivals, in_house=in_house, available_rooms=available_rooms, today=today)


@checkin_bp.route('/registration-card/<int:booking_id>')
@login_required
def registration_card(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    hotel_name = "The Grand Horizon Luxury Hotel & Resort"
    hotel_address = "Ocean Boulevard, Lido Coastline, Mogadishu, Somalia"
    hotel_phone = "+252 61 555-0100"
    try:
        from app.models import HotelSetting
        hotel_name = HotelSetting.get_value('hotel_name', hotel_name)
        hotel_address = HotelSetting.get_value('hotel_address', hotel_address)
        hotel_phone = HotelSetting.get_value('hotel_phone', hotel_phone)
    except Exception:
        pass

    return render_template(
        'checkin/registration_card.html',
        booking=booking,
        hotel_name=hotel_name,
        hotel_address=hotel_address,
        hotel_phone=hotel_phone,
        now=datetime.utcnow()
    )


@checkin_bp.route('/checkin/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def checkin_guest(booking_id):
    import os
    import time
    from werkzeug.utils import secure_filename
    booking = Booking.query.get_or_404(booking_id)

    if booking.status == 'Checked-in':
        flash('Guest is already checked in.', 'info')
        return redirect(url_for('checkin.index'))

    if request.method == 'POST':
        key_card = request.form.get('key_card_number', '').strip()
        id_verified = bool(request.form.get('id_verified'))
        early_fee = float(request.form.get('early_checkin_fee', 0.0) or 0.0)
        deposit_amt = float(request.form.get('deposit_amount', 0.0) or 0.0)
        notes = request.form.get('notes', '').strip()

        # Update Guest ID details if provided
        if booking.guest:
            if request.form.get('id_type'):
                booking.guest.id_type = request.form.get('id_type').strip()
            if request.form.get('id_number'):
                booking.guest.id_number = request.form.get('id_number').strip()
            if request.form.get('nationality'):
                booking.guest.nationality = request.form.get('nationality').strip()

            # Handle ID / Passport Photo upload or Live Camera Scan (Base64)
            id_photo_base64 = request.form.get('id_photo_base64', '').strip()
            if id_photo_base64 and ',' in id_photo_base64:
                import base64
                header, encoded = id_photo_base64.split(',', 1)
                file_bytes = base64.b64decode(encoded)
                fname = f"id_cam_{booking.guest_id}_{int(time.time())}.jpg"
                upload_dir = os.path.join('app', 'static', 'uploads', 'ids')
                os.makedirs(upload_dir, exist_ok=True)
                with open(os.path.join(upload_dir, fname), 'wb') as f:
                    f.write(file_bytes)
                booking.guest.id_photo = f"uploads/ids/{fname}"
            elif 'id_photo' in request.files:
                file = request.files['id_photo']
                if file and file.filename != '':
                    ext = os.path.splitext(secure_filename(file.filename))[1].lower()
                    if ext in ['.jpg', '.jpeg', '.png', '.webp', '.pdf']:
                        fname = f"id_{booking.guest_id}_{int(time.time())}{ext}"
                        upload_dir = os.path.join('app', 'static', 'uploads', 'ids')
                        os.makedirs(upload_dir, exist_ok=True)
                        file.save(os.path.join(upload_dir, fname))
                        booking.guest.id_photo = f"uploads/ids/{fname}"

        # Update Booking status & deposit
        booking.status = 'Checked-in'
        if deposit_amt > 0:
            booking.deposit_amount = (booking.deposit_amount or 0.0) + deposit_amt

        # Update Rooms to Occupied
        for br in booking.booking_rooms:
            br.room.status = 'Occupied'
            br.room.key_card_code = key_card

        # Create check-in record
        record = CheckinRecord(
            booking_id=booking.id,
            room_id=booking.booking_rooms[0].room_id if booking.booking_rooms else 1,
            actual_check_in=datetime.utcnow(),
            key_card_number=key_card,
            id_verified=id_verified,
            early_checkin_fee=early_fee,
            deposit_collected=deposit_amt,
            deposit_refunded=0.0,
            deposit_status='Held' if deposit_amt > 0 else 'None',
            checked_in_by=current_user.id,
            notes=notes
        )
        db.session.add(record)

        # Add early check-in fee to folio if applicable
        if early_fee > 0:
            invoice = Invoice.query.filter_by(booking_id=booking.id).first()
            if invoice:
                add_item_to_folio(invoice.id, 'Other Fee', 'Early Check-in Surcharge', early_fee, 1)

        db.session.commit()
        log_audit('CHECK_IN', 'Booking', booking.id, f"Checked in booking {booking.booking_reference}, Key Card: {key_card}, Deposit: ${deposit_amt:.2f}")
        flash(f'Guest checked in successfully! Key Card: {key_card}. Deposit collected: ${deposit_amt:.2f}', 'success')
        return redirect(url_for('checkin.index'))

    current_hour = datetime.now().hour
    suggested_early_fee = 35.00 if current_hour < 10 else (15.00 if current_hour < 13 else 0.00)
    return render_template('checkin/checkin_form.html', booking=booking, suggested_early_fee=suggested_early_fee)


@checkin_bp.route('/checkout/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def checkout_guest(booking_id):
    from app.services.billing_service import process_folio_payment
    booking = Booking.query.get_or_404(booking_id)
    invoice = Invoice.query.filter_by(booking_id=booking.id).first()

    if request.method == 'POST':
        late_fee = float(request.form.get('late_checkout_fee', 0.0) or 0.0)
        deposit_action = request.form.get('deposit_action', 'refund') # refund or apply_to_folio
        notes = request.form.get('notes', '').strip()

        # Handle Security Deposit Action if held
        record = booking.checkin_record
        deposit_held = record.deposit_collected if (record and record.deposit_status == 'Held') else 0.0

        if deposit_held > 0:
            if deposit_action == 'apply_to_folio' and invoice:
                # Apply deposit directly against invoice balance
                applied_amt = min(deposit_held, invoice.balance_due) if invoice.balance_due > 0 else deposit_held
                process_folio_payment(invoice.id, applied_amt, 'Deposit Credit', current_user.id, f'Deposit applied to final settlement (Ref #{booking.booking_reference})')
                record.deposit_status = 'Applied to Folio'
                record.deposit_refunded = max(0.0, deposit_held - applied_amt)
            elif deposit_action == 'refund':
                record.deposit_refunded = deposit_held
                record.deposit_status = 'Refunded'

        # If there's an outstanding balance and user didn't explicitly settle or override
        if invoice and invoice.balance_due > 0 and not request.form.get('confirm_unpaid_checkout'):
            flash(f'Cannot complete check-out. There is an outstanding balance of ${invoice.balance_due:,.2f}. Settle payment first or confirm override.', 'danger')
            return render_template('checkin/checkout_form.html', booking=booking, invoice=invoice, suggested_late_fee=0.0)

        if late_fee > 0 and invoice:
            add_item_to_folio(invoice.id, 'Other Fee', 'Late Check-out Surcharge', late_fee, 1)

        # 1. Update Booking status
        booking.status = 'Checked-out'

        # 2. Update Rooms to Cleaning & dirty
        for br in booking.booking_rooms:
            room = br.room
            room.status = 'Cleaning'
            room.clean_status = 'Dirty'
            room.key_card_code = None

            # 3. Auto-assign Housekeeping Task!
            hk_task = HousekeepingTask(
                room_id=room.id,
                status='Dirty',
                priority='High',
                cleaning_type='Check-out Deep Clean',
                notes=f'Auto generated upon check-out of Booking {booking.booking_reference}'
            )
            db.session.add(hk_task)

        # 4. Update check-in record checkout time
        if record:
            record.actual_check_out = datetime.utcnow()
            record.checked_out_by = current_user.id
            record.late_checkout_fee = late_fee
            if notes:
                record.notes = (record.notes or '') + '\n' + notes

        db.session.commit()
        log_audit('CHECK_OUT', 'Booking', booking.id, f"Checked out booking {booking.booking_reference}. Rooms set to Cleaning.")
        flash(f'Guest checked out successfully! Rooms set to Cleaning and sent to Housekeeping queue.', 'success')
        return redirect(url_for('checkin.index'))

    current_hour = datetime.now().hour
    suggested_late_fee = 40.00 if current_hour >= 15 else (20.00 if current_hour >= 12 else 0.00)
    return render_template('checkin/checkout_form.html', booking=booking, invoice=invoice, suggested_late_fee=suggested_late_fee)


@checkin_bp.route('/shift-room/<int:booking_id>', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager', 'Receptionist')
def shift_room(booking_id):
    from app.utils.helpers import send_notification
    booking = Booking.query.get_or_404(booking_id)
    if booking.status != 'Checked-in':
        flash('Qol-beddelka waxaa la samayn karaa oo kaliya martida hadda qolalka ku hoyata (Checked-in).', 'danger')
        return redirect(request.referrer or url_for('checkin.index'))

    new_room_id = request.form.get('new_room_id', type=int)
    reason = request.form.get('reason', 'Guest Request / Room Upgrade').strip()
    key_card = request.form.get('key_card_number', '').strip()
    adjust_rate = request.form.get('adjust_rate') == 'on'

    new_room = Room.query.get_or_404(new_room_id)
    if new_room.status != 'Available':
        flash(f'Qolka {new_room.room_number} hadda ma bannaana (Status: {new_room.status}). Fadlan dooro qol bannaan.', 'danger')
        return redirect(request.referrer or url_for('checkin.index'))

    # Determine old room
    old_room = None
    if booking.checkin_record and booking.checkin_record.room:
        old_room = booking.checkin_record.room
    elif booking.booking_rooms:
        old_room = booking.booking_rooms[0].room

    old_room_num = old_room.room_number if old_room else "N/A"

    # 1. Update Old Room -> Cleaning & Dirty
    if old_room:
        old_room.status = 'Cleaning'
        old_room.clean_status = 'Dirty'
        old_room.key_card_code = None

        # Automatically assign high-priority housekeeping task
        hk_task = HousekeepingTask(
            room_id=old_room.id,
            status='Dirty',
            priority='High',
            cleaning_type='Room Shift Turnover',
            notes=f"Qol-Beddel: Martidii ({booking.guest.full_name}) waxay u guurtay Rm {new_room.room_number}. Fadlan nadiifi qolka {old_room.room_number}."
        )
        db.session.add(hk_task)

    # 2. Update New Room -> Occupied
    new_room.status = 'Occupied'
    new_room.clean_status = 'Clean'
    if key_card:
        new_room.key_card_code = key_card

    # 3. Update Checkin Record
    if booking.checkin_record:
        booking.checkin_record.room_id = new_room.id
        if key_card:
            booking.checkin_record.key_card_number = key_card
        shift_note = f"\n[Qol-Beddel {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}] Laga soo wareejiyay Rm {old_room_num} -> Rm {new_room.room_number}. Sababta: {reason} (Waxaa wareejiyay: {current_user.username})"
        booking.checkin_record.notes = (booking.checkin_record.notes or '') + shift_note

    # 4. Update BookingRoom & Folio adjustment if requested
    if booking.booking_rooms:
        for br in booking.booking_rooms:
            if old_room and br.room_id == old_room.id:
                br.room_id = new_room.id
                if adjust_rate:
                    old_price = br.price_per_night
                    new_price = new_room.room_type.base_price if new_room.room_type else old_price
                    br.price_per_night = new_price
                    rate_diff = new_price - old_price
                    if rate_diff != 0:
                        invoice = Invoice.query.filter_by(booking_id=booking.id).first()
                        if invoice:
                            desc = f"Room Shift Adjustment (Rm {old_room_num} -> {new_room.room_number})"
                            add_item_to_folio(invoice.id, 'Room Charge', desc, rate_diff, 1)
                break

    db.session.commit()
    log_audit('ROOM_SHIFT', 'Booking', booking.id, f"Shifted guest {booking.guest.full_name} from Rm {old_room_num} to Rm {new_room.room_number}. Reason: {reason}")
    send_notification(
        user_id=None,
        title=f"Qol-Beddel Waa La Sameeyay (Rm {old_room_num} -> Rm {new_room.room_number})",
        message=f"Martida {booking.guest.full_name} waxaa laga wareejiyay qolka {old_room_num} waxaana la dejiyay qolka {new_room.room_number}. Sababta: {reason}.",
        notif_type='info',
        link="/frontdesk/"
    )
    flash(f"Martida {booking.guest.full_name} si guul leh ayaa looga wareejiyay Qolka {old_room_num} loona dejiyay Qolka {new_room.room_number}!", 'success')
    return redirect(request.referrer or url_for('checkin.index'))



@checkin_bp.route('/room-shift', methods=['GET', 'POST'])
@login_required
@role_required('Super Admin', 'Manager', 'Receptionist')
def room_shift_hub():
    if request.method == 'POST':
        booking_id = request.form.get('booking_id', type=int)
        if booking_id:
            return shift_room(booking_id)

    in_house = Booking.query.filter_by(status='Checked-in').order_by(Booking.check_in_date.desc()).all()
    available_rooms = Room.query.filter_by(status='Available').order_by(Room.floor.asc(), Room.room_number.asc()).all()
    from app.models import AuditLog
    shift_logs = AuditLog.query.filter_by(action='ROOM_SHIFT').order_by(AuditLog.created_at.desc()).limit(25).all()

    return render_template(
        'checkin/room_shift.html',
        in_house=in_house,
        available_rooms=available_rooms,
        shift_logs=shift_logs
    )
