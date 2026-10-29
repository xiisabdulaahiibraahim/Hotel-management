import os
from datetime import datetime
from flask import Flask, render_template, request
from config import Config
from app.models import db, login_manager, HotelSetting, Notification

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.rooms import rooms_bp
    from app.routes.bookings import bookings_bp
    from app.routes.checkin import checkin_bp
    from app.routes.billing import billing_bp
    from app.routes.guests import guests_bp
    from app.routes.housekeeping import housekeeping_bp
    from app.routes.maintenance import maintenance_bp
    from app.routes.restaurant import restaurant_bp
    from app.routes.inventory import inventory_bp
    from app.routes.staff import staff_bp
    from app.routes.expenses import expenses_bp
    from app.routes.reports import reports_bp
    from app.routes.guest_portal import guest_portal_bp
    from app.routes.settings import settings_bp
    from app.routes.api import api_bp
    from app.routes.users import users_bp
    from app.routes.delivery import delivery_bp

    app.register_blueprint(guest_portal_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(bookings_bp)
    app.register_blueprint(checkin_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(guests_bp)
    app.register_blueprint(housekeeping_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(restaurant_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(delivery_bp)
    from app.routes.communication import communication_bp
    app.register_blueprint(communication_bp)

    @app.route('/login')
    def login_redirect():
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))

    @app.route('/checkin')
    def checkin_redirect():
        from flask import redirect, url_for
        return redirect(url_for('checkin.index'))

    # Context processors for templates
    @app.context_processor
    def inject_global_data():
        currency = '$'
        hotel_name = "The Grand Horizon Luxury Hotel & Resort"
        try:
            currency = HotelSetting.get_value('currency_symbol', '$')
            hotel_name = HotelSetting.get_value('hotel_name', 'The Grand Horizon Luxury Hotel & Resort')
        except Exception:
            pass

        return {
            'CURRENCY': currency,
            'HOTEL_NAME': hotel_name,
            'now': datetime.utcnow(),
            'request': request
        }

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    return app
