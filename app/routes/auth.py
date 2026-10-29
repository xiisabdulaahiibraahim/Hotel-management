from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from app.models import db, User, Role, Guest
from app.utils.helpers import log_audit

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username_or_email = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact the administrator.', 'danger')
                return render_template('auth/login.html')

            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user, remember=remember)
            log_audit('LOGIN', 'User', user.id, f"User {user.username} logged in successfully")
            
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.full_name}!', 'success')
            
            # If guest user, redirect to portal, otherwise dashboard
            if user.role.name == 'Guest':
                return redirect(next_page or url_for('guest_portal.my_bookings'))
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash('Invalid username/email or password.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        id_number = request.form.get('id_number', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')

        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash('Username or email is already registered.', 'danger')
            return render_template('auth/register.html')

        guest_role = Role.query.filter_by(name='Guest').first()
        if not guest_role:
            guest_role = Role(name='Guest', description='Customer portal guest account')
            db.session.add(guest_role)
            db.session.flush()

        new_user = User(
            role_id=guest_role.id,
            username=username,
            email=email,
            full_name=f"{first_name} {last_name}",
            phone=phone,
            is_active=True
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.flush()

        # Create Guest CRM profile
        guest = Guest(
            user_id=new_user.id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            id_number=id_number or f"G-{new_user.id}"
        )
        db.session.add(guest)
        db.session.commit()

        login_user(new_user)
        flash('Account created successfully! Welcome to The Grand Horizon.', 'success')
        return redirect(url_for('guest_portal.index'))

    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    log_audit('LOGOUT', 'User', current_user.id, f"User {current_user.username} logged out")
    logout_user()
    flash('You have been logged out securely.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name', current_user.full_name).strip()
        current_user.phone = request.form.get('phone', current_user.phone).strip()
        
        # Change password if provided
        new_password = request.form.get('new_password')
        if new_password:
            current_user.set_password(new_password)
            flash('Password updated successfully.', 'success')
            
        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html')
