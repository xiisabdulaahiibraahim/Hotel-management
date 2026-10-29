from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, date
from app.models import db, Expense, ExpenseCategory, DailyCashRegister
from app.utils.decorators import role_required
from app.utils.helpers import log_audit

expenses_bp = Blueprint('expenses', __name__, url_prefix='/expenses')

@expenses_bp.route('/')
@login_required
@role_required('Super Admin', 'Manager', 'Accountant')
def index():
    category_id = request.args.get('category')
    query = Expense.query

    if category_id:
        query = query.filter_by(category_id=int(category_id))

    expenses = query.order_by(Expense.expense_date.desc(), Expense.id.desc()).all()
    categories = ExpenseCategory.query.all()
    today = date.today()

    today_register = DailyCashRegister.query.filter_by(register_date=today).first()
    past_registers = DailyCashRegister.query.order_by(DailyCashRegister.register_date.desc()).limit(7).all()
    total_expenses = sum(e.amount for e in expenses)

    return render_template(
        'expenses/index.html',
        expenses=expenses,
        categories=categories,
        today_register=today_register,
        past_registers=past_registers,
        total_expenses=total_expenses,
        selected_category=category_id,
        today=today
    )


@expenses_bp.route('/add', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager', 'Accountant')
def add():
    category_id = int(request.form.get('category_id'))
    amount = float(request.form.get('amount', 0.0) or 0.0)
    exp_date_str = request.form.get('expense_date')
    description = request.form.get('description', '').strip()
    payment_method = request.form.get('payment_method', 'Cash')

    if amount <= 0 or not description:
        flash('Valid amount and description are required.', 'danger')
        return redirect(url_for('expenses.index'))

    exp_date = datetime.strptime(exp_date_str, '%Y-%m-%d').date() if exp_date_str else date.today()

    expense = Expense(
        category_id=category_id,
        amount=amount,
        expense_date=exp_date,
        description=description,
        payment_method=payment_method,
        recorded_by=current_user.id
    )
    db.session.add(expense)

    # If paid from cash, update today's cash register paid out
    if payment_method == 'Cash':
        register = DailyCashRegister.query.filter_by(register_date=exp_date).first()
        if register and register.status == 'Open':
            register.cash_paid_out += amount

    db.session.commit()
    log_audit('CREATE_EXPENSE', 'Expense', expense.id, f"${amount} for {description}")
    flash(f'Expense of ${amount:,.2f} recorded successfully.', 'success')
    return redirect(url_for('expenses.index'))


@expenses_bp.route('/cash-register/open', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager', 'Accountant')
def open_cash_register():
    today = date.today()
    opening = float(request.form.get('opening_cash', 0.0) or 0.0)

    reg = DailyCashRegister.query.filter_by(register_date=today).first()
    if not reg:
        reg = DailyCashRegister(
            register_date=today,
            opening_cash=opening,
            status='Open'
        )
        db.session.add(reg)
    else:
        reg.opening_cash = opening
        reg.status = 'Open'

    db.session.commit()
    flash(f'Daily Cash Register for {today} opened with ${opening:,.2f}.', 'success')
    return redirect(url_for('expenses.index'))


@expenses_bp.route('/cash-register/close', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager', 'Accountant')
def close_cash_register():
    today = date.today()
    reg = DailyCashRegister.query.filter_by(register_date=today).first()
    if reg:
        closing_cash = float(request.form.get('closing_cash', 0.0) or 0.0)
        reg.closing_cash = closing_cash
        reg.status = 'Closed'
        reg.closed_by = current_user.id
        reg.closed_at = datetime.utcnow()
        db.session.commit()
        flash(f'Daily Cash Register for {today} closed successfully.', 'success')
    return redirect(url_for('expenses.index'))
