from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required
from extensions import mongo, bcrypt
from models.user import User
from utils.validators import validate_email, validate_password, validate_role
from utils.decorators import admin_only, landlord_only, tenant_only

# Blueprint with URL prefix /auth
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# ---------------------------
# REGISTER USER
# ---------------------------
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    role = data.get("role")

    # Validation
    if not validate_email(email):
        return jsonify({"error": "Invalid email"}), 400

    if not validate_password(password):
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    if not validate_role(role):
        return jsonify({"error": "Invalid role"}), 400

    # Check if user already exists
    existing_user = mongo.db.users.find_one({"email": email})
    if existing_user:
        return jsonify({"error": "User already exists"}), 409

    # Hash password
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    # Create user object and insert into DB
    user = User(email=email, password=hashed_password, role=role)
    mongo.db.users.insert_one(user.to_dict())

    return jsonify({"message": "User registered successfully"}), 201

# ---------------------------
# LOGIN USER
# ---------------------------
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    # Find user
    user = mongo.db.users.find_one({"email": email})
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Check password
    if not bcrypt.check_password_hash(user["password"], password):
        return jsonify({"error": "Incorrect password"}), 401

    # Create JWT token including role
    access_token = create_access_token(identity={
        "user_id": str(user["_id"]),
        "role": user["role"]
    })

    return jsonify({"access_token": access_token, "role": user["role"]}), 200

# ---------------------------
# ROLE-BASED ROUTES
# ---------------------------

# Admin-only route
@auth_bp.route("/admin/dashboard", methods=["GET"])
@jwt_required()
@admin_only
def admin_dashboard():
    return jsonify({"message": "Welcome to the admin dashboard"})

# Landlord-only route
@auth_bp.route("/landlord/properties", methods=["GET"])
@jwt_required()
@landlord_only
def landlord_properties():
    return jsonify({"message": "Here are your properties"})

# Tenant-only route
@auth_bp.route("/tenant/bookings", methods=["GET"])
@jwt_required()
@tenant_only
def tenant_bookings():
    return jsonify({"message": "Here are your bookings"})
    return jsonify({"access_token": access_token, "role": user["role"]}), 200