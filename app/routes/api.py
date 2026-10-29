from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime
from app.models import db, Booking, Room, Notification, MenuItem, Guest
from app.services.booking_service import search_available_rooms

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/calendar/events')
@login_required
def calendar_events():
    """
    Returns bookings formatted for FullCalendar.
    """
    bookings = Booking.query.filter(Booking.status.in_(['Confirmed', 'Checked-in', 'Checked-out'])).all()
    events = []

    status_colors = {
        'Checked-in': '#3b82f6', # Blue
        'Confirmed': '#10b981',  # Emerald green
        'Checked-out': '#64748b',# Slate grey
        'Pending': '#f59e0b'     # Amber
    }

    for b in bookings:
        room_nums = ", ".join(br.room.room_number for br in b.booking_rooms if br.room)
        events.append({
            'id': b.id,
            'title': f"#{b.booking_reference} - {b.guest.full_name if b.guest else 'Guest'} (Rm {room_nums})",
            'start': b.check_in_date.isoformat(),
            'end': b.check_out_date.isoformat(),
            'url': f"/bookings/{b.id}",
            'backgroundColor': status_colors.get(b.status, '#d97706'),
            'borderColor': status_colors.get(b.status, '#d97706')
        })

    return jsonify(events)


@api_bp.route('/rooms/available')
def check_availability():
    check_in_str = request.args.get('check_in')
    check_out_str = request.args.get('check_out')
    type_id = request.args.get('type_id')

    if not check_in_str or not check_out_str:
        return jsonify({'error': 'Missing dates'}), 400

    try:
        check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
        room_type_id = int(type_id) if type_id else None

        rooms = search_available_rooms(check_in, check_out, room_type_id=room_type_id)
        return jsonify([r.to_dict() for r in rooms])
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/notifications/unread')
@login_required
def unread_notifications():
    notifs = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(Notification.created_at.desc()).limit(10).all()
    return jsonify([n.to_dict() for n in notifs])


@api_bp.route('/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notif_id):
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id == current_user.id:
        notif.is_read = True
        db.session.commit()
    return jsonify({'success': True})


@api_bp.route('/guests/search')
@login_required
def search_guests():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    
    guests = Guest.query.filter(
        (Guest.first_name.ilike(f'%{q}%')) |
        (Guest.last_name.ilike(f'%{q}%')) |
        (Guest.phone.ilike(f'%{q}%'))
    ).limit(10).all()

    return jsonify([g.to_dict() for g in guests])
