from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from extensions import mongo

def role_required(required_role):
    """
    Generic decorator to check if a user has a specific role.
    Usage: @role_required("admin")
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Get the logged-in user's email from JWT
            identity = get_jwt_identity()
            if not identity:
                return jsonify({"error": "Missing JWT token"}), 401

            user = mongo.db.users.find_one({"email": identity})
            if not user:
                return jsonify({"error": "User not found"}), 404

            if user.get("role") != required_role:
                return jsonify({"error": f"{required_role.capitalize()} role required"}), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator

# Shortcut decorators
admin_only = role_required("admin")
landlord_only = role_required("landlord")
tenant_only = role_required("tenant")
