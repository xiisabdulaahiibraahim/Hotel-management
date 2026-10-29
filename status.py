from app import create_app
from app.models import db, User, Role, Room, Booking, Guest

app = create_app()
with app.app_context():
    print('=== HOTEL MANAGEMENT SYSTEM STATUS ===')
    print(f'Users:    {User.query.count()}')
    print(f'Roles:    {Role.query.count()}')
    print(f'Rooms:    {Room.query.count()}')
    print(f'Guests:   {Guest.query.count()}')
    print(f'Bookings: {Booking.query.count()}')
    print()
    print('=== STAFF ACCOUNTS ===')
    non_guest = User.query.join(Role).filter(Role.name != 'Guest').all()
    for u in non_guest:
        print(f'  {u.username:15s} | {u.role.name:22s} | Active: {u.is_active}')
    print()
    print('Password for all: Admin123!')
    print('URL: http://127.0.0.1:5000')
