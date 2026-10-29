from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, date
from app.models import db, Employee, Shift, Attendance, LeaveRequest, User, Role
from app.utils.decorators import role_required
from app.utils.helpers import log_audit

staff_bp = Blueprint('staff', __name__, url_prefix='/staff')

@staff_bp.route('/')
@login_required
@role_required('Super Admin', 'Manager')
def index():
    dept = request.args.get('dept')
    query = Employee.query

    if dept:
        query = query.filter_by(department=dept)

    employees = query.order_by(Employee.first_name.asc()).all()
    shifts = Shift.query.all()
    today_attendance = Attendance.query.filter_by(date=date.today()).all()
    pending_leaves = LeaveRequest.query.filter_by(status='Pending').all()

    departments = [
        'Front Office', 'Housekeeping', 'Maintenance', 
        'Kitchen & Food', 'Accounting', 'Security', 'Management'
    ]

    return render_template(
        'staff/index.html',
        employees=employees,
        shifts=shifts,
        today_attendance=today_attendance,
        pending_leaves=pending_leaves,
        departments=departments,
        selected_dept=dept
    )


@staff_bp.route('/add', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager')
def add():
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    department = request.form.get('department')
    designation = request.form.get('designation', '').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()
    shift_id = request.form.get('shift_id')
    basic_salary = float(request.form.get('basic_salary', 0.0) or 0.0)

    emp_count = Employee.query.count() + 1
    emp_code = f"EMP-{emp_count:03d}"

    emp = Employee(
        employee_code=emp_code,
        first_name=first_name,
        last_name=last_name,
        department=department,
        designation=designation,
        phone=phone,
        email=email,
        shift_id=int(shift_id) if shift_id else None,
        basic_salary=basic_salary,
        status='Active'
    )
    db.session.add(emp)
    db.session.commit()
    log_audit('CREATE_EMPLOYEE', 'Employee', emp.id, f"Added employee {emp.full_name} ({emp.employee_code})")
    flash(f'Employee {emp.full_name} ({emp.employee_code}) registered successfully.', 'success')
    return redirect(url_for('staff.index'))


@staff_bp.route('/attendance/log', methods=['POST'])
@login_required
def log_attendance():
    emp_id = int(request.form.get('employee_id'))
    status = request.form.get('status', 'Present')
    notes = request.form.get('notes', '').strip()
    today = date.today()

    existing = Attendance.query.filter_by(employee_id=emp_id, date=today).first()
    if existing:
        existing.status = status
        existing.notes = notes
    else:
        now_time = datetime.utcnow().time()
        att = Attendance(
            employee_id=emp_id,
            date=today,
            check_in=now_time,
            status=status,
            notes=notes
        )
        db.session.add(att)

    db.session.commit()
    flash('Attendance logged successfully.', 'success')
    return redirect(url_for('staff.index'))


@staff_bp.route('/leave/<int:leave_id>/review', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager')
def review_leave(leave_id):
    leave = LeaveRequest.query.get_or_404(leave_id)
    status = request.form.get('status') # Approved or Rejected
    leave.status = status
    leave.reviewed_by = current_user.id
    db.session.commit()
    flash(f'Leave request #{leave.id} marked as {status}.', 'info')
    return redirect(url_for('staff.index'))
