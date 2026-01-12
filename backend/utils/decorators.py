
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, get_jwt

def admin_only(fn):
    """Decorator to restrict access to admin users only"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # ✅ FIXED: Get role from claims, not from identity
        claims = get_jwt()
        role = claims.get("role")
        
        if role != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper

def landlord_only(fn):
    """Decorator to restrict access to landlord users only"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # ✅ FIXED: Get role from claims, not from identity
        claims = get_jwt()
        role = claims.get("role")
        
        if role != "landlord":
            return jsonify({"error": "Landlord access required"}), 403
        return fn(*args, **kwargs)
    return wrapper

def tenant_only(fn):
    """Decorator to restrict access to tenant users only"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # ✅ FIXED: Get role from claims, not from identity
        claims = get_jwt()
        role = claims.get("role")
        
        if role != "tenant":
            return jsonify({"error": "Tenant access required"}), 403
        return fn(*args, **kwargs)
    return wrapper