from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from extensions import mongo
from models.booking import Booking
from utils.decorators import landlord_only, tenant_only
from utils.validators import validate_booking_data
from bson import ObjectId
from datetime import datetime

booking_bp = Blueprint("booking", __name__)

# ---------------------------
# LANDLORD: GET ALL BOOKINGS FOR MY PROPERTIES
# ---------------------------
@booking_bp.route("/landlord/my-bookings", methods=["GET"])
@jwt_required()
@landlord_only
def get_landlord_bookings():
    """Get all bookings for properties owned by the landlord"""
    try:
        landlord_id = get_jwt_identity()
        
        # Get query parameters for filtering
        status = request.args.get("status")
        property_id = request.args.get("property_id")
        booking_type = request.args.get("booking_type")
        from_date = request.args.get("from_date")
        to_date = request.args.get("to_date")
        
        # Pagination
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        
        # Build query
        query = {"landlord_id": landlord_id}
        
        if status:
            query["status"] = status
        
        if property_id and ObjectId.is_valid(property_id):
            query["property_id"] = property_id
        
        if booking_type:
            query["booking_type"] = booking_type
        
        # Date range filter
        if from_date or to_date:
            query["booking_date"] = {}
            if from_date:
                query["booking_date"]["$gte"] = from_date
            if to_date:
                query["booking_date"]["$lte"] = to_date
        
        # Get total count
        total_count = mongo.db.bookings.count_documents(query)
        
        # Apply pagination and sorting (newest first)
        skip = (page - 1) * per_page
        bookings_cursor = mongo.db.bookings.find(query).sort("created_at", -1).skip(skip).limit(per_page)
        bookings = list(bookings_cursor)
        
        # Enrich bookings with property details
        for booking in bookings:
            # Get property details
            property_data = mongo.db.properties.find_one({"_id": ObjectId(booking["property_id"])})
            if property_data:
                booking["property_details"] = {
                    "title": property_data.get("title"),
                    "address": property_data.get("address"),
                    "city": property_data.get("city"),
                    "price": property_data.get("price"),
                    "images": property_data.get("images", [])[:1]  # First image only
                }
            
            # Convert ObjectIds to strings
            booking["_id"] = str(booking["_id"])
            booking["property_id"] = str(booking["property_id"])
            booking["tenant_id"] = str(booking["tenant_id"])
            booking["landlord_id"] = str(booking["landlord_id"])
            
            # Convert datetime objects to ISO format
            for date_field in ["created_at", "updated_at", "confirmed_at", "completed_at", "cancelled_at"]:
                if booking.get(date_field) and isinstance(booking[date_field], datetime):
                    booking[date_field] = booking[date_field].isoformat()
        
        return jsonify({
            "bookings": bookings,
            "count": len(bookings),
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "total_pages": (total_count + per_page - 1) // per_page
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to fetch bookings: {str(e)}"}), 500


# ---------------------------
# LANDLORD: GET SINGLE BOOKING DETAILS
# ---------------------------
@booking_bp.route("/landlord/<booking_id>", methods=["GET"])
@jwt_required()
@landlord_only
def get_booking_details(booking_id):
    """Get detailed information about a specific booking"""
    try:
        landlord_id = get_jwt_identity()
        
        # Validate booking ID
        if not ObjectId.is_valid(booking_id):
            return jsonify({"error": "Invalid booking ID"}), 400
        
        # Get booking
        booking = mongo.db.bookings.find_one({"_id": ObjectId(booking_id)})
        
        if not booking:
            return jsonify({"error": "Booking not found"}), 404
        
        # Verify landlord owns the property
        if str(booking["landlord_id"]) != landlord_id:
            return jsonify({"error": "Unauthorized access to this booking"}), 403
        
        # Get property details
        property_data = mongo.db.properties.find_one({"_id": ObjectId(booking["property_id"])})
        if property_data:
            booking["property_details"] = {
                "title": property_data.get("title"),
                "description": property_data.get("description"),
                "address": property_data.get("address"),
                "city": property_data.get("city"),
                "state": property_data.get("state"),
                "price": property_data.get("price"),
                "bedrooms": property_data.get("bedrooms"),
                "bathrooms": property_data.get("bathrooms"),
                "images": property_data.get("images", [])
            }
        
        # Get tenant details
        tenant_data = mongo.db.users.find_one({"_id": ObjectId(booking["tenant_id"])})
        if tenant_data:
            booking["tenant_details"] = {
                "email": tenant_data.get("email"),
                "role": tenant_data.get("role")
            }
        
        # Convert ObjectIds to strings
        booking["_id"] = str(booking["_id"])
        booking["property_id"] = str(booking["property_id"])
        booking["tenant_id"] = str(booking["tenant_id"])
        booking["landlord_id"] = str(booking["landlord_id"])
        
        # Convert datetime objects
        for date_field in ["created_at", "updated_at", "confirmed_at", "completed_at", "cancelled_at"]:
            if booking.get(date_field) and isinstance(booking[date_field], datetime):
                booking[date_field] = booking[date_field].isoformat()
        
        return jsonify(booking), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to fetch booking details: {str(e)}"}), 500


# ---------------------------
# LANDLORD: CONFIRM BOOKING
# ---------------------------
@booking_bp.route("/landlord/<booking_id>/confirm", methods=["PUT"])
@jwt_required()
@landlord_only
def confirm_booking(booking_id):
    """Confirm a pending booking"""
    try:
        landlord_id = get_jwt_identity()
        data = request.get_json() or {}
        
        # Validate booking ID
        if not ObjectId.is_valid(booking_id):
            return jsonify({"error": "Invalid booking ID"}), 400
        
        # Get booking
        booking = mongo.db.bookings.find_one({"_id": ObjectId(booking_id)})
        
        if not booking:
            return jsonify({"error": "Booking not found"}), 404
        
        # Verify landlord owns the property
        if str(booking["landlord_id"]) != landlord_id:
            return jsonify({"error": "Unauthorized to confirm this booking"}), 403
        
        # Check if booking is pending
        if booking["status"] != "pending":
            return jsonify({"error": f"Cannot confirm booking with status: {booking['status']}"}), 400
        
        # Update booking status
        update_data = {
            "status": "confirmed",
            "confirmed_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Add optional notes from landlord
        if data.get("notes"):
            update_data["notes"] = data["notes"]
        
        mongo.db.bookings.update_one(
            {"_id": ObjectId(booking_id)},
            {"$set": update_data}
        )
        
        return jsonify({
            "message": "Booking confirmed successfully",
            "booking_id": booking_id,
            "status": "confirmed"
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to confirm booking: {str(e)}"}), 500


# ---------------------------
# LANDLORD: REJECT BOOKING
# ---------------------------
@booking_bp.route("/landlord/<booking_id>/reject", methods=["PUT"])
@jwt_required()
@landlord_only
def reject_booking(booking_id):
    """Reject a pending booking"""
    try:
        landlord_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get("rejection_reason"):
            return jsonify({"error": "Rejection reason is required"}), 400
        
        # Validate booking ID
        if not ObjectId.is_valid(booking_id):
            return jsonify({"error": "Invalid booking ID"}), 400
        
        # Get booking
        booking = mongo.db.bookings.find_one({"_id": ObjectId(booking_id)})
        
        if not booking:
            return jsonify({"error": "Booking not found"}), 404
        
        # Verify landlord owns the property
        if str(booking["landlord_id"]) != landlord_id:
            return jsonify({"error": "Unauthorized to reject this booking"}), 403
        
        # Check if booking is pending
        if booking["status"] != "pending":
            return jsonify({"error": f"Cannot reject booking with status: {booking['status']}"}), 400
        
        # Update booking status
        update_data = {
            "status": "rejected",
            "rejection_reason": data["rejection_reason"],
            "updated_at": datetime.utcnow()
        }
        
        mongo.db.bookings.update_one(
            {"_id": ObjectId(booking_id)},
            {"$set": update_data}
        )
        
        return jsonify({
            "message": "Booking rejected successfully",
            "booking_id": booking_id,
            "status": "rejected"
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to reject booking: {str(e)}"}), 500


# ---------------------------
# LANDLORD: COMPLETE BOOKING
# ---------------------------
@booking_bp.route("/landlord/<booking_id>/complete", methods=["PUT"])
@jwt_required()
@landlord_only
def complete_booking(booking_id):
    """Mark a confirmed booking as completed"""
    try:
        landlord_id = get_jwt_identity()
        data = request.get_json() or {}
        
        # Validate booking ID
        if not ObjectId.is_valid(booking_id):
            return jsonify({"error": "Invalid booking ID"}), 400
        
        # Get booking
        booking = mongo.db.bookings.find_one({"_id": ObjectId(booking_id)})
        
        if not booking:
            return jsonify({"error": "Booking not found"}), 404
        
        # Verify landlord owns the property
        if str(booking["landlord_id"]) != landlord_id:
            return jsonify({"error": "Unauthorized to complete this booking"}), 403
        
        # Check if booking is confirmed
        if booking["status"] != "confirmed":
            return jsonify({"error": f"Can only complete confirmed bookings. Current status: {booking['status']}"}), 400
        
        # Update booking status
        update_data = {
            "status": "completed",
            "completed_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Add optional notes
        if data.get("notes"):
            update_data["notes"] = data["notes"]
        
        mongo.db.bookings.update_one(
            {"_id": ObjectId(booking_id)},
            {"$set": update_data}
        )
        
        return jsonify({
            "message": "Booking marked as completed",
            "booking_id": booking_id,
            "status": "completed"
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to complete booking: {str(e)}"}), 500


# ---------------------------
# LANDLORD: ADD/UPDATE NOTES
# ---------------------------
@booking_bp.route("/landlord/<booking_id>/notes", methods=["PUT"])
@jwt_required()
@landlord_only
def update_booking_notes(booking_id):
    """Add or update internal notes for a booking"""
    try:
        landlord_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or "notes" not in data:
            return jsonify({"error": "Notes field is required"}), 400
        
        # Validate booking ID
        if not ObjectId.is_valid(booking_id):
            return jsonify({"error": "Invalid booking ID"}), 400
        
        # Get booking
        booking = mongo.db.bookings.find_one({"_id": ObjectId(booking_id)})
        
        if not booking:
            return jsonify({"error": "Booking not found"}), 404
        
        # Verify landlord owns the property
        if str(booking["landlord_id"]) != landlord_id:
            return jsonify({"error": "Unauthorized to update notes for this booking"}), 403
        
        # Update notes
        mongo.db.bookings.update_one(
            {"_id": ObjectId(booking_id)},
            {"$set": {
                "notes": data["notes"],
                "updated_at": datetime.utcnow()
            }}
        )
        
        return jsonify({
            "message": "Notes updated successfully",
            "booking_id": booking_id
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to update notes: {str(e)}"}), 500


# ---------------------------
# LANDLORD: GET BOOKING STATISTICS
# ---------------------------
@booking_bp.route("/landlord/statistics", methods=["GET"])
@jwt_required()
@landlord_only
def get_landlord_booking_statistics():
    """Get booking statistics for the landlord's properties"""
    try:
        landlord_id = get_jwt_identity()
        
        # Total bookings by status
        status_pipeline = [
            {"$match": {"landlord_id": landlord_id}},
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }}
        ]
        status_stats = list(mongo.db.bookings.aggregate(status_pipeline))
        
        # Bookings by property
        property_pipeline = [
            {"$match": {"landlord_id": landlord_id}},
            {"$group": {
                "_id": "$property_id",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        property_stats = list(mongo.db.bookings.aggregate(property_pipeline))
        
        # Enrich property stats with property details
        for stat in property_stats:
            property_data = mongo.db.properties.find_one({"_id": ObjectId(stat["_id"])})
            if property_data:
                stat["property_title"] = property_data.get("title")
                stat["property_address"] = property_data.get("address")
            stat["_id"] = str(stat["_id"])
        
        # Recent bookings (last 7 days)
        from datetime import timedelta
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_count = mongo.db.bookings.count_documents({
            "landlord_id": landlord_id,
            "created_at": {"$gte": seven_days_ago}
        })
        
        # Pending bookings count
        pending_count = mongo.db.bookings.count_documents({
            "landlord_id": landlord_id,
            "status": "pending"
        })
        
        return jsonify({
            "status_breakdown": status_stats,
            "top_properties": property_stats,
            "recent_bookings_count": recent_count,
            "pending_bookings_count": pending_count
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to fetch statistics: {str(e)}"}), 500


# ---------------------------
# LANDLORD: GET UPCOMING BOOKINGS
# ---------------------------
@booking_bp.route("/landlord/upcoming", methods=["GET"])
@jwt_required()
@landlord_only
def get_upcoming_bookings():
    """Get confirmed bookings scheduled for future dates"""
    try:
        landlord_id = get_jwt_identity()
        
        # Get today's date
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Query for confirmed bookings with date >= today
        bookings = list(mongo.db.bookings.find({
            "landlord_id": landlord_id,
            "status": "confirmed",
            "booking_date": {"$gte": today}
        }).sort("booking_date", 1).limit(50))
        
        # Enrich with property details
        for booking in bookings:
            property_data = mongo.db.properties.find_one({"_id": ObjectId(booking["property_id"])})
            if property_data:
                booking["property_details"] = {
                    "title": property_data.get("title"),
                    "address": property_data.get("address"),
                    "city": property_data.get("city")
                }
            
            # Convert ObjectIds
            booking["_id"] = str(booking["_id"])
            booking["property_id"] = str(booking["property_id"])
            booking["tenant_id"] = str(booking["tenant_id"])
            booking["landlord_id"] = str(booking["landlord_id"])
            
            # Convert datetime
            for date_field in ["created_at", "updated_at", "confirmed_at"]:
                if booking.get(date_field) and isinstance(booking[date_field], datetime):
                    booking[date_field] = booking[date_field].isoformat()
        
        return jsonify({
            "bookings": bookings,
            "count": len(bookings)
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to fetch upcoming bookings: {str(e)}"}), 500
    
    # ---------------------------
# TENANT: CREATE A NEW BOOKING
# ---------------------------
@booking_bp.route("/tenant/create", methods=["POST"])
@jwt_required()
@tenant_only
def create_booking():
    """Create a new booking request for a property"""
    try:
        tenant_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        is_valid, errors = validate_booking_data(data)
        if not is_valid:
            return jsonify({"error": "Validation failed", "details": errors}), 400
        
        # Validate property exists
        property_id = data.get("property_id")
        if not ObjectId.is_valid(property_id):
            return jsonify({"error": "Invalid property ID"}), 400
        
        property_data = mongo.db.properties.find_one({"_id": ObjectId(property_id)})
        if not property_data:
            return jsonify({"error": "Property not found"}), 404
        
        # Get landlord ID from property
        landlord_id = str(property_data.get("landlord_id"))
        
        # Prevent tenant from booking their own property (if they're also a landlord)
        if tenant_id == landlord_id:
            return jsonify({"error": "You cannot book your own property"}), 400
        
        # Get tenant details
        tenant_data = mongo.db.users.find_one({"_id": tenant_id})
        
        # Create booking object
        booking = Booking(
            property_id=ObjectId(property_id),
            tenant_id=tenant_id,
            landlord_id=landlord_id,
            booking_type=data.get("booking_type"),
            booking_date=data.get("booking_date"),
            booking_time=data.get("booking_time"),
            status="pending",
            tenant_name=data.get("tenant_name"),
            tenant_email=data.get("tenant_email"),
            tenant_phone=data.get("tenant_phone"),
            message=data.get("message"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Insert into database
        result = mongo.db.bookings.insert_one(booking.to_dict())
        
        return jsonify({
            "message": "Booking request created successfully",
            "booking_id": str(result.inserted_id),
            "status": "pending",
            "property_title": property_data.get("title"),
            "booking_date": data.get("booking_date"),
            "booking_time": data.get("booking_time")
        }), 201
        
    except Exception as e:
        return jsonify({"error": f"Failed to create booking: {str(e)}"}), 500


# ---------------------------
# TENANT: GET ALL MY BOOKINGS
# ---------------------------
@booking_bp.route("/tenant/my-bookings", methods=["GET"])
@jwt_required()
@tenant_only
def get_tenant_bookings():
    """Get all bookings created by the tenant"""
    try:
        tenant_id = get_jwt_identity()
        
        # Get query parameters for filtering
        status = request.args.get("status")
        booking_type = request.args.get("booking_type")
        from_date = request.args.get("from_date")
        to_date = request.args.get("to_date")
        
        # Pagination
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        
        # Build query
        query = {"tenant_id": tenant_id}
        
        if status:
            query["status"] = status
        
        if booking_type:
            query["booking_type"] = booking_type
        
        # Date range filter
        if from_date or to_date:
            query["booking_date"] = {}
            if from_date:
                query["booking_date"]["$gte"] = from_date
            if to_date:
                query["booking_date"]["$lte"] = to_date
        
        # Get total count
        total_count = mongo.db.bookings.count_documents(query)
        
        # Apply pagination and sorting (newest first)
        skip = (page - 1) * per_page
        bookings_cursor = mongo.db.bookings.find(query).sort("created_at", -1).skip(skip).limit(per_page)
        bookings = list(bookings_cursor)
        
        # Enrich bookings with property details
        for booking in bookings:
            # Get property details
            property_data = mongo.db.properties.find_one({"_id": ObjectId(booking["property_id"])})
            if property_data:
                booking["property_details"] = {
                    "title": property_data.get("title"),
                    "address": property_data.get("address"),
                    "city": property_data.get("city"),
                    "state": property_data.get("state"),
                    "price": property_data.get("price"),
                    "bedrooms": property_data.get("bedrooms"),
                    "bathrooms": property_data.get("bathrooms"),
                    "images": property_data.get("images", [])[:1]  # First image only
                }
            
            # Get landlord contact info (only for confirmed bookings)
            if booking["status"] == "confirmed":
                landlord_data = mongo.db.users.find_one({"_id": booking["landlord_id"]})
                if landlord_data:
                    booking["landlord_contact"] = {
                        "email": landlord_data.get("email"),
                        "phone": landlord_data.get("phone")
                    }
            
            # Convert ObjectIds to strings
            booking["_id"] = str(booking["_id"])
            booking["property_id"] = str(booking["property_id"])
            booking["tenant_id"] = str(booking["tenant_id"])
            booking["landlord_id"] = str(booking["landlord_id"])
            
            # Convert datetime objects to ISO format
            for date_field in ["created_at", "updated_at", "confirmed_at", "completed_at", "cancelled_at"]:
                if booking.get(date_field) and isinstance(booking[date_field], datetime):
                    booking[date_field] = booking[date_field].isoformat()
        
        return jsonify({
            "bookings": bookings,
            "count": len(bookings),
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "total_pages": (total_count + per_page - 1) // per_page
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to fetch bookings: {str(e)}"}), 500


# ---------------------------
# TENANT: GET SINGLE BOOKING DETAILS
# ---------------------------
@booking_bp.route("/tenant/<booking_id>", methods=["GET"])
@jwt_required()
@tenant_only
def get_tenant_booking_details(booking_id):
    """Get detailed information about a specific booking"""
    try:
        tenant_id = get_jwt_identity()
        
        # Validate booking ID
        if not ObjectId.is_valid(booking_id):
            return jsonify({"error": "Invalid booking ID"}), 400
        
        # Get booking
        booking = mongo.db.bookings.find_one({"_id": ObjectId(booking_id)})
        
        if not booking:
            return jsonify({"error": "Booking not found"}), 404
        
        # Verify tenant owns this booking
        if str(booking["tenant_id"]) != tenant_id:
            return jsonify({"error": "Unauthorized access to this booking"}), 403
        
        # Get property details
        property_data = mongo.db.properties.find_one({"_id": ObjectId(booking["property_id"])})
        if property_data:
            booking["property_details"] = {
                "title": property_data.get("title"),
                "description": property_data.get("description"),
                "address": property_data.get("address"),
                "city": property_data.get("city"),
                "state": property_data.get("state"),
                "price": property_data.get("price"),
                "property_type": property_data.get("property_type"),
                "bedrooms": property_data.get("bedrooms"),
                "bathrooms": property_data.get("bathrooms"),
                "area": property_data.get("area"),
                "images": property_data.get("images", [])
            }
        
        # Get landlord contact info (only for confirmed bookings)
        if booking["status"] == "confirmed":
            landlord_data = mongo.db.users.find_one({"_id": booking["landlord_id"]})
            if landlord_data:
                booking["landlord_contact"] = {
                    "name": landlord_data.get("name"),
                    "email": landlord_data.get("email"),
                    "phone": landlord_data.get("phone")
                }
        
        # Convert ObjectIds to strings
        booking["_id"] = str(booking["_id"])
        booking["property_id"] = str(booking["property_id"])
        booking["tenant_id"] = str(booking["tenant_id"])
        booking["landlord_id"] = str(booking["landlord_id"])
        
        # Convert datetime objects
        for date_field in ["created_at", "updated_at", "confirmed_at", "completed_at", "cancelled_at"]:
            if booking.get(date_field) and isinstance(booking[date_field], datetime):
                booking[date_field] = booking[date_field].isoformat()
        
        return jsonify(booking), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to fetch booking details: {str(e)}"}), 500


# ---------------------------
# TENANT: CANCEL A BOOKING
# ---------------------------
@booking_bp.route("/tenant/<booking_id>/cancel", methods=["PUT"])
@jwt_required()
@tenant_only
def cancel_tenant_booking(booking_id):
    """Cancel a booking (tenant can only cancel pending or confirmed bookings)"""
    try:
        tenant_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get("cancellation_reason"):
            return jsonify({"error": "Cancellation reason is required"}), 400
        
        # Validate booking ID
        if not ObjectId.is_valid(booking_id):
            return jsonify({"error": "Invalid booking ID"}), 400
        
        # Get booking
        booking = mongo.db.bookings.find_one({"_id": ObjectId(booking_id)})
        
        if not booking:
            return jsonify({"error": "Booking not found"}), 404
        
        # Verify tenant owns this booking
        if str(booking["tenant_id"]) != tenant_id:
            return jsonify({"error": "Unauthorized to cancel this booking"}), 403
        
        # Check if booking can be cancelled
        if booking["status"] not in ["pending", "confirmed"]:
            return jsonify({
                "error": f"Cannot cancel booking with status: {booking['status']}"
            }), 400
        
        # Update booking status
        update_data = {
            "status": "cancelled",
            "cancellation_reason": data["cancellation_reason"],
            "cancelled_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        mongo.db.bookings.update_one(
            {"_id": ObjectId(booking_id)},
            {"$set": update_data}
        )
        
        return jsonify({
            "message": "Booking cancelled successfully",
            "booking_id": booking_id,
            "status": "cancelled"
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to cancel booking: {str(e)}"}), 500


# ---------------------------
# TENANT: UPDATE BOOKING (Only pending bookings)
# ---------------------------
@booking_bp.route("/tenant/<booking_id>/update", methods=["PUT"])
@jwt_required()
@tenant_only
def update_tenant_booking(booking_id):
    """Update booking details (only for pending bookings)"""
    try:
        tenant_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate booking ID
        if not ObjectId.is_valid(booking_id):
            return jsonify({"error": "Invalid booking ID"}), 400
        
        # Get booking
        booking = mongo.db.bookings.find_one({"_id": ObjectId(booking_id)})
        
        if not booking:
            return jsonify({"error": "Booking not found"}), 404
        
        # Verify tenant owns this booking
        if str(booking["tenant_id"]) != tenant_id:
            return jsonify({"error": "Unauthorized to update this booking"}), 403
        
        # Can only update pending bookings
        if booking["status"] != "pending":
            return jsonify({
                "error": f"Cannot update booking with status: {booking['status']}"
            }), 400
        
        # Validate update data
        is_valid, errors = validate_booking_data(data, is_update=True)
        if not is_valid:
            return jsonify({"error": "Validation failed", "details": errors}), 400
        
        # Build update document
        update_data = {
            "updated_at": datetime.utcnow()
        }
        
        # Update allowed fields
        allowed_fields = [
            "booking_date", "booking_time", "booking_type",
            "tenant_name", "tenant_email", "tenant_phone", "message"
        ]
        
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        # Update booking
        mongo.db.bookings.update_one(
            {"_id": ObjectId(booking_id)},
            {"$set": update_data}
        )
        
        return jsonify({
            "message": "Booking updated successfully",
            "booking_id": booking_id
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to update booking: {str(e)}"}), 500


# ---------------------------
# TENANT: GET BOOKING STATISTICS
# ---------------------------
@booking_bp.route("/tenant/statistics", methods=["GET"])
@jwt_required()
@tenant_only
def get_tenant_booking_statistics():
    """Get booking statistics for the tenant"""
    try:
        tenant_id = get_jwt_identity()
        
        # Total bookings by status
        status_pipeline = [
            {"$match": {"tenant_id": tenant_id}},
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }}
        ]
        status_stats = list(mongo.db.bookings.aggregate(status_pipeline))
        
        # Bookings by type
        type_pipeline = [
            {"$match": {"tenant_id": tenant_id}},
            {"$group": {
                "_id": "$booking_type",
                "count": {"$sum": 1}
            }}
        ]
        type_stats = list(mongo.db.bookings.aggregate(type_pipeline))
        
        # Recent bookings (last 30 days)
        from datetime import timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_count = mongo.db.bookings.count_documents({
            "tenant_id": tenant_id,
            "created_at": {"$gte": thirty_days_ago}
        })
        
        # Upcoming confirmed bookings count
        today = datetime.now().strftime("%Y-%m-%d")
        upcoming_count = mongo.db.bookings.count_documents({
            "tenant_id": tenant_id,
            "status": "confirmed",
            "booking_date": {"$gte": today}
        })
        
        return jsonify({
            "status_breakdown": status_stats,
            "booking_type_breakdown": type_stats,
            "recent_bookings_count": recent_count,
            "upcoming_bookings_count": upcoming_count
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to fetch statistics: {str(e)}"}), 500


# ---------------------------
# TENANT: GET UPCOMING BOOKINGS
# ---------------------------
@booking_bp.route("/tenant/upcoming", methods=["GET"])
@jwt_required()
@tenant_only
def get_tenant_upcoming_bookings():
    """Get confirmed bookings scheduled for future dates"""
    try:
        tenant_id = get_jwt_identity()
        
        # Get today's date
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Query for confirmed bookings with date >= today
        bookings = list(mongo.db.bookings.find({
            "tenant_id": tenant_id,
            "status": "confirmed",
            "booking_date": {"$gte": today}
        }).sort("booking_date", 1).limit(50))
        
        # Enrich with property and landlord details
        for booking in bookings:
            # Property details
            property_data = mongo.db.properties.find_one({"_id": ObjectId(booking["property_id"])})
            if property_data:
                booking["property_details"] = {
                    "title": property_data.get("title"),
                    "address": property_data.get("address"),
                    "city": property_data.get("city"),
                    "images": property_data.get("images", [])[:1]
                }
            
            # Landlord contact
            landlord_data = mongo.db.users.find_one({"_id": booking["landlord_id"]})
            if landlord_data:
                booking["landlord_contact"] = {
                    "name": landlord_data.get("name"),
                    "email": landlord_data.get("email"),
                    "phone": landlord_data.get("phone")
                }
            
            # Convert ObjectIds
            booking["_id"] = str(booking["_id"])
            booking["property_id"] = str(booking["property_id"])
            booking["tenant_id"] = str(booking["tenant_id"])
            booking["landlord_id"] = str(booking["landlord_id"])
            
            # Convert datetime
            for date_field in ["created_at", "updated_at", "confirmed_at"]:
                if booking.get(date_field) and isinstance(booking[date_field], datetime):
                    booking[date_field] = booking[date_field].isoformat()
        
        return jsonify({
            "bookings": bookings,
            "count": len(bookings)
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to fetch upcoming bookings: {str(e)}"}), 500