from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import db, User, Role
from app.utils.helpers import log_audit
from datetime import datetime

users_bp = Blueprint('users', __name__, url_prefix='/users')

def admin_required():
    return current_user.is_authenticated and (current_user.has_role('Super Admin', 'Manager') or current_user.role_id == 1)

@users_bp.route('/')
@login_required
def index():
    if not admin_required():
        flash('Access restricted. Admin credentials required to manage system users & roles.', 'danger')
        return redirect(url_for('dashboard.index'))

    users = User.query.order_by(User.id.asc()).all()
    roles = Role.query.order_by(Role.id.asc()).all()

    total_users = len(users)
    active_users = sum(1 for u in users if u.is_active)
    admin_count = sum(1 for u in users if u.role and u.role.name in ['Super Admin', 'Manager'])
    staff_count = total_users - admin_count

    return render_template(
        'users/index.html',
        users=users,
        roles=roles,
        total_users=total_users,
        active_users=active_users,
        admin_count=admin_count,
        staff_count=staff_count
    )

@users_bp.route('/create', methods=['POST'])
@login_required
def create_user():
    if not admin_required():
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('dashboard.index'))

    username = request.form.get('username', '').strip().lower()
    email = request.form.get('email', '').strip().lower()
    full_name = request.form.get('full_name', '').strip()
    phone = request.form.get('phone', '').strip()
    role_id = request.form.get('role_id')
    password = request.form.get('password', '').strip()
    is_active = bool(request.form.get('is_active', 1))

    if not username or not email or not full_name or not password or not role_id:
        flash('Please fill in all required fields (Full Name, Username, Email, Role, Password).', 'danger')
        return redirect(url_for('users.index'))

    if User.query.filter_by(username=username).first():
        flash(f'Username "{username}" is already in use. Please choose another username.', 'danger')
        return redirect(url_for('users.index'))

    if User.query.filter_by(email=email).first():
        flash(f'Email address "{email}" is already registered in the system.', 'danger')
        return redirect(url_for('users.index'))

    new_user = User(
        username=username,
        email=email,
        full_name=full_name,
        phone=phone,
        role_id=int(role_id),
        is_active=is_active
    )
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    log_audit('CREATE_USER', 'User', new_user.id, f"Created system user '{username}' with role '{new_user.role.name if new_user.role else 'None'}'")
    flash(f"User account '{username}' ({new_user.role.name if new_user.role else 'Role'}) has been created successfully!", 'success')
    return redirect(url_for('users.index'))

@users_bp.route('/<int:user_id>/edit', methods=['POST'])
@login_required
def edit_user(user_id):
    if not admin_required():
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('dashboard.index'))

    user = User.query.get_or_404(user_id)
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip().lower()
    phone = request.form.get('phone', '').strip()
    role_id = request.form.get('role_id')
    is_active = bool(request.form.get('is_active', 0))

    if not full_name or not email or not role_id:
        flash('Full Name, Email and Role are required.', 'danger')
        return redirect(url_for('users.index'))

    existing_email = User.query.filter(User.email == email, User.id != user_id).first()
    if existing_email:
        flash(f'Email "{email}" is already registered to another user.', 'danger')
        return redirect(url_for('users.index'))

    # If editing super admin id 1, ensure it remains active
    if user.id == 1:
        is_active = True

    user.full_name = full_name
    user.email = email
    user.phone = phone
    user.role_id = int(role_id)
    user.is_active = is_active
    user.updated_at = datetime.utcnow()

    db.session.commit()
    log_audit('EDIT_USER', 'User', user.id, f"Updated user '{user.username}' profile & role")
    flash(f"User account '{user.username}' updated successfully.", 'success')
    return redirect(url_for('users.index'))

@users_bp.route('/<int:user_id>/reset-password', methods=['POST'])
@login_required
def reset_password(user_id):
    if not admin_required():
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('dashboard.index'))

    user = User.query.get_or_404(user_id)
    new_password = request.form.get('new_password', '').strip()

    if not new_password or len(new_password) < 4:
        flash('New password must be at least 4 characters long.', 'danger')
        return redirect(url_for('users.index'))

    user.set_password(new_password)
    user.updated_at = datetime.utcnow()
    db.session.commit()

    log_audit('RESET_PASSWORD', 'User', user.id, f"Password reset for user '{user.username}' by admin {current_user.username}")
    flash(f"Password for user '{user.username}' has been updated successfully.", 'success')
    return redirect(url_for('users.index'))

@users_bp.route('/<int:user_id>/toggle-status', methods=['POST'])
@login_required
def toggle_status(user_id):
    if not admin_required():
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('dashboard.index'))

    user = User.query.get_or_404(user_id)
    if user.id == current_user.id or user.id == 1:
        flash('You cannot deactivate your own root administrator account.', 'warning')
        return redirect(url_for('users.index'))

    user.is_active = not user.is_active
    db.session.commit()

    status_str = "activated" if user.is_active else "deactivated"
    log_audit('TOGGLE_USER_STATUS', 'User', user.id, f"User '{user.username}' {status_str}")
    flash(f"User '{user.username}' account has been {status_str}.", 'info')
    return redirect(url_for('users.index'))

@users_bp.route('/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if not admin_required():
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('dashboard.index'))

    user = User.query.get_or_404(user_id)
    if user.id == 1 or user.id == current_user.id:
        flash('Cannot delete primary system Administrator or your current logged-in user account.', 'danger')
        return redirect(url_for('users.index'))

    uname = user.username
    db.session.delete(user)
    db.session.commit()

    log_audit('DELETE_USER', 'User', user_id, f"Deleted user '{uname}'")
    flash(f"User account '{uname}' has been deleted from the system.", 'success')
    return redirect(url_for('users.index'))
