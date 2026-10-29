from datetime import datetime
from app.models import db, Invoice, InvoiceItem, Payment, Booking
from app.utils.helpers import generate_invoice_number, generate_payment_reference, log_audit

def create_invoice_for_booking(booking, deposit_amount=0.0):
    """
    Creates an initial guest folio invoice based on reserved rooms.
    """
    inv_num = generate_invoice_number()
    invoice = Invoice(
        invoice_number=inv_num,
        booking_id=booking.id,
        guest_id=booking.guest_id,
        issue_date=datetime.utcnow().date(),
        due_date=booking.check_out_date,
        subtotal=booking.subtotal_amount,
        tax_rate=5.0,
        tax_amount=booking.tax_amount,
        discount_amount=booking.discount_amount,
        total_amount=booking.total_amount,
        paid_amount=0.0,
        balance_due=booking.total_amount,
        status='Unpaid'
    )
    db.session.add(invoice)
    db.session.flush()

    # Add line items for each booked room
    for br in booking.booking_rooms:
        room_desc = f"{br.room.room_type.name} (Room {br.room.room_number}) - {br.nights} Night(s)"
        item = InvoiceItem(
            invoice_id=invoice.id,
            category='Room Charge',
            description=room_desc,
            unit_price=br.price_per_night,
            quantity=br.nights,
            total_price=br.subtotal,
            date_incurred=booking.check_in_date
        )
        db.session.add(item)

    # Process deposit payment if any
    if deposit_amount > 0:
        pay_ref = generate_payment_reference()
        payment = Payment(
            payment_reference=pay_ref,
            invoice_id=invoice.id,
            booking_id=booking.id,
            amount=deposit_amount,
            payment_method='Cash',
            transaction_reference='Advance Deposit',
            status='Completed'
        )
        db.session.add(payment)
        invoice.paid_amount = deposit_amount
        invoice.balance_due = max(invoice.total_amount - deposit_amount, 0.0)
        invoice.status = 'Partially Paid' if invoice.balance_due > 0 else 'Paid'

    return invoice


def add_item_to_folio(invoice_id, category, description, unit_price, quantity=1):
    invoice = Invoice.query.get_or_404(invoice_id)
    total = round(unit_price * quantity, 2)
    
    item = InvoiceItem(
        invoice_id=invoice.id,
        category=category,
        description=description,
        unit_price=unit_price,
        quantity=quantity,
        total_price=total,
        date_incurred=datetime.utcnow().date()
    )
    db.session.add(item)
    invoice.recalculate()
    db.session.commit()
    log_audit('ADD_FOLIO_ITEM', 'Invoice', invoice.id, f"{category}: {description} (${total})")
    return item


def process_folio_payment(invoice_id, amount, payment_method, tx_ref=None, staff_id=None):
    invoice = Invoice.query.get_or_404(invoice_id)
    booking = invoice.booking

    pay_ref = generate_payment_reference()
    payment = Payment(
        payment_reference=pay_ref,
        invoice_id=invoice.id,
        booking_id=booking.id,
        amount=amount,
        payment_method=payment_method,
        transaction_reference=tx_ref,
        status='Completed',
        received_by=staff_id
    )
    db.session.add(payment)
    db.session.flush()

    invoice.recalculate()
    booking.paid_amount = invoice.paid_amount
    db.session.commit()

    log_audit('PAYMENT_RECEIVED', 'Invoice', invoice.id, f"{pay_ref}: ${amount} via {payment_method}")
    return payment
