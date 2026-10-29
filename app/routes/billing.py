from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
import io
from app.models import (
    db, Invoice, InvoiceItem, Payment, Booking, HotelSetting, HotelService, 
    NightAuditRecord, Room, RestaurantOrder, Expense
)
from app.services.billing_service import add_item_to_folio, process_folio_payment
from app.utils.helpers import log_audit, generate_qr_code_base64, send_notification
from app.utils.decorators import role_required
from sqlalchemy import func
from datetime import datetime, date

billing_bp = Blueprint('billing', __name__, url_prefix='/billing')

@billing_bp.route('/')
@login_required
@role_required('Super Admin', 'Manager', 'Accountant', 'Receptionist')
def index():
    status = request.args.get('status')
    query = Invoice.query

    if status:
        query = query.filter_by(status=status)

    invoices = query.order_by(Invoice.created_at.desc()).all()
    total_receivable = sum(inv.balance_due for inv in invoices if inv.status != 'Void')
    total_collected = sum(inv.paid_amount for inv in invoices)

    return render_template(
        'billing/index.html',
        invoices=invoices,
        selected_status=status,
        total_receivable=total_receivable,
        total_collected=total_collected
    )


@billing_bp.route('/folio/<int:invoice_id>')
@login_required
@role_required('Super Admin', 'Manager', 'Accountant', 'Receptionist')
def folio(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    # Generate QR code for invoice validation / digital receipt
    qr_data = f"HOTEL: The Grand Horizon | INV: {invoice.invoice_number} | TOTAL: ${invoice.total_amount:.2f} | STATUS: {invoice.status}"
    qr_base64 = generate_qr_code_base64(qr_data)
    hotel_name = HotelSetting.get_value('hotel_name', 'The Grand Horizon Luxury Hotel & Resort')
    hotel_address = HotelSetting.get_value('hotel_address', 'Ocean Boulevard, Lido Coastline, Mogadishu, Somalia')
    hotel_phone = HotelSetting.get_value('hotel_phone', '+252 61 555-0100')
    hotel_email = HotelSetting.get_value('hotel_email', 'billing@grandhorizon.com')

    return render_template(
        'billing/folio.html',
        invoice=invoice,
        qr_base64=qr_base64,
        hotel_name=hotel_name,
        hotel_address=hotel_address,
        hotel_phone=hotel_phone,
        hotel_email=hotel_email
    )


@billing_bp.route('/folio/<int:invoice_id>/add-charge', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager', 'Accountant', 'Receptionist')
def add_charge(invoice_id):
    category = request.form.get('category', 'Other Fee')
    description = request.form.get('description', '').strip()
    unit_price = float(request.form.get('unit_price', 0.0) or 0.0)
    quantity = int(request.form.get('quantity', 1) or 1)

    if not description or unit_price <= 0:
        flash('Invalid charge description or price.', 'danger')
        return redirect(url_for('billing.folio', invoice_id=invoice_id))

    add_item_to_folio(invoice_id, category, description, unit_price, quantity)
    flash(f'Charge "{description}" added to guest folio successfully.', 'success')
    return redirect(url_for('billing.folio', invoice_id=invoice_id))


@billing_bp.route('/folio/<int:invoice_id>/payment', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager', 'Accountant', 'Receptionist')
def make_payment(invoice_id):
    amount = float(request.form.get('amount', 0.0) or 0.0)
    payment_method = request.form.get('payment_method', 'Cash')
    tx_ref = request.form.get('transaction_reference', '').strip()

    if amount <= 0:
        flash('Payment amount must be greater than zero.', 'danger')
        return redirect(url_for('billing.folio', invoice_id=invoice_id))

    payment = process_folio_payment(
        invoice_id=invoice_id,
        amount=amount,
        payment_method=payment_method,
        tx_ref=tx_ref,
        staff_id=current_user.id
    )

    flash(f'Payment of ${amount:,.2f} recorded via {payment_method}. Ref: {payment.payment_reference}', 'success')
    return redirect(url_for('billing.folio', invoice_id=invoice_id))


@billing_bp.route('/invoice/<int:invoice_id>/print')
@login_required
@role_required('Super Admin', 'Manager', 'Accountant', 'Receptionist')
def print_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    qr_data = f"HMS-VERIFY-INV:{invoice.invoice_number}-AMT:{invoice.total_amount}-BAL:{invoice.balance_due}"
    qr_base64 = generate_qr_code_base64(qr_data)
    hotel_name = HotelSetting.get_value('hotel_name', 'The Grand Horizon Luxury Hotel & Resort')
    hotel_address = HotelSetting.get_value('hotel_address', 'Ocean Boulevard, Lido Coastline, Mogadishu, Somalia')
    hotel_phone = HotelSetting.get_value('hotel_phone', '+252 61 555-0100')
    hotel_email = HotelSetting.get_value('hotel_email', 'billing@grandhorizon.com')

    return render_template(
        'billing/invoice_print.html',
        invoice=invoice,
        qr_base64=qr_base64,
        hotel_name=hotel_name,
        hotel_address=hotel_address,
        hotel_phone=hotel_phone,
        hotel_email=hotel_email
    )


@billing_bp.route('/fees')
@login_required
@role_required('Super Admin', 'Manager', 'Accountant', 'Receptionist')
def fees():
    services = HotelService.query.order_by(HotelService.category.asc(), HotelService.name.asc()).all()
    categories = ['Laundry', 'Spa & Wellness', 'Airport Transport', 'Surcharges & Fines', 'Minibar & Dining', 'Other Fee']
    return render_template('billing/fees.html', services=services, categories=categories)


@billing_bp.route('/fees/add', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager', 'Accountant')
def add_fee():
    name = request.form.get('name', '').strip()
    category = request.form.get('category', 'Other Fee')
    price = float(request.form.get('price', 0.0) or 0.0)
    unit_type = request.form.get('unit_type', 'per service')
    description = request.form.get('description', '').strip()
    is_active = bool(request.form.get('is_active', True))

    if not name or price < 0:
        flash('Please enter a valid fee name and rate.', 'danger')
        return redirect(url_for('billing.fees'))

    svc = HotelService(
        name=name,
        category=category,
        price=price,
        unit_type=unit_type,
        description=description,
        is_active=is_active
    )
    db.session.add(svc)
    db.session.commit()
    log_audit('CREATE_FEE', 'HotelService', svc.id, f"Created fee {svc.name} (${svc.price})")
    flash(f'Hotel fee / service "{name}" added successfully.', 'success')
    return redirect(url_for('billing.fees'))


@billing_bp.route('/fees/<int:fee_id>/edit', methods=['POST'])
@login_required
def edit_fee(fee_id):
    svc = HotelService.query.get_or_404(fee_id)
    svc.name = request.form.get('name', svc.name).strip()
    svc.category = request.form.get('category', svc.category)
    svc.price = float(request.form.get('price', svc.price) or svc.price)
    svc.unit_type = request.form.get('unit_type', svc.unit_type)
    svc.description = request.form.get('description', svc.description)
    svc.is_active = bool(request.form.get('is_active'))
    db.session.commit()
    log_audit('UPDATE_FEE', 'HotelService', svc.id, f"Updated fee {svc.name}")
    flash(f'Fee "{svc.name}" updated successfully.', 'success')
    return redirect(url_for('billing.fees'))


@billing_bp.route('/fees/<int:fee_id>/delete', methods=['POST'])
@login_required
def delete_fee(fee_id):
    svc = HotelService.query.get_or_404(fee_id)
    name = svc.name
    db.session.delete(svc)
    db.session.commit()
    log_audit('DELETE_FEE', 'HotelService', fee_id, f"Deleted fee {name}")
    flash(f'Fee "{name}" removed successfully.', 'success')
    return redirect(url_for('billing.fees'))


# ============================================================
# NIGHT AUDIT & DAILY CLOSE (XISAAB-XIRKA HABENKII)
# ============================================================

@billing_bp.route('/night-audit')
@login_required
@role_required('Super Admin', 'Manager', 'Accountant')
def night_audit():
    today = datetime.utcnow().date()
    
    # 1. In-house guests to be audited
    in_house = Booking.query.filter_by(status='Checked-in').all()
    total_rooms = Room.query.count() or 1
    occupied_count = len(in_house)
    occupancy_rate = round(occupied_count / total_rooms * 100, 1)

    # 2. Expected nightly room revenue
    expected_room_rev = 0.0
    for b in in_house:
        for br in b.booking_rooms:
            expected_room_rev += br.price_per_night

    # 3. Today's Restaurant & F&B sales
    today_orders = RestaurantOrder.query.filter(
        func.date(RestaurantOrder.created_at) == today,
        RestaurantOrder.status != 'Cancelled'
    ).all()
    today_fb_sales = sum(o.total_amount for o in today_orders)

    # 4. Today's Payments collected by method
    today_payments = Payment.query.filter(
        func.date(Payment.payment_date) == today,
        Payment.status == 'Completed'
    ).all()
    total_payments = sum(p.amount for p in today_payments)

    payment_breakdown = {}
    for p in today_payments:
        payment_breakdown[p.payment_method] = payment_breakdown.get(p.payment_method, 0.0) + p.amount

    # 5. Today's Expenses
    today_expenses = Expense.query.filter(Expense.expense_date == today).all()
    total_expenses = sum(e.amount for e in today_expenses)

    # 6. Check if audit was already performed today
    today_audit = NightAuditRecord.query.filter_by(audit_date=today).first()
    past_audits = NightAuditRecord.query.order_by(NightAuditRecord.audit_date.desc()).limit(15).all()

    return render_template(
        'billing/night_audit.html',
        today=today,
        in_house=in_house,
        total_rooms=total_rooms,
        occupied_count=occupied_count,
        occupancy_rate=occupancy_rate,
        expected_room_rev=expected_room_rev,
        today_fb_sales=today_fb_sales,
        today_payments=today_payments,
        total_payments=total_payments,
        payment_breakdown=payment_breakdown,
        today_expenses=today_expenses,
        total_expenses=total_expenses,
        today_audit=today_audit,
        past_audits=past_audits
    )


@billing_bp.route('/night-audit/execute', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager', 'Accountant')
def execute_night_audit():
    today = datetime.utcnow().date()
    force = request.form.get('force') == 'true'

    # Check existing audit for today
    existing = NightAuditRecord.query.filter_by(audit_date=today).first()
    if existing and not force:
        flash(f'Xisaab-xirka habeenkii ee maanta ({today}) horey ayaa loo sameeyay.', 'warning')
        return redirect(url_for('billing.night_audit'))

    in_house = Booking.query.filter_by(status='Checked-in').all()
    total_rooms = Room.query.count() or 1
    occupied_count = len(in_house)
    occupancy_rate = round(occupied_count / total_rooms * 100, 1)

    # Post Room Charges to active folios
    posted_room_rev = 0.0
    for b in in_house:
        # Find active invoice or create one
        inv = Invoice.query.filter_by(booking_id=b.id).first()
        if not inv:
            inv_count = Invoice.query.count() + 1001
            inv = Invoice(
                invoice_number=f"INV-{inv_count}",
                booking_id=b.id,
                guest_id=b.guest_id,
                issue_date=today,
                due_date=b.check_out_date,
                status='Unpaid'
            )
            db.session.add(inv)
            db.session.flush()

        for br in b.booking_rooms:
            room_num = br.room.room_number if br.room else 'Suite'
            # Check if room charge was already posted today to prevent double charge
            already_posted = InvoiceItem.query.filter(
                InvoiceItem.invoice_id == inv.id,
                InvoiceItem.category == 'Room Charge',
                InvoiceItem.date_incurred == today
            ).first()

            if not already_posted:
                add_item_to_folio(
                    invoice_id=inv.id,
                    category='Room Charge',
                    description=f"Night Audit Room Charge ({today}) - Room {room_num}",
                    unit_price=br.price_per_night,
                    quantity=1
                )
                posted_room_rev += br.price_per_night

    # Today's F&B sales
    today_orders = RestaurantOrder.query.filter(
        func.date(RestaurantOrder.created_at) == today,
        RestaurantOrder.status != 'Cancelled'
    ).all()
    today_fb = sum(o.total_amount for o in today_orders)

    # Today's Payments collected
    today_payments = Payment.query.filter(
        func.date(Payment.payment_date) == today,
        Payment.status == 'Completed'
    ).all()
    total_paid = sum(p.amount for p in today_payments)

    notes = request.form.get('notes', 'Routine End-of-Day Night Audit Closeout').strip()
    gross_total = posted_room_rev + today_fb

    if existing:
        audit_rec = existing
        audit_rec.performed_at = datetime.utcnow()
        audit_rec.performed_by_id = current_user.id
        audit_rec.occupied_rooms_count = occupied_count
        audit_rec.total_rooms_count = total_rooms
        audit_rec.occupancy_rate = occupancy_rate
        audit_rec.room_charges_posted = posted_room_rev
        audit_rec.restaurant_sales = today_fb
        audit_rec.total_revenue = gross_total
        audit_rec.payments_collected = total_paid
        audit_rec.notes = notes
    else:
        audit_rec = NightAuditRecord(
            audit_date=today,
            performed_at=datetime.utcnow(),
            performed_by_id=current_user.id,
            occupied_rooms_count=occupied_count,
            total_rooms_count=total_rooms,
            occupancy_rate=occupancy_rate,
            room_charges_posted=posted_room_rev,
            restaurant_sales=today_fb,
            total_revenue=gross_total,
            payments_collected=total_paid,
            notes=notes
        )
        db.session.add(audit_rec)

    db.session.commit()

    log_audit('NIGHT_AUDIT_EXECUTED', 'NightAuditRecord', audit_rec.id, f"Executed Night Audit for {today}. Room Charges: ${posted_room_rev:,.2f}, F&B: ${today_fb:,.2f}, Total: ${gross_total:,.2f}")
    send_notification(
        user_id=None,
        title=f"Xisaab-Xirka Habeenkii Waa La Fuliyay ({today})",
        message=f"Xisaab-xirka habeenkii ee taariikhda {today} si guul leh ayaa loo dhamaystiray. Qolalka hoyday: {occupied_count}/{total_rooms} ({occupancy_rate}%). Wadarta dakhliga: ${gross_total:,.2f}.",
        notif_type='success',
        link="/billing/night-audit"
    )

    flash(f"Xisaab-xirka habeenkii ee {today} si buuxda ayaa loo fuliyay! Biilasha qolalka ({len(in_house)} qol) waa la post-gareeyay.", 'success')
    return redirect(url_for('billing.night_audit'))


@billing_bp.route('/night-audit/<int:audit_id>/report')
@login_required
@role_required('Super Admin', 'Manager', 'Accountant')
def night_audit_report(audit_id):
    audit = NightAuditRecord.query.get_or_404(audit_id)
    hotel_name = HotelSetting.get_value('hotel_name', 'The Grand Horizon Luxury Hotel & Resort')
    hotel_address = HotelSetting.get_value('hotel_address', 'Ocean Boulevard, Lido Coastline, Mogadishu, Somalia')
    hotel_phone = HotelSetting.get_value('hotel_phone', '+252 61 555-0100')

    # Payments of that audit date
    payments = Payment.query.filter(
        func.date(Payment.payment_date) == audit.audit_date,
        Payment.status == 'Completed'
    ).all()

    payment_breakdown = {}
    for p in payments:
        payment_breakdown[p.payment_method] = payment_breakdown.get(p.payment_method, 0.0) + p.amount

    return render_template(
        'billing/night_audit_report.html',
        audit=audit,
        hotel_name=hotel_name,
        hotel_address=hotel_address,
        hotel_phone=hotel_phone,
        payments=payments,
        payment_breakdown=payment_breakdown
    )



# ==========================================
# SECURITY DEPOSIT ESCROW HUB
# ==========================================

@billing_bp.route('/deposits')
@login_required
@role_required('Super Admin', 'Manager', 'Accountant', 'Receptionist')
def deposits_hub():
    from app.models.booking import CheckinRecord
    
    records = CheckinRecord.query.filter(CheckinRecord.deposit_collected > 0).order_by(CheckinRecord.actual_check_in.desc()).all()
    
    held_records = [r for r in records if r.deposit_status == 'Held']
    refunded_records = [r for r in records if r.deposit_status == 'Refunded']
    applied_records = [r for r in records if r.deposit_status == 'Applied to Folio']
    
    total_held = sum(r.deposit_collected for r in held_records)
    total_refunded = sum(r.deposit_refunded for r in refunded_records)
    total_applied = sum(r.deposit_collected for r in applied_records)

    return render_template(
        'billing/deposits.html',
        records=records,
        held_records=held_records,
        refunded_records=refunded_records,
        applied_records=applied_records,
        total_held=total_held,
        total_refunded=total_refunded,
        total_applied=total_applied
    )


@billing_bp.route('/deposits/<int:record_id>/refund', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager', 'Accountant', 'Receptionist')
def refund_deposit(record_id):
    from app.models.booking import CheckinRecord
    record = CheckinRecord.query.get_or_404(record_id)
    
    deposit_amt = record.deposit_collected
    record.deposit_refunded = deposit_amt
    record.deposit_status = 'Refunded'
    db.session.commit()
    
    log_audit('REFUND_DEPOSIT', 'CheckinRecord', record.id, f"Refunded security deposit of ${deposit_amt:.2f} to {record.booking.guest.full_name if record.booking and record.booking.guest else 'Guest'}")
    flash(f"Deebaajigii dhan ${deposit_amt:,.2f} si buuxda ayaa dib loogu celiyay macmiilka!", 'success')
    return redirect(request.referrer or url_for('billing.deposits_hub'))


@billing_bp.route('/deposits/<int:record_id>/apply', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager', 'Accountant', 'Receptionist')
def apply_deposit_to_folio(record_id):
    from app.models.booking import CheckinRecord
    from app.services.billing_service import process_folio_payment
    
    record = CheckinRecord.query.get_or_404(record_id)
    booking = record.booking
    invoice = Invoice.query.filter_by(booking_id=booking.id).first() if booking else None
    
    if not invoice:
        flash('Invoice for this booking not found.', 'danger')
        return redirect(url_for('billing.deposits_hub'))
        
    deposit_amt = record.deposit_collected
    process_folio_payment(
        invoice_id=invoice.id,
        amount=deposit_amt,
        payment_method='Deposit Credit',
        received_by=current_user.id,
        reference_notes=f"Security Deposit Applied towards Folio (Ref: {booking.booking_reference})"
    )
    
    record.deposit_status = 'Applied to Folio'
    db.session.commit()
    
    log_audit('APPLY_DEPOSIT_FOLIO', 'CheckinRecord', record.id, f"Applied deposit of ${deposit_amt:.2f} to Folio #{invoice.id}")
    flash(f"Deebaajigii dhan ${deposit_amt:,.2f} waxaa toos loogu jaray biilka guud ee qolka (#{booking.booking_reference})!", 'success')
    return redirect(request.referrer or url_for('billing.deposits_hub'))


# ==========================================
# STAY POLICIES & SURCHARGE FEES
# ==========================================

@billing_bp.route('/policies', methods=['GET', 'POST'])
@login_required
@role_required('Super Admin', 'Manager', 'Accountant')
def policies_hub():
    if request.method == 'POST':
        keys = [
            'standard_checkin_time', 'standard_checkout_time',
            'early_checkin_surcharge_morning', 'early_checkin_surcharge_afternoon',
            'late_checkout_surcharge_afternoon', 'late_checkout_surcharge_evening',
            'standard_security_deposit', 'deposit_policy_notes'
        ]
        for k in keys:
            if k in request.form:
                HotelSetting.set_value(k, request.form[k].strip())
        
        log_audit('UPDATE_STAY_POLICIES', 'HotelSetting', None, "Updated stay policies and surcharge rates")
        flash('Siyaasadda joogitaanka iyo khidmadaha qolalka si guul leh ayaa loo keydiyay!', 'success')
        return redirect(url_for('billing.policies_hub'))

    settings = {
        'standard_checkin_time': HotelSetting.get_value('standard_checkin_time', '14:00'),
        'standard_checkout_time': HotelSetting.get_value('standard_checkout_time', '11:00'),
        'early_checkin_surcharge_morning': HotelSetting.get_value('early_checkin_surcharge_morning', '35.00'),
        'early_checkin_surcharge_afternoon': HotelSetting.get_value('early_checkin_surcharge_afternoon', '15.00'),
        'late_checkout_surcharge_afternoon': HotelSetting.get_value('late_checkout_surcharge_afternoon', '20.00'),
        'late_checkout_surcharge_evening': HotelSetting.get_value('late_checkout_surcharge_evening', '40.00'),
        'standard_security_deposit': HotelSetting.get_value('standard_security_deposit', '50.00'),
        'deposit_policy_notes': HotelSetting.get_value('deposit_policy_notes', 'Refundable deposit collected at check-in for incidentals, minibar, or room damages.')
    }
    
    return render_template('billing/policies.html', settings=settings)
