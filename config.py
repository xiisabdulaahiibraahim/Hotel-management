import os
from datetime import timedelta
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-grand-horizon-hms-key-2026'
    
    # Database Configuration:
    # Use MySQL 8 by default when credentials exist, otherwise gracefully use SQLite
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '3306')
    DB_NAME = os.environ.get('DB_NAME', 'hotel_management')
    
    DEFAULT_MYSQL_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    DEFAULT_SQLITE_URI = f"sqlite:///{os.path.join(basedir, 'hotel_management.db')}"
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or (
        DEFAULT_MYSQL_URI if os.environ.get('USE_MYSQL', 'false').lower() == 'true' 
        else DEFAULT_SQLITE_URI
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
    }

    # Session & Security
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Uploads
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    # Hotel Default Constants
    HOTEL_NAME = "The Grand Horizon Luxury Hotel & Resort"
    DEFAULT_CURRENCY = "USD"
    DEFAULT_TAX_RATE = 5.0
    DEFAULT_SERVICE_CHARGE = 3.0
