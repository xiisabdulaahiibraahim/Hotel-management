import io
from app import create_app, db
from app.models import User, Role, Room, RestaurantOrder

app = create_app()

def login_as(client, username):
    client.get('/auth/logout')
    res = client.post('/auth/login', data={'username': username, 'password': 'Admin123!'}, follow_redirects=True)
    assert res.status_code == 200, f"Login failed for {username}"
    return res

def test_rbac():
    with app.app_context():
        with app.test_client() as client:
            print("--- Testing RBAC & Role Segregation ---")
            
            # Test 1: Receptionist
            login_as(client, 'reception')
            r_dash = client.get('/dashboard')
            assert r_dash.status_code == 200, f"Receptionist dashboard failed: {r_dash.status_code}"
            assert b"Reception &" in r_dash.data or b"Front Desk" in r_dash.data, "Not reception dashboard"
            print("1. Receptionist Dashboard: OK (shows Reception & Front Desk Terminal)")

            r_rep = client.get('/reports/')
            assert r_rep.status_code in [403, 302], f"Receptionist accessed reports! Status: {r_rep.status_code}"
            print(f"   Receptionist access to /reports/: Blocked ({r_rep.status_code})")

            r_usr = client.get('/users/')
            assert r_usr.status_code in [403, 302], f"Receptionist accessed users! Status: {r_usr.status_code}"
            print(f"   Receptionist access to /users/: Blocked ({r_usr.status_code})")

            # Test 2: Housekeeping
            login_as(client, 'housekeeping')
            hk_dash = client.get('/dashboard')
            assert hk_dash.status_code == 200, f"Housekeeping dashboard failed: {hk_dash.status_code}"
            assert b"Housekeeping" in hk_dash.data, "Not housekeeping dashboard"
            print("2. Housekeeping Dashboard: OK (shows Housekeeping & Room Hygiene Hub)")

            hk_rep = client.get('/reports/')
            assert hk_rep.status_code in [403, 302], f"Housekeeping accessed reports! Status: {hk_rep.status_code}"
            print(f"   Housekeeping access to /reports/: Blocked ({hk_rep.status_code})")

            hk_bil = client.get('/billing/')
            assert hk_bil.status_code in [403, 302], f"Housekeeping accessed billing! Status: {hk_bil.status_code}"
            print(f"   Housekeeping access to /billing/: Blocked ({hk_bil.status_code})")

            # Test 3: Restaurant / POS Staff
            login_as(client, 'pos')
            pos_dash = client.get('/dashboard')
            assert pos_dash.status_code == 200, f"POS dashboard failed: {pos_dash.status_code}"
            assert b"Culinary, POS" in pos_dash.data or b"Dining" in pos_dash.data, "Not POS dashboard"
            print("3. Restaurant/POS Dashboard: OK (shows Culinary, POS & Delivery Terminal)")

            pos_rep = client.get('/reports/')
            assert pos_rep.status_code in [403, 302], f"POS accessed reports! Status: {pos_rep.status_code}"
            print(f"   Restaurant/POS access to /reports/: Blocked ({pos_rep.status_code})")

            # Test 4: Accountant
            login_as(client, 'accountant')
            acc_dash = client.get('/dashboard')
            assert acc_dash.status_code == 200, f"Accountant dashboard failed: {acc_dash.status_code}"
            assert b"Financial" in acc_dash.data, "Not Accountant dashboard"
            print("4. Accountant Dashboard: OK (shows Financial & Accounting Hub)")

            acc_rep = client.get('/reports/')
            assert acc_rep.status_code == 200, f"Accountant cannot access reports! Status: {acc_rep.status_code}"
            print("   Accountant access to /reports/: Allowed (200 OK)")

            acc_usr = client.get('/users/')
            assert acc_usr.status_code in [403, 302], f"Accountant accessed users! Status: {acc_usr.status_code}"
            print(f"   Accountant access to /users/: Blocked ({acc_usr.status_code})")

            # Test 5: Super Admin
            login_as(client, 'admin')
            adm_dash = client.get('/dashboard')
            assert adm_dash.status_code == 200
            assert b"Executive Hotel Performance" in adm_dash.data or b"Active Operational &" in adm_dash.data or b"Executive" in adm_dash.data, "Not admin dashboard"
            print("5. Super Admin Dashboard: OK (shows Full Executive Master Dashboard)")

            adm_usr = client.get('/users/')
            assert adm_usr.status_code == 200, f"Admin failed users: {adm_usr.status_code}"
            print("   Super Admin access to /users/: Allowed (200 OK)")

            # Test 6: Room Image Upload
            dummy_img = (io.BytesIO(b"fake image data"), "test_room.jpg")
            res_room = client.post('/rooms/add', data={
                'room_number': 'TEST-999',
                'floor': '3',
                'room_type_id': '1',
                'status': 'Available',
                'notes': 'Test suite with upload',
                'room_image': dummy_img
            }, content_type='multipart/form-data', follow_redirects=True)
            assert res_room.status_code == 200
            test_r = Room.query.filter_by(room_number='TEST-999').first()
            assert test_r is not None and test_r.image is not None, "Room image was not saved!"
            print(f"6. Room Image Upload: SUCCESS! Room image saved to: {test_r.image}")

            # Clean up test room
            db.session.delete(test_r)
            db.session.commit()
            print("   Test room cleaned up.")

            # Test 7: Delivery Order with Photo Upload
            dummy_deliv_img = (io.BytesIO(b"fake delivery parcel image"), "parcel.jpg")
            res_deliv = client.post('/delivery/create', data={
                'customer_name': 'Test Delivery Customer',
                'customer_phone': '+252615559999',
                'delivery_address': 'Lido Beach Club 12',
                'delivery_rider': 'Rider Test',
                'items_json': '[{"id": 1, "qty": 2}]',
                'delivery_image': dummy_deliv_img
            }, content_type='multipart/form-data', follow_redirects=True)
            assert res_deliv.status_code == 200
            test_d = RestaurantOrder.query.filter_by(customer_name='Test Delivery Customer').first()
            assert test_d is not None and test_d.delivery_image is not None, "Delivery image was not saved!"
            print(f"7. Delivery Image Upload: SUCCESS! Delivery image saved to: {test_d.delivery_image}")

            # Clean up test delivery
            db.session.delete(test_d)
            db.session.commit()
            print("   Test delivery order cleaned up.")

            print("\nALL RBAC AND IMAGE UPLOAD TESTS PASSED WITH 100% SUCCESS!")

if __name__ == '__main__':
    test_rbac()
