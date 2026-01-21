# backend/routes/subscription_routes.py
"""
Subscription Routes - Landlord Subscription Management
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import mongo
from bson import ObjectId
from datetime import datetime, timedelta
from utils.decorators import landlord_only

subscription_bp = Blueprint("subscription", __name__)

# ============================================================================
# SUBSCRIPTION TIERS CONFIGURATION
# ============================================================================

SUBSCRIPTION_TIERS = {
    "free": {
        "name": "Free Plan",
        "price": 0,
        "currency": "KES",
        "max_properties": 2,
        "max_photos": 5,
        "max_videos": 0,
        "commission_rate": 10,  # 10%
        "listing_duration_days": 30,
        "featured_placement": False,
        "priority_search": False,
        "analytics": False,
        "support_level": "community",
        "api_access": False
    },
    "basic": {
        "name": "Basic Plan",
        "price": 2900,
        "currency": "KES",
        "billing_cycle": "monthly",
        "max_properties": 10,
        "max_photos": 999,  # Unlimited
        "max_videos": 1,
        "commission_rate": 5,  # 5%
        "listing_duration_days": 60,
        "featured_placement": False,
        "priority_search": True,
        "analytics": True,
        "support_level": "email",
        "api_access": False
    },
    "premium": {
        "name": "Premium Plan",
        "price": 10000,
        "currency": "KES",
        "billing_cycle": "monthly",
        "max_properties": 999,  # Unlimited
        "max_photos": 999,  # Unlimited
        "max_videos": 999,  # Unlimited
        "commission_rate": 2,  # 2%
        "listing_duration_days": 90,
        "featured_placement": True,
        "priority_search": True,
        "analytics": True,
        "support_level": "24/7",
        "api_access": True,
        "dedicated_manager": True
    }
}


# ============================================================================
# GET SUBSCRIPTION PLANS
# ============================================================================

@subscription_bp.route("/plans", methods=["GET"])
def get_subscription_plans():
    """Get all available subscription plans"""
    try:
        plans = []
        for tier_id, tier_data in SUBSCRIPTION_TIERS.items():
            plans.append({
                "id": tier_id,
                **tier_data
            })
        
        return jsonify({"plans": plans}), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get plans: {str(e)}"}), 500


# ============================================================================
# GET CURRENT SUBSCRIPTION
# ============================================================================

@subscription_bp.route("/current", methods=["GET"])
@jwt_required()
@landlord_only
def get_current_subscription():
    """Get landlord's current subscription"""
    try:
        landlord_id = get_jwt_identity()
        
        # Get user subscription data
        user = mongo.db.users.find_one({"_id": ObjectId(landlord_id)})
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Default to free plan if no subscription
        subscription = user.get("subscription", {
            "tier": "free",
            "status": "active",
            "started_at": datetime.utcnow()
        })
        
        # Get tier details
        tier_id = subscription.get("tier", "free")
        tier_details = SUBSCRIPTION_TIERS.get(tier_id, SUBSCRIPTION_TIERS["free"])
        
        # Get usage statistics
        property_count = mongo.db.properties.count_documents({"landlord_id": landlord_id})
        
        # Calculate commission earned (if applicable)
        # Commission is calculated from confirmed bookings
        commission_pipeline = [
            {
                "$match": {
                    "landlord_id": landlord_id,
                    "status": "confirmed"
                }
            },
            {
                "$lookup": {
                    "from": "properties",
                    "localField": "property_id",
                    "foreignField": "_id",
                    "as": "property"
                }
            },
            {"$unwind": "$property"},
            {
                "$group": {
                    "_id": None,
                    "total_bookings": {"$sum": 1}
                }
            }
        ]
        
        commission_result = list(mongo.db.bookings.aggregate(commission_pipeline))
        total_bookings = commission_result[0]["total_bookings"] if commission_result else 0
        
        response = {
            "subscription": {
                "tier": tier_id,
                "status": subscription.get("status", "active"),
                "started_at": subscription.get("started_at").isoformat() if subscription.get("started_at") else None,
                "expires_at": subscription.get("expires_at").isoformat() if subscription.get("expires_at") else None,
                "auto_renew": subscription.get("auto_renew", False),
                **tier_details
            },
            "usage": {
                "properties_count": property_count,
                "properties_limit": tier_details["max_properties"],
                "total_bookings": total_bookings
            },
            "can_upgrade": tier_id in ["free", "basic"]
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get subscription: {str(e)}"}), 500


# ============================================================================
# SUBSCRIBE TO PLAN
# ============================================================================

@subscription_bp.route("/subscribe", methods=["POST"])
@jwt_required()
@landlord_only
def subscribe_to_plan():
    """Subscribe to a plan"""
    try:
        landlord_id = get_jwt_identity()
        data = request.get_json()
        
        tier_id = data.get("tier")
        billing_cycle = data.get("billing_cycle", "monthly")
        
        if not tier_id or tier_id not in SUBSCRIPTION_TIERS:
            return jsonify({"error": "Invalid subscription tier"}), 400
        
        tier_details = SUBSCRIPTION_TIERS[tier_id]
        
        # Free plan doesn't require payment
        if tier_id == "free":
            return jsonify({"error": "Already on free plan"}), 400
        
        # Calculate subscription period
        start_date = datetime.utcnow()
        if billing_cycle == "monthly":
            end_date = start_date + timedelta(days=30)
        elif billing_cycle == "annual":
            end_date = start_date + timedelta(days=365)
        else:
            return jsonify({"error": "Invalid billing cycle"}), 400
        
        # Create subscription record
        subscription = {
            "tier": tier_id,
            "status": "pending_payment",
            "billing_cycle": billing_cycle,
            "started_at": start_date,
            "expires_at": end_date,
            "auto_renew": data.get("auto_renew", False),
            "price": tier_details["price"],
            "currency": tier_details["currency"]
        }
        
        # Create payment record
        payment = {
            "landlord_id": landlord_id,
            "type": "subscription",
            "tier": tier_id,
            "amount": tier_details["price"],
            "currency": tier_details["currency"],
            "billing_cycle": billing_cycle,
            "status": "pending",
            "created_at": datetime.utcnow(),
            "subscription_period": {
                "start": start_date,
                "end": end_date
            }
        }
        
        payment_result = mongo.db.payments.insert_one(payment)
        payment_id = str(payment_result.inserted_id)
        
        print(f"✅ Subscription initiated: {tier_id} for {landlord_id}")
        
        return jsonify({
            "message": "Subscription initiated. Please complete payment.",
            "payment_id": payment_id,
            "subscription": subscription,
            "payment_amount": tier_details["price"]
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to subscribe: {str(e)}"}), 500


# ============================================================================
# CONFIRM SUBSCRIPTION PAYMENT
# ============================================================================

@subscription_bp.route("/confirm-payment/<payment_id>", methods=["POST"])
@jwt_required()
@landlord_only
def confirm_subscription_payment(payment_id):
    """Confirm subscription payment and activate subscription"""
    try:
        landlord_id = get_jwt_identity()
        
        if not ObjectId.is_valid(payment_id):
            return jsonify({"error": "Invalid payment ID"}), 400
        
        # Get payment
        payment = mongo.db.payments.find_one({
            "_id": ObjectId(payment_id),
            "landlord_id": landlord_id,
            "type": "subscription"
        })
        
        if not payment:
            return jsonify({"error": "Payment not found"}), 404
        
        if payment["status"] != "pending":
            return jsonify({"error": "Payment already processed"}), 400
        
        # Update payment status
        mongo.db.payments.update_one(
            {"_id": ObjectId(payment_id)},
            {"$set": {
                "status": "completed",
                "completed_at": datetime.utcnow()
            }}
        )
        
        # Activate subscription
        subscription = {
            "tier": payment["tier"],
            "status": "active",
            "billing_cycle": payment["billing_cycle"],
            "started_at": payment["subscription_period"]["start"],
            "expires_at": payment["subscription_period"]["end"],
            "auto_renew": True,
            "last_payment_id": payment_id,
            "last_payment_date": datetime.utcnow()
        }
        
        mongo.db.users.update_one(
            {"_id": ObjectId(landlord_id)},
            {"$set": {"subscription": subscription}}
        )
        
        print(f"✅ Subscription activated: {payment['tier']} for {landlord_id}")
        
        return jsonify({
            "message": "Subscription activated successfully",
            "subscription": subscription
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to confirm payment: {str(e)}"}), 500


# ============================================================================
# CANCEL SUBSCRIPTION
# ============================================================================

@subscription_bp.route("/cancel", methods=["POST"])
@jwt_required()
@landlord_only
def cancel_subscription():
    """Cancel subscription (downgrade to free at end of period)"""
    try:
        landlord_id = get_jwt_identity()
        
        user = mongo.db.users.find_one({"_id": ObjectId(landlord_id)})
        
        if not user or not user.get("subscription"):
            return jsonify({"error": "No active subscription"}), 404
        
        subscription = user["subscription"]
        
        if subscription["tier"] == "free":
            return jsonify({"error": "Already on free plan"}), 400
        
        # Set to cancel at end of period
        mongo.db.users.update_one(
            {"_id": ObjectId(landlord_id)},
            {"$set": {
                "subscription.auto_renew": False,
                "subscription.cancel_at_period_end": True,
                "subscription.cancelled_at": datetime.utcnow()
            }}
        )
        
        print(f"✅ Subscription cancelled: {landlord_id}")
        
        return jsonify({
            "message": "Subscription will be cancelled at end of billing period",
            "expires_at": subscription.get("expires_at").isoformat() if subscription.get("expires_at") else None
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to cancel subscription: {str(e)}"}), 500


# ============================================================================
# UPGRADE SUBSCRIPTION
# ============================================================================

@subscription_bp.route("/upgrade", methods=["POST"])
@jwt_required()
@landlord_only
def upgrade_subscription():
    """Upgrade to a higher tier"""
    try:
        landlord_id = get_jwt_identity()
        data = request.get_json()
        
        new_tier = data.get("tier")
        
        if not new_tier or new_tier not in SUBSCRIPTION_TIERS:
            return jsonify({"error": "Invalid subscription tier"}), 400
        
        user = mongo.db.users.find_one({"_id": ObjectId(landlord_id)})
        current_subscription = user.get("subscription", {"tier": "free"})
        current_tier = current_subscription.get("tier", "free")
        
        # Validate upgrade path
        tier_order = ["free", "basic", "premium"]
        if tier_order.index(new_tier) <= tier_order.index(current_tier):
            return jsonify({"error": "Can only upgrade to higher tier"}), 400
        
        # Calculate prorated amount if upgrading mid-cycle
        new_tier_details = SUBSCRIPTION_TIERS[new_tier]
        
        # For simplicity, charge full amount for upgrade
        # In production, implement prorated pricing
        
        return jsonify({
            "message": "Upgrade available",
            "current_tier": current_tier,
            "new_tier": new_tier,
            "price": new_tier_details["price"],
            "requires_payment": True
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to upgrade: {str(e)}"}), 500


# ============================================================================
# GET SUBSCRIPTION HISTORY
# ============================================================================

@subscription_bp.route("/history", methods=["GET"])
@jwt_required()
@landlord_only
def get_subscription_history():
    """Get subscription payment history"""
    try:
        landlord_id = get_jwt_identity()
        
        # Get all subscription payments
        payments = list(mongo.db.payments.find({
            "landlord_id": landlord_id,
            "type": "subscription"
        }).sort("created_at", -1))
        
        for payment in payments:
            payment["_id"] = str(payment["_id"])
            if payment.get("created_at"):
                payment["created_at"] = payment["created_at"].isoformat()
            if payment.get("completed_at"):
                payment["completed_at"] = payment["completed_at"].isoformat()
        
        return jsonify({"payments": payments}), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get history: {str(e)}"}), 500