# backend/routes/admin_notification_routes.py
"""
Admin Notification Management Routes
Broadcast messages, campaigns, and notification templates
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import mongo
from utils.decorators import admin_only
from bson import ObjectId
from datetime import datetime, timedelta

admin_notification_bp = Blueprint("admin_notifications", __name__)

# ============================================================================
# BROADCAST MESSAGES
# ============================================================================

@admin_notification_bp.route("/broadcast", methods=["POST"])
@jwt_required()
@admin_only
def send_broadcast():
    """
    Send broadcast notification to all users or specific groups
    
    Request body:
    {
        "title": "System Maintenance",
        "message": "Platform will be down for 2 hours",
        "target_audience": "all" | "landlords" | "tenants",
        "notification_type": "system_announcement",
        "link": "/announcements/123" (optional)
    }
    """
    try:
        admin_id = get_jwt_identity()
        data = request.get_json()
        
        title = data.get('title')
        message = data.get('message')
        target_audience = data.get('target_audience', 'all')
        notification_type = data.get('notification_type', 'system_announcement')
        link = data.get('link')
        
        if not title or not message:
            return jsonify({"error": "Title and message are required"}), 400
        
        # Build query for target users
        query = {}
        if target_audience == 'landlords':
            query['role'] = 'landlord'
        elif target_audience == 'tenants':
            query['role'] = 'tenant'
        # 'all' means no role filter
        
        # Get all target users
        users = list(mongo.db.users.find(query, {"_id": 1}))
        user_ids = [str(user["_id"]) for user in users]
        
        # Create notification for each user
        notifications = []
        for user_id in user_ids:
            notification = {
                "user_id": user_id,
                "title": title,
                "message": message,
                "notification_type": notification_type,
                "link": link,
                "is_read": False,
                "created_at": datetime.utcnow(),
                "broadcast_id": str(ObjectId()),  # Group broadcasts together
                "sent_by": admin_id
            }
            notifications.append(notification)
        
        # Bulk insert
        if notifications:
            result = mongo.db.notifications.insert_many(notifications)
            
            # Log broadcast
            broadcast_log = {
                "admin_id": admin_id,
                "title": title,
                "message": message,
                "target_audience": target_audience,
                "notification_type": notification_type,
                "recipients_count": len(user_ids),
                "sent_at": datetime.utcnow()
            }
            mongo.db.broadcast_logs.insert_one(broadcast_log)
            
            print(f"✅ Broadcast sent to {len(user_ids)} users")
            
            return jsonify({
                "message": "Broadcast sent successfully",
                "recipients": len(user_ids)
            }), 200
        else:
            return jsonify({"error": "No users found for target audience"}), 404
        
    except Exception as e:
        print(f"❌ Error sending broadcast: {str(e)}")
        return jsonify({"error": f"Failed to send broadcast: {str(e)}"}), 500


# ============================================================================
# TARGETED CAMPAIGNS
# ============================================================================

@admin_notification_bp.route("/campaign", methods=["POST"])
@jwt_required()
@admin_only
def send_targeted_campaign():
    """
    Send targeted campaign to specific user segment
    
    Request body:
    {
        "title": "Renew Your Properties",
        "message": "Your properties are expiring soon",
        "criteria": {
            "role": "landlord",
            "inactive_days": 30,  # Landlords inactive for 30+ days
            "property_status": "inactive"  # With inactive properties
        }
    }
    """
    try:
        admin_id = get_jwt_identity()
        data = request.get_json()
        
        title = data.get('title')
        message = data.get('message')
        criteria = data.get('criteria', {})
        
        if not title or not message:
            return jsonify({"error": "Title and message required"}), 400
        
        # Build query based on criteria
        query = {}
        
        # Role filter
        if criteria.get('role'):
            query['role'] = criteria['role']
        
        # Get users
        users = list(mongo.db.users.find(query, {"_id": 1}))
        
        # Apply additional filters
        target_user_ids = []
        
        for user in users:
            user_id = str(user["_id"])
            include_user = True
            
            # Check inactive days
            if criteria.get('inactive_days'):
                inactive_threshold = datetime.utcnow() - timedelta(days=criteria['inactive_days'])
                # Check last booking or property update
                last_activity = mongo.db.bookings.find_one(
                    {"$or": [{"landlord_id": user_id}, {"tenant_id": user_id}]},
                    sort=[("created_at", -1)]
                )
                if last_activity and last_activity.get('created_at', datetime.min) > inactive_threshold:
                    include_user = False
            
            # Check property status
            if criteria.get('property_status') and user['_id']:
                property_count = mongo.db.properties.count_documents({
                    "landlord_id": user_id,
                    "status": criteria['property_status']
                })
                if property_count == 0:
                    include_user = False
            
            if include_user:
                target_user_ids.append(user_id)
        
        # Create notifications
        notifications = []
        for user_id in target_user_ids:
            notification = {
                "user_id": user_id,
                "title": title,
                "message": message,
                "notification_type": "campaign",
                "is_read": False,
                "created_at": datetime.utcnow(),
                "campaign_id": str(ObjectId()),
                "sent_by": admin_id
            }
            notifications.append(notification)
        
        if notifications:
            mongo.db.notifications.insert_many(notifications)
            
            # Log campaign
            campaign_log = {
                "admin_id": admin_id,
                "title": title,
                "message": message,
                "criteria": criteria,
                "recipients_count": len(target_user_ids),
                "sent_at": datetime.utcnow()
            }
            mongo.db.campaign_logs.insert_one(campaign_log)
            
            print(f"✅ Campaign sent to {len(target_user_ids)} users")
            
            return jsonify({
                "message": "Campaign sent successfully",
                "recipients": len(target_user_ids)
            }), 200
        else:
            return jsonify({"error": "No users match criteria"}), 404
        
    except Exception as e:
        return jsonify({"error": f"Failed to send campaign: {str(e)}"}), 500


# ============================================================================
# NOTIFICATION TEMPLATES
# ============================================================================

@admin_notification_bp.route("/templates", methods=["GET"])
@jwt_required()
@admin_only
def get_templates():
    """Get all notification templates"""
    try:
        templates = list(mongo.db.notification_templates.find())
        
        for template in templates:
            template["_id"] = str(template["_id"])
            if template.get("created_at"):
                template["created_at"] = template["created_at"].isoformat()
        
        return jsonify({"templates": templates}), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get templates: {str(e)}"}), 500


@admin_notification_bp.route("/templates", methods=["POST"])
@jwt_required()
@admin_only
def create_template():
    """
    Create notification template
    
    Request body:
    {
        "name": "Welcome Email",
        "title": "Welcome to {{platform_name}}!",
        "message": "Hi {{user_name}}, welcome aboard!",
        "notification_type": "welcome",
        "variables": ["platform_name", "user_name"]
    }
    """
    try:
        admin_id = get_jwt_identity()
        data = request.get_json()
        
        template = {
            "name": data.get('name'),
            "title": data.get('title'),
            "message": data.get('message'),
            "notification_type": data.get('notification_type'),
            "variables": data.get('variables', []),
            "created_by": admin_id,
            "created_at": datetime.utcnow(),
            "is_active": True
        }
        
        result = mongo.db.notification_templates.insert_one(template)
        template["_id"] = str(result.inserted_id)
        
        return jsonify({
            "message": "Template created successfully",
            "template": template
        }), 201
        
    except Exception as e:
        return jsonify({"error": f"Failed to create template: {str(e)}"}), 500


@admin_notification_bp.route("/templates/<template_id>", methods=["PUT"])
@jwt_required()
@admin_only
def update_template(template_id):
    """Update notification template"""
    try:
        if not ObjectId.is_valid(template_id):
            return jsonify({"error": "Invalid template ID"}), 400
        
        data = request.get_json()
        
        update_data = {
            "name": data.get('name'),
            "title": data.get('title'),
            "message": data.get('message'),
            "notification_type": data.get('notification_type'),
            "variables": data.get('variables', []),
            "updated_at": datetime.utcnow()
        }
        
        mongo.db.notification_templates.update_one(
            {"_id": ObjectId(template_id)},
            {"$set": update_data}
        )
        
        return jsonify({"message": "Template updated successfully"}), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to update template: {str(e)}"}), 500


@admin_notification_bp.route("/templates/<template_id>", methods=["DELETE"])
@jwt_required()
@admin_only
def delete_template(template_id):
    """Delete notification template"""
    try:
        if not ObjectId.is_valid(template_id):
            return jsonify({"error": "Invalid template ID"}), 400
        
        mongo.db.notification_templates.delete_one({"_id": ObjectId(template_id)})
        
        return jsonify({"message": "Template deleted successfully"}), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to delete template: {str(e)}"}), 500


# ============================================================================
# SCHEDULED NOTIFICATIONS
# ============================================================================

@admin_notification_bp.route("/schedule", methods=["POST"])
@jwt_required()
@admin_only
def schedule_notification():
    """
    Schedule a notification for future delivery
    
    Request body:
    {
        "title": "Maintenance Alert",
        "message": "Scheduled maintenance tomorrow",
        "target_audience": "all",
        "scheduled_for": "2024-12-25T10:00:00"
    }
    """
    try:
        admin_id = get_jwt_identity()
        data = request.get_json()
        
        scheduled_for_str = data.get('scheduled_for')
        if not scheduled_for_str:
            return jsonify({"error": "scheduled_for is required"}), 400
        
        scheduled_for = datetime.fromisoformat(scheduled_for_str)
        
        if scheduled_for <= datetime.utcnow():
            return jsonify({"error": "scheduled_for must be in the future"}), 400
        
        scheduled_notification = {
            "title": data.get('title'),
            "message": data.get('message'),
            "target_audience": data.get('target_audience', 'all'),
            "notification_type": data.get('notification_type', 'system_announcement'),
            "scheduled_for": scheduled_for,
            "created_by": admin_id,
            "created_at": datetime.utcnow(),
            "status": "pending"  # pending, sent, cancelled
        }
        
        result = mongo.db.scheduled_notifications.insert_one(scheduled_notification)
        
        return jsonify({
            "message": "Notification scheduled successfully",
            "schedule_id": str(result.inserted_id),
            "scheduled_for": scheduled_for.isoformat()
        }), 201
        
    except Exception as e:
        return jsonify({"error": f"Failed to schedule notification: {str(e)}"}), 500


@admin_notification_bp.route("/schedule", methods=["GET"])
@jwt_required()
@admin_only
def get_scheduled_notifications():
    """Get all scheduled notifications"""
    try:
        scheduled = list(mongo.db.scheduled_notifications.find(
            {"status": "pending"}
        ).sort("scheduled_for", 1))
        
        for item in scheduled:
            item["_id"] = str(item["_id"])
            if item.get("scheduled_for"):
                item["scheduled_for"] = item["scheduled_for"].isoformat()
            if item.get("created_at"):
                item["created_at"] = item["created_at"].isoformat()
        
        return jsonify({"scheduled_notifications": scheduled}), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get scheduled notifications: {str(e)}"}), 500


@admin_notification_bp.route("/schedule/<schedule_id>", methods=["DELETE"])
@jwt_required()
@admin_only
def cancel_scheduled_notification(schedule_id):
    """Cancel a scheduled notification"""
    try:
        if not ObjectId.is_valid(schedule_id):
            return jsonify({"error": "Invalid schedule ID"}), 400
        
        mongo.db.scheduled_notifications.update_one(
            {"_id": ObjectId(schedule_id)},
            {"$set": {"status": "cancelled", "cancelled_at": datetime.utcnow()}}
        )
        
        return jsonify({"message": "Scheduled notification cancelled"}), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to cancel notification: {str(e)}"}), 500


# ============================================================================
# BROADCAST HISTORY
# ============================================================================

@admin_notification_bp.route("/history", methods=["GET"])
@jwt_required()
@admin_only
def get_broadcast_history():
    """Get broadcast and campaign history"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        
        # Get broadcasts
        skip = (page - 1) * per_page
        broadcasts = list(mongo.db.broadcast_logs.find()
                         .sort("sent_at", -1)
                         .skip(skip)
                         .limit(per_page))
        
        # Get campaigns
        campaigns = list(mongo.db.campaign_logs.find()
                        .sort("sent_at", -1)
                        .skip(skip)
                        .limit(per_page))
        
        # Combine and sort
        all_history = broadcasts + campaigns
        all_history.sort(key=lambda x: x.get("sent_at", datetime.min), reverse=True)
        
        # Format
        for item in all_history:
            item["_id"] = str(item["_id"])
            if item.get("sent_at"):
                item["sent_at"] = item["sent_at"].isoformat()
        
        total = mongo.db.broadcast_logs.count_documents({}) + \
                mongo.db.campaign_logs.count_documents({})
        
        return jsonify({
            "history": all_history[:per_page],
            "page": page,
            "per_page": per_page,
            "total": total
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get history: {str(e)}"}), 500


# ============================================================================
# NOTIFICATION STATISTICS
# ============================================================================

@admin_notification_bp.route("/stats", methods=["GET"])
@jwt_required()
@admin_only
def get_notification_stats():
    """Get notification statistics"""
    try:
        # Total notifications sent
        total_notifications = mongo.db.notifications.count_documents({})
        
        # Unread notifications
        unread_notifications = mongo.db.notifications.count_documents({"is_read": False})
        
        # Broadcasts sent
        total_broadcasts = mongo.db.broadcast_logs.count_documents({})
        
        # Campaigns sent
        total_campaigns = mongo.db.campaign_logs.count_documents({})
        
        # Scheduled pending
        scheduled_pending = mongo.db.scheduled_notifications.count_documents({"status": "pending"})
        
        # Notifications by type
        by_type = list(mongo.db.notifications.aggregate([
            {"$group": {
                "_id": "$notification_type",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]))
        
        return jsonify({
            "total_notifications": total_notifications,
            "unread_notifications": unread_notifications,
            "total_broadcasts": total_broadcasts,
            "total_campaigns": total_campaigns,
            "scheduled_pending": scheduled_pending,
            "by_type": by_type
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get stats: {str(e)}"}), 500