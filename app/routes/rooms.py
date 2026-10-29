from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app.models import db, Room, RoomType, Amenity, HousekeepingTask
from app.utils.decorators import role_required
from app.utils.helpers import log_audit

rooms_bp = Blueprint('rooms', __name__, url_prefix='/rooms')

@rooms_bp.route('/')
@login_required
@role_required('Super Admin', 'Manager', 'Receptionist', 'Housekeeping')
def index():
    status_filter = request.args.get('status')
    floor_filter = request.args.get('floor')
    type_filter = request.args.get('type')

    query = Room.query

    if status_filter:
        query = query.filter_by(status=status_filter)
    if floor_filter:
        query = query.filter_by(floor=int(floor_filter))
    if type_filter:
        query = query.filter_by(room_type_id=int(type_filter))

    rooms = query.order_by(Room.room_number.asc()).all()
    room_types = RoomType.query.all()
    floors = db.session.query(Room.floor).distinct().order_by(Room.floor.asc()).all()
    floors = [f[0] for f in floors]

    total_count = Room.query.count()
    available_count = Room.query.filter_by(status='Available').count()
    occupied_count = Room.query.filter_by(status='Occupied').count()
    cleaning_count = Room.query.filter(Room.status.in_(['Cleaning']) | (Room.clean_status == 'Dirty')).count()
    maint_count = Room.query.filter(Room.status.in_(['Maintenance', 'Out of Order'])).count()

    return render_template(
        'rooms/index.html',
        rooms=rooms,
        room_types=room_types,
        floors=floors,
        total_count=total_count,
        available_count=available_count,
        occupied_count=occupied_count,
        cleaning_count=cleaning_count,
        maint_count=maint_count,
        selected_status=status_filter,
        selected_floor=floor_filter,
        selected_type=type_filter
    )


@rooms_bp.route('/status-board')
@login_required
@role_required('Super Admin', 'Manager', 'Receptionist', 'Housekeeping')
def status_board():
    """
    Visual color-coded grid matrix grouped by floors.
    """
    rooms = Room.query.order_by(Room.floor.asc(), Room.room_number.asc()).all()
    floors_dict = {}
    for r in rooms:
        if r.floor not in floors_dict:
            floors_dict[r.floor] = []
        floors_dict[r.floor].append(r)

    room_types = RoomType.query.all()
    return render_template('rooms/status_board.html', floors_dict=floors_dict, room_types=room_types)


import os
import time
from flask import current_app
from werkzeug.utils import secure_filename

@rooms_bp.route('/add', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager')
def add():
    room_number = request.form.get('room_number', '').strip()
    floor = int(request.form.get('floor', 1))
    room_type_id = int(request.form.get('room_type_id'))
    status = request.form.get('status', 'Available')
    notes = request.form.get('notes', '').strip()

    if Room.query.filter_by(room_number=room_number).first():
        flash(f'Room {room_number} already exists.', 'danger')
        return redirect(url_for('rooms.index'))

    # Handle image upload
    image_path = None
    image_file = request.files.get('room_image')
    if image_file and image_file.filename:
        ext = os.path.splitext(image_file.filename)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.webp', '.avif', '.gif']:
            safe_num = secure_filename(room_number) or 'room'
            filename = f"room_{safe_num}_{int(time.time())}{ext}"
            upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads'), 'rooms')
            os.makedirs(upload_dir, exist_ok=True)
            image_file.save(os.path.join(upload_dir, filename))
            image_path = f"/static/uploads/rooms/{filename}"

    room = Room(
        room_number=room_number,
        floor=floor,
        room_type_id=room_type_id,
        status=status,
        clean_status='Clean' if status == 'Available' else 'Dirty',
        image=image_path,
        notes=notes
    )
    db.session.add(room)
    # Also sync to room type if image was uploaded
    if image_path:
        rt = RoomType.query.get(room_type_id)
        if rt:
            rt.primary_image = image_path
    db.session.commit()
    log_audit('CREATE_ROOM', 'Room', room.id, f"Added Room {room.room_number}")
    flash(f'Room {room.room_number} added successfully.', 'success')
    return redirect(url_for('rooms.index'))


@rooms_bp.route('/<int:room_id>/edit', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager', 'Receptionist')
def edit(room_id):
    room = Room.query.get_or_404(room_id)
    room.floor = int(request.form.get('floor', room.floor))
    room.room_type_id = int(request.form.get('room_type_id', room.room_type_id))
    new_status = request.form.get('status', room.status)
    room.notes = request.form.get('notes', room.notes)
    
    # Handle image upload in edit
    image_file = request.files.get('room_image')
    if image_file and image_file.filename:
        ext = os.path.splitext(image_file.filename)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.webp', '.avif', '.gif']:
            safe_num = secure_filename(room.room_number) or 'room'
            filename = f"room_{safe_num}_{int(time.time())}{ext}"
            upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads'), 'rooms')
            os.makedirs(upload_dir, exist_ok=True)
            image_file.save(os.path.join(upload_dir, filename))
            room.image = f"/static/uploads/rooms/{filename}"
            # Immediately sync to room type so public website sees it everywhere
            if room.room_type:
                room.room_type.primary_image = room.image

    # If room status changed to Cleaning or Dirty, trigger housekeeping task
    if new_status in ['Cleaning'] and room.status != 'Cleaning':
        room.clean_status = 'Dirty'
        task = HousekeepingTask(room_id=room.id, status='Dirty', priority='High', cleaning_type='Daily Tidy')
        db.session.add(task)

    room.status = new_status
    db.session.commit()
    log_audit('UPDATE_ROOM', 'Room', room.id, f"Updated Room {room.room_number} status to {new_status}")
    flash(f'Room {room.room_number} updated.', 'success')
    return redirect(url_for('rooms.index'))


@rooms_bp.route('/<int:room_id>/delete', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager')
def delete(room_id):
    room = Room.query.get_or_404(room_id)
    if room.status == 'Occupied':
        flash(f'Cannot delete Room {room.room_number} because it is currently occupied.', 'danger')
        return redirect(url_for('rooms.index'))
    try:
        room_num = room.room_number
        db.session.delete(room)
        db.session.commit()
        log_audit('DELETE_ROOM', 'Room', room_id, f"Deleted Room {room_num}")
        flash(f'Room {room_num} deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Cannot delete Room {room.room_number}: linked to existing bookings or maintenance records.', 'warning')
    return redirect(url_for('rooms.index'))


@rooms_bp.route('/types')
@login_required
def room_types():
    types = RoomType.query.all()
    amenities = Amenity.query.all()
    return render_template('rooms/types.html', types=types, amenities=amenities)
