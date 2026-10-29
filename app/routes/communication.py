from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
import urllib.parse
from app.models import db, Booking, Guest, CommunicationLog
from app.utils.decorators import role_required
from app.utils.helpers import log_audit, send_notification

communication_bp = Blueprint('communications', __name__, url_prefix='/communications')

@communication_bp.route('/')
@communication_bp.route('/hub')
@login_required
@role_required('Super Admin', 'Manager', 'Receptionist')
def hub():
    logs = CommunicationLog.query.order_by(CommunicationLog.created_at.desc()).limit(100).all()
    in_house = Booking.query.filter_by(status='Checked-in').all()
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(20).all()
    
    total_sent = CommunicationLog.query.count()
    whatsapp_sent = CommunicationLog.query.filter_by(channel='WhatsApp').count()
    sms_sent = CommunicationLog.query.filter_by(channel='SMS').count()

    return render_template(
        'communications/hub.html',
        logs=logs,
        in_house=in_house,
        recent_bookings=recent_bookings,
        total_sent=total_sent,
        whatsapp_sent=whatsapp_sent,
        sms_sent=sms_sent
    )


@communication_bp.route('/send', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager', 'Receptionist')
def send_message():
    channel = request.form.get('channel', 'WhatsApp').strip() # WhatsApp or SMS
    recipient_name = request.form.get('recipient_name', 'Guest').strip()
    raw_phone = request.form.get('recipient_phone', '').strip()
    template_type = request.form.get('template_type', 'General').strip()
    message = request.form.get('message_content', '').strip()

    if not raw_phone or not message:
        flash('Fadlan geli lambarka taleefanka iyo fariinta aad rabto inaad dirto.', 'danger')
        return redirect(url_for('communications.hub'))

    # Clean phone: remove spaces, dashes, parentheses
    clean_phone = "".join(ch for ch in raw_phone if ch.isdigit())
    # If Somali number starting with 061 or 61, format to 25261...
    if clean_phone.startswith('061') or clean_phone.startswith('062') or clean_phone.startswith('068'):
        clean_phone = '252' + clean_phone[1:]
    elif clean_phone.startswith('61') or clean_phone.startswith('62') or clean_phone.startswith('68'):
        clean_phone = '252' + clean_phone
    elif not clean_phone.startswith('252') and len(clean_phone) <= 9:
        clean_phone = '252' + clean_phone

    # Create communication log record
    log = CommunicationLog(
        channel=channel,
        recipient_name=recipient_name,
        recipient_phone=clean_phone,
        template_type=template_type,
        message_content=message,
        status='Sent',
        sent_by=current_user.id
    )
    db.session.add(log)
    db.session.commit()

    log_audit('SEND_COMMUNICATION', 'CommunicationLog', log.id, f"Sent {channel} to {recipient_name} ({clean_phone})")

    # If WhatsApp, generate direct web link and redirect or show prompt
    if channel == 'WhatsApp':
        encoded_msg = urllib.parse.quote(message)
        wa_url = f"https://api.whatsapp.com/send?phone={clean_phone}&text={encoded_msg}"
        flash(f"Fariinta WhatsApp-ka ee {recipient_name} waa la diyaariyay! Waxaa si toos ah loogu furayaa WhatsApp Web/App.", 'success')
        return render_template('communications/redirect_whatsapp.html', wa_url=wa_url, recipient_name=recipient_name, phone=clean_phone)
    else:
        # SMS dispatch (simulated/gateway integrated)
        send_notification(
            user_id=None,
            title=f"SMS loo diray {recipient_name}",
            message=f"Fariin SMS ah ayaa loo diray {recipient_name} ({clean_phone}): {message[:60]}...",
            notif_type='info',
            link="/communications/hub"
        )
        flash(f"Fariinta SMS-ka ah si guul leh ayaa loogu diray {recipient_name} (+{clean_phone})!", 'success')
        return redirect(request.referrer or url_for('communications.hub'))

