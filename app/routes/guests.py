from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import db, Guest, Booking
from app.utils.helpers import log_audit
from app.utils.decorators import role_required

guests_bp = Blueprint('guests', __name__, url_prefix='/guests')

@guests_bp.route('/')
@login_required
@role_required('Super Admin', 'Manager', 'Receptionist', 'Accountant')
def index():
    search = request.args.get('q', '').strip()
    tier = request.args.get('tier')

    query = Guest.query

    if tier == 'Blacklisted':
        query = query.filter_by(is_blacklisted=True)
    elif tier:
        query = query.filter_by(vip_tier=tier)
    if search:
        query = query.filter(
            (Guest.first_name.ilike(f'%{search}%')) |
            (Guest.last_name.ilike(f'%{search}%')) |
            (Guest.email.ilike(f'%{search}%')) |
            (Guest.phone.ilike(f'%{search}%')) |
            (Guest.id_number.ilike(f'%{search}%'))
        )

    guests = query.order_by(Guest.first_name.asc()).all()
    return render_template('guests/index.html', guests=guests, search=search, selected_tier=tier)


@guests_bp.route('/<int:guest_id>')
@login_required
def profile(guest_id):
    guest = Guest.query.get_or_404(guest_id)
    total_spent = sum(b.paid_amount for b in guest.bookings)
    return render_template('guests/profile.html', guest=guest, total_spent=total_spent)


@guests_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        guest = Guest(
            first_name=request.form.get('first_name', '').strip(),
            last_name=request.form.get('last_name', '').strip(),
            email=request.form.get('email', '').strip(),
            phone=request.form.get('phone', '').strip(),
            id_type=request.form.get('id_type', 'Passport'),
            id_number=request.form.get('id_number', '').strip(),
            nationality=request.form.get('nationality', 'Somali').strip(),
            address=request.form.get('address', '').strip(),
            vip_tier=request.form.get('vip_tier', 'Standard'),
            notes=request.form.get('notes', '').strip()
        )
        db.session.add(guest)
        db.session.commit()
        log_audit('CREATE_GUEST', 'Guest', guest.id, f"Added guest {guest.full_name}")
        flash(f'Guest {guest.full_name} created successfully.', 'success')
        return redirect(url_for('guests.profile', guest_id=guest.id))

    return render_template('guests/add.html')


@guests_bp.route('/<int:guest_id>/edit', methods=['POST'])
@login_required
def edit(guest_id):
    import os, time
    from werkzeug.utils import secure_filename

    guest = Guest.query.get_or_404(guest_id)
    guest.first_name = request.form.get('first_name', guest.first_name).strip()
    guest.last_name = request.form.get('last_name', guest.last_name).strip()
    guest.email = request.form.get('email', guest.email).strip()
    guest.phone = request.form.get('phone', guest.phone).strip()
    guest.id_type = request.form.get('id_type', guest.id_type)
    guest.id_number = request.form.get('id_number', guest.id_number).strip()
    guest.nationality = request.form.get('nationality', guest.nationality).strip()
    guest.vip_tier = request.form.get('vip_tier', guest.vip_tier)
    guest.is_blacklisted = bool(request.form.get('is_blacklisted'))
    guest.notes = request.form.get('notes', guest.notes).strip()

    id_photo_base64 = request.form.get('id_photo_base64', '').strip()
    if id_photo_base64 and ',' in id_photo_base64:
        import base64
        header, encoded = id_photo_base64.split(',', 1)
        file_bytes = base64.b64decode(encoded)
        fname = f"id_cam_{guest.id}_{int(time.time())}.jpg"
        upload_dir = os.path.join('app', 'static', 'uploads', 'ids')
        os.makedirs(upload_dir, exist_ok=True)
        with open(os.path.join(upload_dir, fname), 'wb') as f:
            f.write(file_bytes)
        guest.id_photo = f"uploads/ids/{fname}"
    elif 'id_photo' in request.files:
        file = request.files['id_photo']
        if file and file.filename != '':
            ext = os.path.splitext(secure_filename(file.filename))[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.webp', '.pdf']:
                fname = f"id_{guest.id}_{int(time.time())}{ext}"
                upload_dir = os.path.join('app', 'static', 'uploads', 'ids')
                os.makedirs(upload_dir, exist_ok=True)
                file.save(os.path.join(upload_dir, fname))
                guest.id_photo = f"uploads/ids/{fname}"

    db.session.commit()
    log_audit('UPDATE_GUEST', 'Guest', guest.id, f"Updated profile for {guest.full_name}")
    flash('Guest profile updated successfully.', 'success')
    return redirect(url_for('guests.profile', guest_id=guest.id))


@guests_bp.route('/blacklist')
@login_required
@role_required('Super Admin', 'Manager', 'Receptionist')
def blacklist_hub():
    blacklisted = Guest.query.filter_by(is_blacklisted=True).order_by(Guest.updated_at.desc()).all()
    vip_platinum = Guest.query.filter_by(vip_tier='VIP Platinum').all()
    vip_gold = Guest.query.filter_by(vip_tier='Gold').all()
    vip_silver = Guest.query.filter_by(vip_tier='Silver').all()

    return render_template(
        'guests/blacklist.html',
        blacklisted=blacklisted,
        vip_platinum=vip_platinum,
        vip_gold=vip_gold,
        vip_silver=vip_silver
    )


@guests_bp.route('/blacklist/<int:guest_id>/toggle', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager')
def toggle_blacklist(guest_id):
    guest = Guest.query.get_or_404(guest_id)
    guest.is_blacklisted = not guest.is_blacklisted
    reason = request.form.get('reason', '').strip()
    if reason:
        guest.notes = (guest.notes or '') + f"\n[Blacklist Action: {reason}]"
    db.session.commit()
    log_audit('TOGGLE_BLACKLIST', 'Guest', guest.id, f"Guest {guest.full_name} blacklist status: {guest.is_blacklisted}")
    status_str = "waa lagu daray liiska mamnuuca (Blacklisted)" if guest.is_blacklisted else "waa laga saaray liiska mamnuuca"
    flash(f"Martida {guest.full_name} {status_str}.", 'info')
    return redirect(request.referrer or url_for('guests.blacklist_hub'))
