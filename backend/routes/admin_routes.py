# ============================================================================
# FILE 1: backend/routes/admin_routes.py
# ============================================================================
"""
Admin Routes - Dashboard, User Management, Property Moderation
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from extensions import mongo, bcrypt
from utils.decorators import admin_only
from bson import ObjectId
from datetime import datetime, timedelta

admin_bp = Blueprint("admin", __name__)

# ============================================================================
# ADMIN DASHBOARD & STATISTICS
# ============================================================================

@admin_bp.route("/dashboard/stats", methods=["GET"])
@jwt_required()
@admin_only
def get_dashboard_stats():
    """Get comprehensive dashboard statistics"""
    try:
        print("\n📊 Admin Dashboard Stats Request")
        
        # ===== USER STATISTICS =====
        total_users = mongo.db.users.count_documents({})
        users_by_role = list(mongo.db.users.aggregate([
            {"$group": {
                "_id": "$role",
                "count": {"$sum": 1}
            }}
        ]))
        
        # Recent users (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_users = mongo.db.users.count_documents({
            "created_at": {"$gte": thirty_days_ago}
        })
        
        # ===== PROPERTY STATISTICS =====
        total_properties = mongo.db.properties.count_documents({})
        properties_by_status = list(mongo.db.properties.aggregate([
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }}
        ]))
        
        # Properties by moderation status
        properties_by_moderation = list(mongo.db.properties.aggregate([
            {"$group": {
                "_id": "$moderation_status",
                "count": {"$sum": 1}
            }}
        ]))
        
        # Pending properties (need review)
        pending_properties = mongo.db.properties.count_documents({
            "moderation_status": "pending_review"
        })
        
        # Average moderation score
        avg_score_pipeline = [
            {"$group": {
                "_id": None,
                "avg_score": {"$avg": "$moderation_score"}
            }}
        ]
        avg_score_result = list(mongo.db.properties.aggregate(avg_score_pipeline))
        avg_moderation_score = round(avg_score_result[0]["avg_score"], 2) if avg_score_result else 0
        
        # ===== BOOKING STATISTICS =====
        total_bookings = mongo.db.bookings.count_documents({})
        bookings_by_status = list(mongo.db.bookings.aggregate([
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }}
        ]))
        
        # Recent bookings
        recent_bookings = mongo.db.bookings.count_documents({
            "created_at": {"$gte": thirty_days_ago}
        })
        
        # ===== NOTIFICATION STATISTICS =====
        total_notifications = mongo.db.notifications.count_documents({})
        unread_notifications = mongo.db.notifications.count_documents({
            "is_read": False
        })
        
        # ===== SYSTEM HEALTH =====
        # Check if collections are accessible
        collections_status = {
            "users": True,
            "properties": True,
            "bookings": True,
            "notifications": True
        }
        
        response_data = {
            "users": {
                "total": total_users,
                "by_role": users_by_role,
                "recent_30_days": recent_users
            },
            "properties": {
                "total": total_properties,
                "by_status": properties_by_status,
                "by_moderation": properties_by_moderation,
                "pending_review": pending_properties,
                "avg_moderation_score": avg_moderation_score
            },
            "bookings": {
                "total": total_bookings,
                "by_status": bookings_by_status,
                "recent_30_days": recent_bookings
            },
            "notifications": {
                "total": total_notifications,
                "unread": unread_notifications
            },
            "system": {
                "status": "healthy",
                "collections": collections_status,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        print(f"✅ Stats compiled: {total_users} users, {total_properties} properties")
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"❌ Error getting dashboard stats: {str(e)}")
        return jsonify({"error": f"Failed to get dashboard stats: {str(e)}"}), 500


@admin_bp.route("/dashboard/recent-activity", methods=["GET"])
@jwt_required()
@admin_only
def get_recent_activity():
    """Get recent activity across the platform"""
    try:
        limit = request.args.get("limit", 20, type=int)
        
        # Recent user registrations
        recent_users = list(mongo.db.users.find(
            {},
            {"email": 1, "role": 1, "created_at": 1}
        ).sort("_id", -1).limit(limit))
        
        # Recent property listings
        recent_properties = list(mongo.db.properties.find(
            {},
            {"title": 1, "city": 1, "price": 1, "status": 1, "moderation_status": 1, "created_at": 1}
        ).sort("created_at", -1).limit(limit))
        
        # Recent bookings
        recent_bookings = list(mongo.db.bookings.find(
            {},
            {"property_id": 1, "tenant_id": 1, "status": 1, "booking_date": 1, "created_at": 1}
        ).sort("created_at", -1).limit(limit))
        
        # Convert ObjectIds to strings
        for user in recent_users:
            user["_id"] = str(user["_id"])
            if user.get("created_at") and isinstance(user["created_at"], datetime):
                user["created_at"] = user["created_at"].isoformat()
        
        for prop in recent_properties:
            prop["_id"] = str(prop["_id"])
            if prop.get("created_at") and isinstance(prop["created_at"], datetime):
                prop["created_at"] = prop["created_at"].isoformat()
        
        for booking in recent_bookings:
            booking["_id"] = str(booking["_id"])
            booking["property_id"] = str(booking["property_id"])
            booking["tenant_id"] = str(booking["tenant_id"])
            if booking.get("created_at") and isinstance(booking["created_at"], datetime):
                booking["created_at"] = booking["created_at"].isoformat()
        
        return jsonify({
            "recent_users": recent_users,
            "recent_properties": recent_properties,
            "recent_bookings": recent_bookings
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get recent activity: {str(e)}"}), 500


# ============================================================================
# USER MANAGEMENT
# ============================================================================

@admin_bp.route("/users", methods=["GET"])
@jwt_required()
@admin_only
def get_all_users():
    """Get all users with filtering and pagination"""
    try:
        # Query parameters
        role = request.args.get("role")
        search = request.args.get("search")
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        sort_by = request.args.get("sort_by", "newest")
        
        # Build query
        query = {}
        
        if role:
            query["role"] = role
        
        if search:
            query["$or"] = [
                {"email": {"$regex": search, "$options": "i"}}
            ]
        
        # Get total count
        total_count = mongo.db.users.count_documents(query)
        
        # Build sort criteria
        if sort_by == "oldest":
            sort_criteria = [("_id", 1)]
        else:  # newest (default)
            sort_criteria = [("_id", -1)]
        
        # Apply pagination
        skip = (page - 1) * per_page
        users_cursor = mongo.db.users.find(
            query,
            {"password": 0}  # Exclude password
        ).sort(sort_criteria).skip(skip).limit(per_page)
        
        users = list(users_cursor)
        
        # Get additional stats for each user
        for user in users:
            user_id = str(user["_id"])
            user["_id"] = user_id
            
            # Count properties if landlord
            if user["role"] == "landlord":
                user["properties_count"] = mongo.db.properties.count_documents({
                    "landlord_id": user_id
                })
            
            # Count bookings
            if user["role"] == "tenant":
                user["bookings_count"] = mongo.db.bookings.count_documents({
                    "tenant_id": user_id
                })
            elif user["role"] == "landlord":
                user["bookings_count"] = mongo.db.bookings.count_documents({
                    "landlord_id": user_id
                })
            
            # Convert datetime
            if user.get("created_at") and isinstance(user["created_at"], datetime):
                user["created_at"] = user["created_at"].isoformat()
        
        return jsonify({
            "users": users,
            "count": len(users),
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "total_pages": (total_count + per_page - 1) // per_page
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to fetch users: {str(e)}"}), 500


@admin_bp.route("/users/<user_id>", methods=["GET"])
@jwt_required()
@admin_only
def get_user_details(user_id):
    """Get detailed information about a specific user"""
    try:
        if not ObjectId.is_valid(user_id):
            return jsonify({"error": "Invalid user ID"}), 400
        
        # Get user
        user = mongo.db.users.find_one(
            {"_id": ObjectId(user_id)},
            {"password": 0}  # Exclude password
        )
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        user["_id"] = str(user["_id"])
        
        # Get user's properties (if landlord)
        if user["role"] == "landlord":
            properties = list(mongo.db.properties.find(
                {"landlord_id": user_id},
                {"title": 1, "city": 1, "price": 1, "status": 1, "created_at": 1}
            ).limit(10))
            
            for prop in properties:
                prop["_id"] = str(prop["_id"])
                if prop.get("created_at") and isinstance(prop["created_at"], datetime):
                    prop["created_at"] = prop["created_at"].isoformat()
            
            user["properties"] = properties
            user["total_properties"] = mongo.db.properties.count_documents({"landlord_id": user_id})
        
        # Get user's bookings
        bookings = list(mongo.db.bookings.find(
            {"tenant_id": user_id} if user["role"] == "tenant" else {"landlord_id": user_id}
        ).sort("created_at", -1).limit(10))
        
        for booking in bookings:
            booking["_id"] = str(booking["_id"])
            booking["property_id"] = str(booking["property_id"])
            if booking.get("created_at") and isinstance(booking["created_at"], datetime):
                booking["created_at"] = booking["created_at"].isoformat()
        
        user["recent_bookings"] = bookings
        user["total_bookings"] = mongo.db.bookings.count_documents(
            {"tenant_id": user_id} if user["role"] == "tenant" else {"landlord_id": user_id}
        )
        
        # Convert datetime
        if user.get("created_at") and isinstance(user["created_at"], datetime):
            user["created_at"] = user["created_at"].isoformat()
        
        return jsonify(user), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to fetch user details: {str(e)}"}), 500


@admin_bp.route("/users/<user_id>/suspend", methods=["PUT"])
@jwt_required()
@admin_only
def suspend_user(user_id):
    """Suspend a user account"""
    try:
        if not ObjectId.is_valid(user_id):
            return jsonify({"error": "Invalid user ID"}), 400
        
        data = request.get_json() or {}
        reason = data.get("reason", "Account suspended by admin")
        
        # Check if user exists
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Prevent admin from suspending themselves
        current_admin_id = get_jwt_identity()
        if str(user_id) == current_admin_id:
            return jsonify({"error": "Cannot suspend your own account"}), 400
        
        # Update user status
        mongo.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "is_suspended": True,
                "suspension_reason": reason,
                "suspended_at": datetime.utcnow(),
                "suspended_by": current_admin_id
            }}
        )
        
        # If landlord, deactivate all their properties
        if user["role"] == "landlord":
            mongo.db.properties.update_many(
                {"landlord_id": user_id},
                {"$set": {"status": "inactive"}}
            )
        
        print(f"✅ User suspended: {user['email']}")
        
        return jsonify({
            "message": "User suspended successfully",
            "user_id": user_id
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to suspend user: {str(e)}"}), 500


@admin_bp.route("/users/<user_id>/activate", methods=["PUT"])
@jwt_required()
@admin_only
def activate_user(user_id):
    """Activate/unsuspend a user account"""
    try:
        if not ObjectId.is_valid(user_id):
            return jsonify({"error": "Invalid user ID"}), 400
        
        # Check if user exists
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Update user status
        mongo.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "is_suspended": False,
                    "activated_at": datetime.utcnow()
                },
                "$unset": {
                    "suspension_reason": "",
                    "suspended_at": "",
                    "suspended_by": ""
                }
            }
        )
        
        print(f"✅ User activated: {user['email']}")
        
        return jsonify({
            "message": "User activated successfully",
            "user_id": user_id
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to activate user: {str(e)}"}), 500


@admin_bp.route("/users/<user_id>", methods=["DELETE"])
@jwt_required()
@admin_only
def delete_user(user_id):
    """Delete a user account (with confirmation)"""
    try:
        if not ObjectId.is_valid(user_id):
            return jsonify({"error": "Invalid user ID"}), 400
        
        # Check if user exists
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Prevent admin from deleting themselves
        current_admin_id = get_jwt_identity()
        if str(user_id) == current_admin_id:
            return jsonify({"error": "Cannot delete your own account"}), 400
        
        # Prevent deleting other admins
        if user["role"] == "admin":
            return jsonify({"error": "Cannot delete admin accounts"}), 403
        
        # Delete user's data
        if user["role"] == "landlord":
            # Delete properties
            mongo.db.properties.delete_many({"landlord_id": user_id})
            # Delete bookings
            mongo.db.bookings.delete_many({"landlord_id": user_id})
        elif user["role"] == "tenant":
            # Delete bookings
            mongo.db.bookings.delete_many({"tenant_id": user_id})
        
        # Delete notifications
        mongo.db.notifications.delete_many({"user_id": user_id})
        
        # Delete user
        mongo.db.users.delete_one({"_id": ObjectId(user_id)})
        
        print(f"✅ User deleted: {user['email']}")
        
        return jsonify({
            "message": "User and associated data deleted successfully",
            "user_id": user_id
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to delete user: {str(e)}"}), 500


# ============================================================================
# PROPERTY MODERATION QUEUE
# ============================================================================

@admin_bp.route("/moderation/queue", methods=["GET"])
@jwt_required()
@admin_only
def get_moderation_queue():
    """Get all properties pending review"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        sort_by = request.args.get("sort_by", "score_low")  # score_low, score_high, newest, oldest
        
        # Query for pending review properties
        query = {"moderation_status": "pending_review"}
        
        # Build sort criteria
        if sort_by == "score_low":
            sort_criteria = [("moderation_score", 1)]  # Lowest scores first
        elif sort_by == "score_high":
            sort_criteria = [("moderation_score", -1)]
        elif sort_by == "oldest":
            sort_criteria = [("created_at", 1)]
        else:  # newest
            sort_criteria = [("created_at", -1)]
        
        # Get total count
        total_count = mongo.db.properties.count_documents(query)
        
        # Apply pagination
        skip = (page - 1) * per_page
        properties_cursor = mongo.db.properties.find(query).sort(sort_criteria).skip(skip).limit(per_page)
        properties = list(properties_cursor)
        
        # Enrich with landlord details
        for prop in properties:
            landlord = mongo.db.users.find_one(
                {"_id": ObjectId(prop["landlord_id"])},
                {"email": 1, "role": 1}
            )
            
            if landlord:
                prop["landlord_info"] = {
                    "email": landlord["email"],
                    "user_id": str(landlord["_id"])
                }
            
            # Convert ObjectIds
            prop["_id"] = str(prop["_id"])
            prop["landlord_id"] = str(prop["landlord_id"])
            
            # Convert datetime
            if prop.get("created_at") and isinstance(prop["created_at"], datetime):
                prop["created_at"] = prop["created_at"].isoformat()
            if prop.get("moderated_at") and isinstance(prop["moderated_at"], datetime):
                prop["moderated_at"] = prop["moderated_at"].isoformat()
        
        return jsonify({
            "properties": properties,
            "count": len(properties),
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "total_pages": (total_count + per_page - 1) // per_page
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to fetch moderation queue: {str(e)}"}), 500


@admin_bp.route("/moderation/<property_id>/approve", methods=["PUT"])
@jwt_required()
@admin_only
def approve_property(property_id):
    """Manually approve a property"""
    try:
        admin_id = get_jwt_identity()
        data = request.get_json() or {}
        
        if not ObjectId.is_valid(property_id):
            return jsonify({"error": "Invalid property ID"}), 400
        
        # Get property
        prop = mongo.db.properties.find_one({"_id": ObjectId(property_id)})
        if not prop:
            return jsonify({"error": "Property not found"}), 404
        
        # Update property
        mongo.db.properties.update_one(
            {"_id": ObjectId(property_id)},
            {"$set": {
                "moderation_status": "approved",
                "status": "active",
                "moderation_notes": data.get("notes", "Approved by admin"),
                "moderated_at": datetime.utcnow(),
                "moderated_by": admin_id,
                "updated_at": datetime.utcnow()
            }}
        )
        
        print(f"✅ Property approved by admin: {prop['title']}")
        
        # TODO: Send notification to landlord
        
        return jsonify({
            "message": "Property approved successfully",
            "property_id": property_id
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to approve property: {str(e)}"}), 500


@admin_bp.route("/moderation/<property_id>/reject", methods=["PUT"])
@jwt_required()
@admin_only
def reject_property(property_id):
    """Manually reject a property"""
    try:
        admin_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get("reason"):
            return jsonify({"error": "Rejection reason is required"}), 400
        
        if not ObjectId.is_valid(property_id):
            return jsonify({"error": "Invalid property ID"}), 400
        
        # Get property
        prop = mongo.db.properties.find_one({"_id": ObjectId(property_id)})
        if not prop:
            return jsonify({"error": "Property not found"}), 404
        
        # Update property
        mongo.db.properties.update_one(
            {"_id": ObjectId(property_id)},
            {"$set": {
                "moderation_status": "rejected",
                "status": "inactive",
                "moderation_notes": data["reason"],
                "moderated_at": datetime.utcnow(),
                "moderated_by": admin_id,
                "updated_at": datetime.utcnow()
            }}
        )
        
        print(f"❌ Property rejected by admin: {prop['title']}")
        
        # TODO: Send notification to landlord with rejection reason
        
        return jsonify({
            "message": "Property rejected successfully",
            "property_id": property_id
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to reject property: {str(e)}"}), 500


# ============================================================================
# SYSTEM ANALYTICS
# ============================================================================

@admin_bp.route("/analytics/growth", methods=["GET"])
@jwt_required()
@admin_only
def get_growth_analytics():
    """Get user and property growth trends"""
    try:
        days = request.args.get("days", 30, type=int)
        
        # Get date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # User growth
        user_growth_pipeline = [
            {"$match": {"created_at": {"$gte": start_date, "$lte": end_date}}},
            {"$group": {
                "_id": {
                    "year": {"$year": "$created_at"},
                    "month": {"$month": "$created_at"},
                    "day": {"$dayOfMonth": "$created_at"}
                },
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        user_growth = list(mongo.db.users.aggregate(user_growth_pipeline))
        
        # Property growth
        property_growth_pipeline = [
            {"$match": {"created_at": {"$gte": start_date, "$lte": end_date}}},
            {"$group": {
                "_id": {
                    "year": {"$year": "$created_at"},
                    "month": {"$month": "$created_at"},
                    "day": {"$dayOfMonth": "$created_at"}
                },
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        property_growth = list(mongo.db.properties.aggregate(property_growth_pipeline))
        
        return jsonify({
            "period_days": days,
            "user_growth": user_growth,
            "property_growth": property_growth
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to fetch growth analytics: {str(e)}"}), 500