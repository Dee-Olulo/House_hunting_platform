from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from extensions import mongo, bcrypt
from models.user import User
from utils.validators import validate_email, validate_password, validate_role

auth_bp = Blueprint("auth", __name__)

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

    # Check if user exists
    existing_user = mongo.db.users.find_one({"email": email})
    if existing_user:
        return jsonify({"error": "User already exists"}), 409

    # Hash password
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

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

    user = mongo.db.users.find_one({"email": email})

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    if not bcrypt.check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    # Create JWT token with role
    access_token = create_access_token(
        identity={
            "user_id": str(user["_id"]),
            "role": user["role"]
        }
    )

    return jsonify({
        "access_token": access_token,
        "role": user["role"]
    }), 200
