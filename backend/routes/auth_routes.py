# auth_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from extensions import mongo, bcrypt
from models.user import User
from utils.validators import validate_email, validate_password, validate_role
from utils.decorators import admin_only, landlord_only, tenant_only
from services.notification_service import NotificationService
from datetime import datetime, timedelta
import secrets
import string

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

        if not validate_email(email):
            return jsonify({"error": "Invalid email format"}), 400

        if not validate_password(password):
            return jsonify({"error": "Password must be at least 6 characters"}), 400

        if not validate_role(role):
            return jsonify({"error": "Invalid role. Must be admin, landlord, or tenant"}), 400

        existing_user = mongo.db.users.find_one({"email": email})
        if existing_user:
            return jsonify({"error": "User already exists"}), 409

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        user = User(email=email, password=hashed_password, role=role)
        user_dict = user.to_dict()
        result = mongo.db.users.insert_one(user_dict)
        
        user_dict['_id'] = result.inserted_id
        user_dict['name'] = email.split('@')[0]
        
        notification_service.notify_welcome(user_dict)

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

        # ✅ CHECK SUSPENSION — block login before issuing a token
        if user.get("is_suspended"):
            suspension_reason = user.get("suspension_reason", "Your account has been suspended.")
            print(f"🚫 Blocked login for suspended user: {email}")
            return jsonify({
                "error": "account_suspended",
                "message": "Your account has been suspended. Please contact support.",
                "reason": suspension_reason
            }), 403

        # Create JWT token
        access_token = create_access_token(
            identity=str(user["_id"]),
            additional_claims={
                "email": user["email"],
                "role": user["role"]
            }
        )
        
        return jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "user": {
                "user_id": str(user["_id"]),
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
        user_id = get_jwt_identity()
        claims = get_jwt()

        # ✅ Also check suspension on /me in case account was suspended mid-session
        user = mongo.db.users.find_one({"_id": __import__('bson').ObjectId(user_id)}, {"is_suspended": 1, "suspension_reason": 1})
        if user and user.get("is_suspended"):
            return jsonify({
                "error": "account_suspended",
                "message": "Your account has been suspended. Please contact support.",
                "reason": user.get("suspension_reason", "")
            }), 403
        
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

# ---------------------------
# REQUEST PASSWORD RESET
# ---------------------------
@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    try:
        data = request.get_json()
        email = data.get("email")
        
        if not email:
            return jsonify({"error": "Email is required"}), 400
        
        if not validate_email(email):
            return jsonify({"error": "Invalid email format"}), 400
        
        user = mongo.db.users.find_one({"email": email})
        
        if not user:
            return jsonify({
                "message": "If an account exists with this email, a password reset link has been sent.",
                "email": email
            }), 200
        
        reset_token = ''.join(secrets.choice(string.digits) for _ in range(6))
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        mongo.db.password_resets.update_one(
            {"email": email},
            {
                "$set": {
                    "email": email,
                    "token": reset_token,
                    "expires_at": expires_at,
                    "used": False,
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )
        
        print(f"\n{'='*50}")
        print(f"🔐 PASSWORD RESET TOKEN FOR: {email}")
        print(f"Token: {reset_token}")
        print(f"Expires: {expires_at}")
        print(f"{'='*50}\n")
        
        return jsonify({
            "message": "If an account exists with this email, a password reset link has been sent.",
            "email": email,
            "dev_token": reset_token  # Remove in production
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to process request: {str(e)}"}), 500


# ---------------------------
# VERIFY RESET TOKEN
# ---------------------------
@auth_bp.route("/verify-reset-token", methods=["POST"])
def verify_reset_token():
    try:
        data = request.get_json()
        email = data.get("email")
        token = data.get("token")
        
        if not email or not token:
            return jsonify({"error": "Email and token are required"}), 400
        
        reset_request = mongo.db.password_resets.find_one({
            "email": email,
            "token": token,
            "used": False
        })
        
        if not reset_request:
            return jsonify({"error": "Invalid or expired reset token"}), 400
        
        if reset_request["expires_at"] < datetime.utcnow():
            return jsonify({"error": "Reset token has expired"}), 400
        
        return jsonify({
            "message": "Token is valid",
            "email": email
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to verify token: {str(e)}"}), 500


# ---------------------------
# RESET PASSWORD
# ---------------------------
@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    try:
        data = request.get_json()
        email = data.get("email")
        token = data.get("token")
        new_password = data.get("new_password")
        
        if not email or not token or not new_password:
            return jsonify({"error": "Email, token, and new password are required"}), 400
        
        if not validate_password(new_password):
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        
        reset_request = mongo.db.password_resets.find_one({
            "email": email,
            "token": token,
            "used": False
        })
        
        if not reset_request:
            return jsonify({"error": "Invalid or expired reset token"}), 400
        
        if reset_request["expires_at"] < datetime.utcnow():
            return jsonify({"error": "Reset token has expired"}), 400
        
        user = mongo.db.users.find_one({"email": email})
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        hashed_password = bcrypt.generate_password_hash(new_password).decode("utf-8")
        
        mongo.db.users.update_one(
            {"email": email},
            {"$set": {"password": hashed_password}}
        )
        
        mongo.db.password_resets.update_one(
            {"email": email, "token": token},
            {"$set": {"used": True, "used_at": datetime.utcnow()}}
        )
        
        return jsonify({
            "message": "Password has been reset successfully",
            "email": email
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to reset password: {str(e)}"}), 500


# ---------------------------
# CHANGE PASSWORD
# ---------------------------
@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        email = claims.get("email")
        
        data = request.get_json()
        current_password = data.get("current_password")
        new_password = data.get("new_password")
        
        if not current_password or not new_password:
            return jsonify({"error": "Current and new passwords are required"}), 400
        
        if not validate_password(new_password):
            return jsonify({"error": "New password must be at least 6 characters"}), 400
        
        user = mongo.db.users.find_one({"email": email})
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        if not bcrypt.check_password_hash(user["password"], current_password):
            return jsonify({"error": "Current password is incorrect"}), 401
        
        hashed_password = bcrypt.generate_password_hash(new_password).decode("utf-8")
        
        mongo.db.users.update_one(
            {"email": email},
            {"$set": {"password": hashed_password}}
        )
        
        return jsonify({
            "message": "Password changed successfully"
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to change password: {str(e)}"}), 500