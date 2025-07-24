from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from models import db, User, ParkingLot, ParkingSpot, Reservation
from flask import request
import math
from sqlalchemy import func
import traceback


app = Flask(__name__)

# ----- Configuration -----
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret-key'

# CORS config
CORS(app,
     supports_credentials=True,
     origins=["http://localhost:5173"],
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# ----- Initialize Extensions -----
db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

# ----- Handle CORS Preflight -----
@app.before_request
def handle_options_request():
    if request.method == 'OPTIONS':
        response = jsonify({"msg": "CORS preflight successful"})
        response.headers["Access-Control-Allow-Origin"] = "http://localhost:5173"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response

# ----- Seed Admin Once -----
@app.before_request
def create_admin_once():
    # only run this the first time through
    if not hasattr(app, 'admin_created'):
        # look for any existing admin by role
        if not User.query.filter_by(role="admin").first():
            admin_user = User(
                fullname="Admin User",               # new fullname field
                email="admin@example.com",           # unique, non-null
                password=generate_password_hash("admin123"),
                address="Admin HQ, 1 Infinite Loop",# required address
                pincode="000000",                    # required pincode
                role="admin"
            )
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Admin user created.")
        # mark it so we never seed again this request cycle
        app.admin_created = True

def admin_required_route(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Enforce JWT + admin role
        try:
            user_id = int(get_jwt_identity())
        except (TypeError, ValueError):
            return jsonify({"msg": "Invalid token identity"}), 400

        user = User.query.get(user_id)
        if not user or user.role != 'admin':
            return jsonify({"msg": "Admin access required"}), 403

        # Call the original view without injecting user_id
        return fn(*args, **kwargs)
    return wrapper


# ============================
#          ROUTES
# ============================

@app.route('/')
def home():
    return jsonify({"msg": "Parking App API is running"})


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}

    fullname = data.get('fullname')
    email    = data.get('email')
    password = data.get('password')
    address  = data.get('address')
    pincode  = data.get('pincode')

    # validate
    if not all([fullname, email, password, address, pincode]):
        return jsonify({"msg": "All fields (fullname, email, password, address, pincode) are required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "Email already exists"}), 409

    # hash & create
    hashed_pw = generate_password_hash(password)
    new_user = User(
        fullname=fullname,
        email=email,
        password=hashed_pw,
        address=address,
        pincode=pincode,
        role='user'
    )
    db.session.add(new_user)
    db.session.commit()

    token = create_access_token(identity=str(new_user.id))
    return jsonify({
        "msg": "Registration successful",
        "access_token": token,
        "email": new_user.email,
        "role": new_user.role
    }), 201



@app.route('/admin/lots/<int:lot_id>', methods=['DELETE'])
@jwt_required()
@admin_required_route
def delete_parking_lot(lot_id):
    try:
        lot = ParkingLot.query.filter_by(
            id=lot_id,
            created_by=int(get_jwt_identity())
        ).first()
        if not lot:
            return jsonify(msg='Lot not found'), 404

        # ensure no occupied spots
        if any(spot.is_reserved for spot in lot.spots):
            return jsonify(msg='Cannot delete a lot with reserved spots'), 400

        # delete all spots/reservations if you need, or rely on cascade
        for spot in lot.spots:
            db.session.delete(spot)
        db.session.delete(lot)
        db.session.commit()
        return jsonify(msg='Lot deleted'), 200

    except Exception as e:
        traceback.print_exc()              # prints full stack to your console
        return jsonify(msg=str(e)), 500


# ─── Login Route ─────────────────────────────────────────────────────────────────
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}

    email    = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"msg": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({"msg": "Invalid credentials"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({
        "access_token": token,
        "email": user.email,
        "role": user.role
    }), 200

@app.route('/admin/lots', methods=['POST'])
@jwt_required()
@admin_required_route
def create_parking_lot():
    data = request.get_json()
    # Validate input
    for field in ('name','address','pincode','price','maxSpots'):
        if field not in data:
            return jsonify(msg=f"Missing '{field}'"), 400

    try:
        # 1) Create the lot
        lot = ParkingLot(
            name           = data['name'],
            location       = data['address'],
            pincode        = data['pincode'],
            price_per_hour = float(data['price']),
            created_by     = int(get_jwt_identity())
        )
        db.session.add(lot)
        db.session.commit()    # flush so lot.id is assigned

        # 2) Create each spot under that lot
        max_spots = int(data['maxSpots'])
        spots = []
        for i in range(1, max_spots + 1):
            spot = ParkingSpot(
                lot_id      = lot.id,
                spot_number = i
            )
            spots.append(spot)
            db.session.add(spot)

        db.session.commit()    # persist all spots

        return jsonify(msg="Lot created", lot_id=lot.id), 201

    except Exception as e:
        db.session.rollback()
        return jsonify(msg=str(e)), 500


@app.route('/admin/lots/<int:lot_id>/spots', methods=['POST'])
@jwt_required()
@admin_required_route
def create_spot(lot_id):
    admin_id = int(get_jwt_identity())
    data = request.get_json()
    number = data.get('number')

    if not number:
        return jsonify({"msg": "Spot number required"}), 400

    lot = ParkingLot.query.get(lot_id)
    if not lot:
        return jsonify({"msg": "Parking lot not found"}), 404

    for spot in lot.spots:
        if spot.spot_number == number:
            return jsonify({"msg": "Spot number already exists in this lot"}), 400

    spot = ParkingSpot(spot_number=number, lot=lot)
    db.session.add(spot)
    db.session.commit()

    return jsonify({"msg": "Parking spot created"}), 201

@app.route('/admin/lots/<int:lot_id>/spot/<int:spot_id>', methods=['GET'])
@jwt_required()
@admin_required_route
def get_spot_details(lot_id, spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    if spot.lot_id != lot_id:
        return jsonify(msg="Lot/spot mismatch"), 400

    if spot.is_reserved is False:
        return jsonify(msg="Spot is available"), 400

    # find the active reservation
    resv = Reservation.query.filter_by(spot_id=spot_id, end_time=None).first()
    if not resv:
        return jsonify(msg="No active reservation"), 404

    hours    = (datetime.utcnow() - resv.start_time).total_seconds() / 3600
    est_cost = round(hours * spot.lot.price_per_hour, 2)

    return jsonify({
      'id':           resv.id,
      'customer_id':  resv.user_id,
      'vehicle_no':   resv.vehicle_number,
      'start_time':   resv.start_time.isoformat(),
      'est_cost':     est_cost
    }), 200

@app.route('/admin/spot/<int:spot_id>', methods=['DELETE'])
@jwt_required()
@admin_required_route
def delete_parking_spot(spot_id):
    try:
        spot = ParkingSpot.query.get(spot_id)
        if not spot:
            return jsonify(msg='Spot not found'), 404

        if spot.is_reserved:
            return jsonify(msg='Cannot delete a reserved spot'), 400

        db.session.delete(spot)
        db.session.commit()
        return jsonify(msg='Spot deleted'), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify(msg=str(e)), 500




@app.route('/admin/lots/<int:lot_id>', methods=['DELETE'])
@jwt_required()
@admin_required_route
def delete_lot(lot_id):
    admin_id = int(get_jwt_identity())
    if request.method == 'OPTIONS':
        return jsonify({"msg": "Preflight OK"}), 200

    lot = ParkingLot.query.get(lot_id)
    if not lot:
        return jsonify({"msg": "Parking lot not found"}), 404

    # Delete associated spots first
    for spot in lot.spots:
        db.session.delete(spot)

    db.session.delete(lot)
    db.session.commit()

    return jsonify({"msg": f"Lot {lot.name} deleted"}), 200


@app.route('/admin/lots/<int:lot_id>/spots/<int:spot_id>', methods=['PUT'])
@jwt_required()
@admin_required_route
def edit_spot(lot_id, spot_id):
    data = request.get_json() or {}
    new_number = data.get('number')
    if new_number is None:
        return jsonify(msg='Must supply new spot number'), 400

    spot = ParkingSpot.query.filter_by(id=spot_id, lot_id=lot_id).first()
    if not spot:
        return jsonify(msg='Spot not found'), 404

    # update the spot number
    try:
        spot.spot_number = int(new_number)
        db.session.commit()
    except ValueError:
        return jsonify(msg='Invalid number'), 400

    return jsonify(msg='Spot updated'), 200

# DELETE a single spot
@app.route('/admin/lots/<int:lot_id>/spots/<int:spot_id>', methods=['DELETE'])
@jwt_required()
@admin_required_route
def delete_spot(lot_id, spot_id):
    spot = ParkingSpot.query.filter_by(id=spot_id, lot_id=lot_id).first()
    if not spot:
        return jsonify(msg='Spot not found'), 404

    db.session.delete(spot)
    db.session.commit()
    return jsonify(msg='Spot deleted'), 200


@app.route('/user/reserve', methods=['POST'], endpoint='user_confirm_reservation')
@jwt_required()
def user_confirm_reservation():
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    resv_id = data.get('reservation_id')
    vehicle = data.get('vehicle_number')
    if not resv_id or not vehicle:
        return jsonify(msg='reservation_id and vehicle_number are required'), 400

    try:
        resv_id = int(resv_id)
    except (ValueError, TypeError):
        return jsonify(msg='Invalid reservation ID'), 400

    reservation = Reservation.query.filter_by(id=resv_id, user_id=user_id).first()
    if not reservation:
        return jsonify(msg='Reservation not found'), 404

    reservation.vehicle_number = vehicle
    reservation.start_time = reservation.start_time or datetime.utcnow()

    db.session.commit()
    return jsonify(msg='Booking confirmed'), 200




@app.route('/user/dashboard', methods=['GET'])
@jwt_required()
def user_dashboard():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return jsonify({"msg": "Invalid user identity"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    reservations = []
    for res in Reservation.query.filter_by(user_id=user_id).all():
        spot = ParkingSpot.query.get(res.spot_id)
        lot  = ParkingLot.query.get(res.lot_id)

        reservations.append({
            "reservation_id":  res.id,
            "lot_name":        lot.name if lot else "",
            "lot_address": lot.location if lot else "",  # ✅ Correct
            "spot_number":     spot.spot_number if spot else "",
            "vehicle_number":  res.vehicle_number,                # ✅ fixed
            "start_time":      res.start_time.isoformat(),
            "end_time":        res.end_time.isoformat() if res.end_time else None,
            "cost":            getattr(res, 'cost', 0)
        })

    return jsonify({
        'id':          user.id,
        "username":    user.fullname,  # ✅ good call using fullname
        "email":       user.email,  
        "reservations": reservations
    }), 200


@app.route('/user/summary', methods=['GET'])
@jwt_required()
def user_summary():
    user_id = get_jwt_identity()

    # 1) Define start of current month
    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)

    # 2) Query and group by lot
    results = (
        db.session.query(
            ParkingLot.name.label('lot_name'),
            func.count(Reservation.id).label('times_parked'),
            func.sum(
                func.strftime('%s', Reservation.end_time) -
                func.strftime('%s', Reservation.start_time)
            ).label('total_time_secs'),
            func.sum(
                (func.strftime('%s', Reservation.end_time) -
                 func.strftime('%s', Reservation.start_time)) /
                3600.0 * ParkingLot.price_per_hour
            ).label('total_cost')
        )
        .join(Reservation, Reservation.lot_id == ParkingLot.id)
        .filter(
            Reservation.user_id == user_id,
            Reservation.start_time >= month_start,
            Reservation.end_time.isnot(None)
        )
        .group_by(ParkingLot.id)
        .all()
    )

    # 3) Format results
    summary = []
    for row in results:
        summary.append({
            'lot_name': row.lot_name,
            'times_parked': int(row.times_parked or 0),
            'total_time_minutes': (row.total_time_secs or 0) / 60,
            'total_cost': round(row.total_cost or 0, 2)
        })

    return jsonify(summary), 200

@app.route('/user/lots', methods=['GET'])
@jwt_required()
def get_all_lots():
    lots = ParkingLot.query.all()
    result = []

    for lot in lots:
        total_spots = len(lot.spots)
        available_spots = len([s for s in lot.spots if not s.is_reserved])
        result.append({
  'id': lot.id,
  'name': lot.name,
  'location': lot.location,
  'total_spots': total_spots,
  'available_spots': available_spots,
  'price_per_hour': lot.price_per_hour
})

    return jsonify(result), 200



@app.route('/user/release', methods=['POST'])
@jwt_required()
def release_reservation():
    # Force user_id to an integer
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return jsonify({"msg": "Invalid user identity"}), 400

    data = request.get_json()
    reservation_id = data.get('reservation_id')

    # Debug logging
    print(f"[DEBUG] user_id={user_id}, release payload:", data)

    reservation = Reservation.query.get(reservation_id)
    if not reservation or reservation.user_id != user_id:
        return jsonify({"msg": "Reservation not found or unauthorized"}), 404

    # Mark spot as available
    spot = ParkingSpot.query.get(reservation.spot_id)
    if spot:
        spot.is_reserved = False

    # Update reservation with end time and cost
    reservation.end_time = datetime.utcnow()
    duration_hours = (reservation.end_time - reservation.start_time).total_seconds() / 3600
    cost_per_hour = 20
    reservation.cost = round(duration_hours * cost_per_hour, 2)
    db.session.commit()

    return jsonify({
        "msg": "Reservation released",
        "duration": round(duration_hours, 2),
        "cost": reservation.cost
    }), 200

@app.route('/admin/lots/<int:lot_id>', methods=['PUT'])
@jwt_required()
@admin_required_route
def update_parking_lot(lot_id):
    data = request.get_json()
    lot = ParkingLot.query.get_or_404(lot_id)

    # Update fields if present
    if 'name' in data:
        lot.name = data['name']
    if 'location' in data:
        lot.location = data['location']
    if 'pincode' in data:
        lot.pincode = data['pincode']
    if 'price_per_hour' in data:
        lot.price_per_hour = float(data['price_per_hour'])
    # NOTE: we’re not handling maxSpots here—spots resizing is more complex

    db.session.commit()
    return jsonify(msg="Lot updated"), 200

@app.route('/admin/dashboard', methods=['GET'])
@jwt_required()
@admin_required_route
def admin_dashboard():
    # 1) Identify the admin
    admin_id = int(get_jwt_identity())
    admin = User.query.get(admin_id)

    # 2) Fetch all lots created by this admin
    lots = ParkingLot.query.filter_by(created_by=admin_id).all()

    # 3) Build the payload
    lot_list = []
    for lot in lots:
        lot_list.append({
            'id':             lot.id,
            'name':           lot.name,
            'location':       lot.location,
            'pincode':        lot.pincode,
            'price_per_hour': lot.price_per_hour,
            'spots': [
                {
                    'id':           spot.id,
                    'number':       spot.spot_number,
                    'is_available': not spot.is_reserved
                }
                for spot in lot.spots
            ]
        })

          # Build the lot_summary list
    lot_summary = []
    for lot in ParkingLot.query.all():
        # sum active/endless reservation costs
        total_rev = 0
        for resv in Reservation.query.filter_by(
            lot_id=lot.id, 
            end_time=None
        ).all():
            hours = (datetime.utcnow() - resv.start_time).total_seconds() / 3600
            total_rev += round(hours * lot.price_per_hour, 2)

        lot_summary.append({
            'name': lot.name,
            'revenue': total_rev
        })

    # 4) Aggregate stats
    total_spots     = sum(len(l.spots) for l in lots)
    available_spots = sum(spot['is_available'] for l in lot_list for spot in l['spots'])
    reserved_spots  = total_spots - available_spots

    return jsonify({
        'username':        admin.fullname,
        'total_lots':      len(lot_list),
        'total_spots':     total_spots,
        'available_spots': available_spots,
        'reserved_spots':  reserved_spots,
        'lot_summary':     lot_summary,             # fill as needed
        'parking_lots':    lot_list
    }), 200

@app.route('/admin/profile', methods=['PUT'])
@jwt_required()
@admin_required_route
def admin_update_profile():
    # 1. Grab the logged‐in admin’s ID from the JWT
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user or user.role != 'admin':
        return jsonify(msg="Admin not found"), 404

    # 2. Read the new password from the JSON payload
    data = request.get_json() or {}
    new_password = data.get('password', '').strip()
    if not new_password:
        return jsonify(msg="Password is required"), 400

    # 3. Hash & save
    user.password = generate_password_hash(new_password)
    db.session.commit()

    return jsonify(msg="Password updated"), 200

@app.route('/admin/users', methods=['GET'])
@jwt_required()
@admin_required_route
def admin_list_users():
    # only non-admin
    users = User.query.filter(User.role != 'admin').all()
    # remove any accidental duplicates before jsonify:
    unique = { u.id: u for u in users }.values()
    result = [{
        'id':       u.id,
        'email':    u.email,
        'fullname': u.fullname,
        'address':  u.address,
        'pincode':  u.pincode
    } for u in unique]
    return jsonify(users=result), 200

@app.route('/api/reservations/assign', methods=['POST'])
@jwt_required()
def assign_reservation():
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    lot_id = data.get('lot_id')
    if not lot_id:
        return jsonify(message='lot_id required'), 400

    lot = ParkingLot.query.get(lot_id)
    if not lot:
        return jsonify(message='Lot not found'), 404

    spot = ParkingSpot.query.filter_by(
        lot_id=lot_id,
        is_reserved=False
    ).first()

    if not spot:
        return jsonify(message='No spots available'), 400

    # Create reservation immediately
    new_reservation = Reservation(
        user_id=user_id,
        lot_id=lot.id,
        spot_id=spot.id,
        vehicle_number='',          # ← to be filled later
        start_time=None,
        end_time=None
    )
    db.session.add(new_reservation)
    db.session.commit()

    # Mark spot as reserved
    spot.is_reserved = True
    db.session.commit()

    return jsonify({
        'reservation_id': new_reservation.id,
        'spot_number': spot.spot_number,
        'cost': lot.price_per_hour
    }), 201

@app.route('/user/assign', methods=['POST'])
@jwt_required()
def assign_spot():
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    lot_id = data.get('lot_id')
    if not lot_id:
        return jsonify(msg='lot_id required'), 400

    lot = ParkingLot.query.get(lot_id)
    if not lot:
        return jsonify(msg='Lot not found'), 404

    # pick first free spot
    spot = next((s for s in lot.spots if not s.is_reserved), None)
    if not spot:
        return jsonify(msg='No spots available'), 400

    # mark it “held” so nobody else grabs it
    spot.is_reserved = True

    # create a PENDING reservation row
    new_resv = Reservation(
        user_id=user_id,
        lot_id=lot.id,
        spot_id=spot.id,
        start_time=datetime.utcnow(),
        end_time=None,
        vehicle_number=''   # fill on confirm
    )
    db.session.add(new_resv)
    db.session.commit()

    return jsonify({
        'reservation_id': new_resv.id,
        'spot_number': spot.spot_number,
        'cost': lot.price_per_hour
    }), 200 

@app.route('/api/reservations/confirm', methods=['POST'], endpoint='api_confirm_reservation')
@jwt_required()
def api_confirm_reservation():

    user_id = get_jwt_identity()
    data = request.get_json() or {}

    resv_id = data.get('reservation_id')
    vehicle = data.get('vehicle_number')

    if not resv_id or not vehicle:
        return jsonify(message='Missing data'), 400

    reservation = Reservation.query.get(resv_id)
    if not reservation or reservation.user_id != user_id:
        return jsonify(message='Reservation not found'), 404

    if reservation.end_time:
        return jsonify(message='Reservation already completed'), 400

    # Fill details
    reservation.vehicle_number = vehicle
    reservation.start_time = datetime.utcnow()

    # Mark spot as reserved
    spot = ParkingSpot.query.get(reservation.spot_id)
    spot.is_reserved = True

    db.session.commit()
    return jsonify(message='Booking confirmed'), 200



if __name__ == '__main__':
    app.run(debug=True)

