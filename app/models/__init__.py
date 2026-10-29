from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

# Import all models so they register with SQLAlchemy metadata
from app.models.user import Role, Permission, RolePermission, User
from app.models.guest import Guest
from app.models.room import RoomType, Amenity, RoomAmenity, Room, RoomImage, Promotion
from app.models.booking import Booking, BookingRoom, CheckinRecord
from app.models.billing import Invoice, InvoiceItem, Payment, NightAuditRecord
from app.models.housekeeping import HousekeepingTask, LostAndFound
from app.models.maintenance import MaintenanceTicket
from app.models.restaurant import MenuCategory, MenuItem, RestaurantOrder, RestaurantOrderItem, RecipeIngredient, TableReservation
from app.models.services import HotelService, ServiceOrder
from app.models.inventory import Supplier, InventoryCategory, InventoryItem, StockMovement
from app.models.staff import Shift, Employee, Attendance, LeaveRequest
from app.models.expense import ExpenseCategory, Expense, DailyCashRegister
from app.models.misc import Review, Notification, AuditLog, HotelSetting, CommunicationLog
