import os
from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    # Check and add image column to rooms
    try:
        db.session.execute(text("ALTER TABLE rooms ADD COLUMN image VARCHAR(255)"))
        db.session.commit()
        print("Added image column to rooms successfully")
    except Exception as e:
        db.session.rollback()
        print("image column on rooms already exists or error:", e)

    # Check and add delivery_image column to restaurant_orders
    try:
        db.session.execute(text("ALTER TABLE restaurant_orders ADD COLUMN delivery_image VARCHAR(255)"))
        db.session.commit()
        print("Added delivery_image column to restaurant_orders successfully")
    except Exception as e:
        db.session.rollback()
        print("delivery_image column on restaurant_orders already exists or error:", e)

    # Ensure upload directories exist
    upload_base = app.config.get('UPLOAD_FOLDER', os.path.join(os.path.dirname(__file__), 'app', 'static', 'uploads'))
    for sub in ['rooms', 'delivery', 'menu', 'general']:
        p = os.path.join(upload_base, sub)
        os.makedirs(p, exist_ok=True)
        print(f"Directory ready: {p}")
