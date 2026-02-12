"""
routes/listing_confirmation_routes.py
──────────────────────────────────────
Landlord-facing endpoints for Requirement 6.

  POST  /listing-confirmation/<property_id>/confirm   → confirm a listing
  GET   /listing-confirmation/<property_id>/status    → days left, pending flag
  GET   /listing-confirmation/pending                 → all properties needing action
  GET   /listing-confirmation/logs                    → audit trail (admin)

Registered in app.py under url_prefix="/listing-confirmation".
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import mongo
from bson import ObjectId
from datetime import datetime
from services.listing_scheduler import confirm_listing, REMINDER_DAYS, AUTO_DEACTIVATE_DAYS
from utils.decorators import admin_only

listing_confirmation_bp = Blueprint("listing_confirmation", __name__)


# ──────────────────────────────────────────────────────────
# POST  /confirm  — landlord confirms one of their listings
# ──────────────────────────────────────────────────────────
@listing_confirmation_bp.route("/<property_id>/confirm", methods=["POST"])
@jwt_required()
def confirm_property(property_id: str):
    """
    Reset the 30-day confirmation clock for a property.
    Only the owning landlord (or an admin) may call this.
    """
    try:
        if not ObjectId.is_valid(property_id):
            return jsonify({"error": "Invalid property ID"}), 400

        current_user_id = get_jwt_identity()

        # ── ownership guard ─────────────────────────────────────────
        property_doc = mongo.db.properties.find_one(
            {"_id": ObjectId(property_id)},
            {"landlord_id": 1, "title": 1, "status": 1}
        )
        if not property_doc:
            return jsonify({"error": "Property not found"}), 404

        # Allow the landlord who owns it OR any admin
        from flask_jwt_extended import get_jwt
        claims = get_jwt()
        is_admin = claims.get("role") == "admin"

        if str(property_doc["landlord_id"]) != current_user_id and not is_admin:
            return jsonify({"error": "You can only confirm your own properties"}), 403

        # ── do the confirmation ─────────────────────────────────────
        success = confirm_listing(property_id)
        if not success:
            return jsonify({"error": "Property not found"}), 404

        return jsonify({
            "message":      "Property confirmed successfully",
            "property_id":  property_id,
            "confirmed_at": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to confirm property: {str(e)}"}), 500


# ──────────────────────────────────────────────────────────
# GET   /status  — confirmation status of one property
# ──────────────────────────────────────────────────────────
@listing_confirmation_bp.route("/<property_id>/status", methods=["GET"])
@jwt_required()
def get_confirmation_status(property_id: str):
    """
    Returns how many days remain before the next confirmation is due,
    whether the listing is in a pending state, and when it was last confirmed.
    Useful for showing badges / countdowns on property cards.
    """
    try:
        if not ObjectId.is_valid(property_id):
            return jsonify({"error": "Invalid property ID"}), 400

        prop = mongo.db.properties.find_one(
            {"_id": ObjectId(property_id)},
            {"landlord_id": 1, "last_confirmed": 1, "created_at": 1,
             "confirmation_pending": 1, "status": 1}
        )
        if not prop:
            return jsonify({"error": "Property not found"}), 404

        # ── ownership guard ─────────────────────────────────────────
        current_user_id = get_jwt_identity()
        from flask_jwt_extended import get_jwt
        claims = get_jwt()
        is_admin = claims.get("role") == "admin"

        if str(prop["landlord_id"]) != current_user_id and not is_admin:
            return jsonify({"error": "Access denied"}), 403

        # ── calculate days ──────────────────────────────────────────
        last_confirmed = prop.get("last_confirmed") or prop.get("created_at")
        days_elapsed   = (datetime.utcnow() - last_confirmed).days if last_confirmed else 0
        days_remaining = max(0, REMINDER_DAYS - days_elapsed)

        return jsonify({
            "property_id":         property_id,
            "status":              prop.get("status", "active"),
            "last_confirmed":      last_confirmed.isoformat() if last_confirmed else None,
            "days_since_confirmed": days_elapsed,
            "days_until_reminder": days_remaining,
            "confirmation_pending": prop.get("confirmation_pending", False),
            "will_deactivate_in":  max(0, AUTO_DEACTIVATE_DAYS - days_elapsed)
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to get status: {str(e)}"}), 500


# ──────────────────────────────────────────────────────────
# GET   /pending  — all properties belonging to the current
#                   landlord that need confirmation
# ──────────────────────────────────────────────────────────
@listing_confirmation_bp.route("/pending", methods=["GET"])
@jwt_required()
def get_pending_properties():
    """
    Returns active properties where confirmation_pending is True
    for the authenticated landlord.
    """
    try:
        current_user_id = get_jwt_identity()

        pending = list(mongo.db.properties.find({
            "landlord_id":            current_user_id,
            "status":                 "active",
            "confirmation_pending":   True
        }, {
            "_id": 1, "title": 1, "city": 1, "state": 1,
            "last_confirmed": 1, "images": 1
        }))

        # Stringify ObjectIds and format dates
        for p in pending:
            p["_id"] = str(p["_id"])
            if p.get("last_confirmed"):
                days = (datetime.utcnow() - p["last_confirmed"]).days
                p["days_since_confirmed"] = days
                p["last_confirmed"]       = p["last_confirmed"].isoformat()

        return jsonify({
            "pending_properties": pending,
            "count":              len(pending)
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch pending properties: {str(e)}"}), 500


# ──────────────────────────────────────────────────────────
# GET   /logs  — audit trail (admin only)
# ──────────────────────────────────────────────────────────
@listing_confirmation_bp.route("/logs", methods=["GET"])
@jwt_required()
@admin_only
def get_confirmation_logs():
    """
    Paginated audit log of every confirmation action the scheduler
    (or landlord) has taken.  Admin only.
    """
    try:
        page     = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        action   = request.args.get("action")          # filter by action type

        query = {}
        if action:
            query["action"] = action

        total = mongo.db.listing_confirmation_logs.count_documents(query)
        skip  = (page - 1) * per_page

        logs = list(
            mongo.db.listing_confirmation_logs
            .find(query)
            .sort("timestamp", -1)
            .skip(skip)
            .limit(per_page)
        )

        for log in logs:
            log["_id"]       = str(log["_id"])
            log["timestamp"] = log["timestamp"].isoformat() if log.get("timestamp") else None

        return jsonify({
            "logs":        logs,
            "total":       total,
            "page":        page,
            "per_page":    per_page,
            "total_pages": (total + per_page - 1) // per_page
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch logs: {str(e)}"}), 500