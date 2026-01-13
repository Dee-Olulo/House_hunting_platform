from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import mongo
from services.notification_service import NotificationService
from bson import ObjectId
from datetime import datetime

notification_bp = Blueprint("notification", __name__)
notification_service = NotificationService()

# ---------------------------
# GET ALL NOTIFICATIONS FOR USER
# ---------------------------
@notification_bp.route("/", methods=["GET"])
@jwt_required()
def get_notifications():
    """Get all notifications for the current user"""
    try:
        user_id = get_jwt_identity()
        
        # Get query parameters
        is_read = request.args.get("is_read")
        notification_type = request.args.get("type")
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        
        # Build query
        query = {"user_id": user_id}
        
        if is_read is not None:
            query["is_read"] = is_read.lower() == "true"
        
        if notification_type:
            query["notification_type"] = notification_type
        
        # Get total count
        total_count = mongo.db.notifications.count_documents(query)
        
        # Apply pagination and sorting (newest first)
        skip = (page - 1) * per_page
        notifications_cursor = mongo.db.notifications.find(query).sort("created_at", -1).skip(skip).limit(per_page)
        notifications = list(notifications_cursor)
        
        # Convert ObjectIds to strings
        for notification in notifications:
            notification["_id"] = str(notification["_id"])
            if notification.get("created_at") and isinstance(notification["created_at"], datetime):
                notification["created_at"] = notification["created_at"].isoformat()
            if notification.get("read_at") and isinstance(notification["read_at"], datetime):
                notification["read_at"] = notification["read_at"].isoformat()
        
        return jsonify({
            "notifications": notifications,
            "count": len(notifications),
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "total_pages": (total_count + per_page - 1) // per_page
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to fetch notifications: {str(e)}"}), 500


# ---------------------------
# GET UNREAD COUNT
# ---------------------------
@notification_bp.route("/unread-count", methods=["GET"])
@jwt_required()
def get_unread_count():
    """Get count of unread notifications"""
    try:
        user_id = get_jwt_identity()
        count = notification_service.get_unread_count(user_id)
        
        return jsonify({
            "unread_count": count
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get unread count: {str(e)}"}), 500


# ---------------------------
# MARK NOTIFICATION AS READ
# ---------------------------
@notification_bp.route("/<notification_id>/read", methods=["PUT"])
@jwt_required()
def mark_notification_as_read(notification_id):
    """Mark a specific notification as read"""
    try:
        user_id = get_jwt_identity()
        
        # Validate notification ID
        if not ObjectId.is_valid(notification_id):
            return jsonify({"error": "Invalid notification ID"}), 400
        
        # Check if notification exists and belongs to user
        notification = mongo.db.notifications.find_one({
            "_id": ObjectId(notification_id),
            "user_id": user_id
        })
        
        if not notification:
            return jsonify({"error": "Notification not found"}), 404
        
        # Mark as read
        success = notification_service.mark_as_read(ObjectId(notification_id), user_id)
        
        if success:
            return jsonify({"message": "Notification marked as read"}), 200
        else:
            return jsonify({"error": "Failed to mark notification as read"}), 500
        
    except Exception as e:
        return jsonify({"error": f"Failed to mark notification as read: {str(e)}"}), 500


# ---------------------------
# MARK ALL AS READ
# ---------------------------
@notification_bp.route("/read-all", methods=["PUT"])
@jwt_required()
def mark_all_as_read():
    """Mark all notifications as read for current user"""
    try:
        user_id = get_jwt_identity()
        success = notification_service.mark_all_as_read(user_id)
        
        if success:
            return jsonify({"message": "All notifications marked as read"}), 200
        else:
            return jsonify({"error": "Failed to mark all as read"}), 500
        
    except Exception as e:
        return jsonify({"error": f"Failed to mark all as read: {str(e)}"}), 500


# ---------------------------
# DELETE NOTIFICATION
# ---------------------------
@notification_bp.route("/<notification_id>", methods=["DELETE"])
@jwt_required()
def delete_notification(notification_id):
    """Delete a specific notification"""
    try:
        user_id = get_jwt_identity()
        
        # Validate notification ID
        if not ObjectId.is_valid(notification_id):
            return jsonify({"error": "Invalid notification ID"}), 400
        
        # Delete notification
        success = notification_service.delete_notification(ObjectId(notification_id), user_id)
        
        if success:
            return jsonify({"message": "Notification deleted successfully"}), 200
        else:
            return jsonify({"error": "Notification not found or already deleted"}), 404
        
    except Exception as e:
        return jsonify({"error": f"Failed to delete notification: {str(e)}"}), 500


# ---------------------------
# DELETE ALL NOTIFICATIONS
# ---------------------------
@notification_bp.route("/delete-all", methods=["DELETE"])
@jwt_required()
def delete_all_notifications():
    """Delete all notifications for current user"""
    try:
        user_id = get_jwt_identity()
        
        result = mongo.db.notifications.delete_many({"user_id": user_id})
        
        return jsonify({
            "message": f"Deleted {result.deleted_count} notifications",
            "deleted_count": result.deleted_count
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to delete all notifications: {str(e)}"}), 500


# ---------------------------
# GET NOTIFICATION STATISTICS
# ---------------------------
@notification_bp.route("/statistics", methods=["GET"])
@jwt_required()
def get_notification_statistics():
    """Get notification statistics for current user"""
    try:
        user_id = get_jwt_identity()
        
        # Total notifications
        total_count = mongo.db.notifications.count_documents({"user_id": user_id})
        
        # Unread count
        unread_count = mongo.db.notifications.count_documents({
            "user_id": user_id,
            "is_read": False
        })
        
        # Notifications by type
        type_pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": "$notification_type",
                "count": {"$sum": 1}
            }}
        ]
        by_type = list(mongo.db.notifications.aggregate(type_pipeline))
        
        # Recent notifications (last 7 days)
        from datetime import timedelta
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_count = mongo.db.notifications.count_documents({
            "user_id": user_id,
            "created_at": {"$gte": seven_days_ago}
        })
        
        return jsonify({
            "total_notifications": total_count,
            "unread_count": unread_count,
            "read_count": total_count - unread_count,
            "by_type": by_type,
            "recent_count": recent_count
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get statistics: {str(e)}"}), 500


# ---------------------------
# CLEANUP OLD NOTIFICATIONS (ADMIN)
# ---------------------------
@notification_bp.route("/cleanup", methods=["POST"])
@jwt_required()
def cleanup_old_notifications():
    """
    Cleanup notifications older than specified days
    This should ideally be restricted to admin users
    """
    try:
        data = request.get_json() or {}
        days = data.get("days", 30)
        
        deleted_count = notification_service.cleanup_old_notifications(days)
        
        return jsonify({
            "message": f"Cleaned up notifications older than {days} days",
            "deleted_count": deleted_count
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to cleanup notifications: {str(e)}"}), 500