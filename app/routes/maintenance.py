from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from app.models import db, MaintenanceTicket, Room, User
from app.utils.helpers import log_audit
from app.utils.decorators import role_required

maintenance_bp = Blueprint('maintenance', __name__, url_prefix='/maintenance')

@maintenance_bp.route('/')
@login_required
@role_required('Super Admin', 'Manager', 'Housekeeping', 'Receptionist')
def index():
    status = request.args.get('status')
    priority = request.args.get('priority')

    query = MaintenanceTicket.query

    if status:
        query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(priority=priority)

    tickets = query.order_by(MaintenanceTicket.created_at.desc()).all()
    rooms = Room.query.order_by(Room.room_number.asc()).all()
    technicians = User.query.filter(User.is_active == True).all()

    return render_template(
        'maintenance/index.html',
        tickets=tickets,
        rooms=rooms,
        technicians=technicians,
        selected_status=status,
        selected_priority=priority
    )


@maintenance_bp.route('/create', methods=['POST'])
@login_required
def create():
    room_id = request.form.get('room_id')
    issue_title = request.form.get('issue_title', '').strip()
    description = request.form.get('description', '').strip()
    priority = request.form.get('priority', 'Medium')
    assigned_to = request.form.get('assigned_to')
    estimated_cost = float(request.form.get('estimated_cost', 0.0) or 0.0)

    ticket = MaintenanceTicket(
        room_id=int(room_id) if room_id else None,
        reported_by=current_user.id,
        assigned_to=int(assigned_to) if assigned_to else None,
        issue_title=issue_title,
        description=description,
        priority=priority,
        status='Open',
        estimated_cost=estimated_cost
    )
    db.session.add(ticket)

    # If it's high or emergency priority, update room status to Maintenance
    if room_id and priority in ['High', 'Emergency']:
        room = Room.query.get(int(room_id))
        if room and room.status != 'Occupied':
            room.status = 'Maintenance'

    db.session.commit()
    log_audit('CREATE_TICKET', 'MaintenanceTicket', ticket.id, f"Issue: {ticket.issue_title}")
    flash(f'Maintenance ticket #{ticket.id} created successfully.', 'success')
    return redirect(url_for('maintenance.index'))


@maintenance_bp.route('/<int:ticket_id>/update', methods=['POST'])
@login_required
def update(ticket_id):
    ticket = MaintenanceTicket.query.get_or_404(ticket_id)
    new_status = request.form.get('status', ticket.status)
    actual_cost = float(request.form.get('actual_cost', ticket.actual_cost) or 0.0)
    resolution_notes = request.form.get('resolution_notes', '').strip()

    ticket.status = new_status
    ticket.actual_cost = actual_cost
    if resolution_notes:
        ticket.resolution_notes = resolution_notes

    if new_status in ['Resolved', 'Closed']:
        ticket.resolved_at = datetime.utcnow()
        # If room was in Maintenance, reset back to Available or Cleaning
        if ticket.room and ticket.room.status == 'Maintenance':
            ticket.room.status = 'Available'
            ticket.room.clean_status = 'Clean'

    db.session.commit()
    log_audit('UPDATE_TICKET', 'MaintenanceTicket', ticket.id, f"Ticket #{ticket.id} updated to {new_status}")
    flash(f'Ticket #{ticket.id} updated.', 'success')
    return redirect(url_for('maintenance.index'))
