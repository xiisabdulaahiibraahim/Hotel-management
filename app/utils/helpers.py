import os
import random
import string
import io
import base64
from datetime import datetime
from flask import request
from flask_login import current_user
import qrcode
from app.models import db, AuditLog, Notification, HotelSetting

def generate_booking_reference():
    timestamp = datetime.utcnow().strftime('%y%m')
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"BK-{timestamp}-{random_str}"

def generate_invoice_number():
    timestamp = datetime.utcnow().strftime('%Y%m')
    random_num = random.randint(1000, 9999)
    return f"INV-{timestamp}-{random_num}"

def generate_payment_reference():
    timestamp = datetime.utcnow().strftime('%y%m%d')
    random_num = random.randint(100, 999)
    return f"PAY-{timestamp}-{random_num}"

def format_currency(amount, currency=None):
    if amount is None:
        amount = 0.0
    if currency is None:
        currency = HotelSetting.get_value('currency_symbol', '$')
    return f"{currency}{amount:,.2f}"

def generate_qr_code_base64(data_text):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=6,
        border=2,
    )
    qr.add_data(data_text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")
    
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def log_audit(action, entity_name, entity_id=None, details=None):
    try:
        user_id = current_user.id if current_user and current_user.is_authenticated else None
        ip_addr = request.remote_addr if request else '127.0.0.1'
        log = AuditLog(
            user_id=user_id,
            action=action,
            entity_name=entity_name,
            entity_id=entity_id,
            details=str(details) if details else None,
            ip_address=ip_addr
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()

def send_notification(user_id, title, message, notif_type='info', link=None):
    try:
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notif_type,
            link=link
        )
        db.session.add(notif)
        db.session.commit()
        return notif
    except Exception as e:
        db.session.rollback()
        return None
