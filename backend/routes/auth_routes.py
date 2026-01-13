# auth_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from extensions import mongo, bcrypt
from models.user import User
from utils.validators import validate_email, validate_password, validate_role
from utils.decorators import admin_only, landlord_only, tenant_only
from services.notification_service import NotificationService

# Blueprint with URL prefix /auth
auth_bp = Blueprint("auth", __name__)

# Initialize notification service
notification_service = NotificationService()

# ---------------------------
# REGISTER USER
# ---------------------------
@auth_bp.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        email = data.get("email")
        password = data.get("password")
        role = data.get("role")

        # Validation
        if not validate_email(email):
            return jsonify({"error": "Invalid email format"}), 400

        if not validate_password(password):
            return jsonify({"error": "Password must be at least 6 characters"}), 400

        if not validate_role(role):
            return jsonify({"error": "Invalid role. Must be admin, landlord, or tenant"}), 400

        # Check if user already exists
        existing_user = mongo.db.users.find_one({"email": email})
        if existing_user:
            return jsonify({"error": "User already exists"}), 409

        # Hash password
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        # Create user object and insert into DB
        user = User(email=email, password=hashed_password, role=role)
        user_dict = user.to_dict()
        result = mongo.db.users.insert_one(user_dict)
        
        # SEND WELCOME NOTIFICATION
        user_dict['_id'] = result.inserted_id
        user_dict['name'] = email.split('@')[0]  # Use email prefix as name
        
        notification_service.notify_welcome(user_dict)
        # mongo.db.users.insert_one(user.to_dict())

        return jsonify({
            "message": "User registered successfully",
            "email": email,
            "role": role
        }), 201
    
    except Exception as e:
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500

# ---------------------------
# LOGIN USER
# ---------------------------
@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        # Find user
        user = mongo.db.users.find_one({"email": email})
        if not user:
            return jsonify({"error": "Invalid credentials"}), 401

        # Check password
        if not bcrypt.check_password_hash(user["password"], password):
            return jsonify({"error": "Invalid credentials"}), 401

        # ✅ FIXED: Create JWT token with correct structure
        # identity must be a STRING (becomes 'sub' claim)
        # Additional data goes in additional_claims
        access_token = create_access_token(
            identity=str(user["_id"]),  # ✅ String user ID for 'sub' claim
            additional_claims={
                "email": user["email"],
                "role": user["role"]
            }
        )
        
        return jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "user": {
                "user_id": str(user["_id"]),  # Added for clarity
                "email": user["email"],
                "role": user["role"]
            }
        }), 200
    
    except Exception as e:
        return jsonify({"error": f"Login failed: {str(e)}"}), 500

# ---------------------------
# GET CURRENT USER
# ---------------------------
@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    try:
        # ✅ FIXED: Get user ID from identity and other data from claims
        user_id = get_jwt_identity()  # Returns string user ID
        claims = get_jwt()  # Get additional claims
        
        return jsonify({
            "user": {
                "user_id": user_id,
                "email": claims.get("email"),
                "role": claims.get("role")
            }
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get user: {str(e)}"}), 500

# ---------------------------
# ROLE-BASED ROUTES
# ---------------------------

# Admin-only route
@auth_bp.route("/admin/dashboard", methods=["GET"])
@jwt_required()
@admin_only
def admin_dashboard():
    user_id = get_jwt_identity()
    claims = get_jwt()
    
    return jsonify({
        "message": "Welcome to the admin dashboard",
        "user": {
            "user_id": user_id,
            "email": claims.get("email"),
            "role": claims.get("role")
        }
    }), 200

# Landlord-only route
@auth_bp.route("/landlord/properties", methods=["GET"])
@jwt_required()
@landlord_only
def landlord_properties():
    user_id = get_jwt_identity()
    claims = get_jwt()
    
    return jsonify({
        "message": "Here are your properties",
        "user": {
            "user_id": user_id,
            "email": claims.get("email"),
            "role": claims.get("role")
        }
    }), 200

# Tenant-only route
@auth_bp.route("/tenant/bookings", methods=["GET"])
@jwt_required()
@tenant_only
def tenant_bookings():
    user_id = get_jwt_identity()
    claims = get_jwt()
    
    return jsonify({
        "message": "Here are your bookings",
        "user": {
            "user_id": user_id,
            "email": claims.get("email"),
            "role": claims.get("role")
        }
    }), 200