# routes/favourite_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from extensions import mongo
from utils.decorators import tenant_only
from bson import ObjectId
from datetime import datetime

favourite_bp = Blueprint("favourite", __name__)

# ---------------------------
# ADD PROPERTY TO FAVOURITES
# ---------------------------
@favourite_bp.route("/", methods=["POST"])
@jwt_required()
@tenant_only
def add_to_favourites():
    """
    Add a property to user's favourites
    Request body: { "property_id": "..." }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        property_id = data.get("property_id")
        
        if not property_id:
            return jsonify({"error": "Property ID is required"}), 400
        
        # Validate property ID
        if not ObjectId.is_valid(property_id):
            return jsonify({"error": "Invalid property ID"}), 400
        
        # Check if property exists
        property_exists = mongo.db.properties.find_one({"_id": ObjectId(property_id)})
        if not property_exists:
            return jsonify({"error": "Property not found"}), 404
        
        # Check if already in favourites
        existing = mongo.db.favourites.find_one({
            "user_id": user_id,
            "property_id": property_id
        })
        
        if existing:
            return jsonify({"error": "Property already in favourites"}), 409
        
        # Add to favourites
        favourite = {
            "user_id": user_id,
            "property_id": property_id,
            "created_at": datetime.utcnow()
        }
        
        result = mongo.db.favourites.insert_one(favourite)
        
        return jsonify({
            "message": "Property added to favourites",
            "favourite_id": str(result.inserted_id)
        }), 201
        
    except Exception as e:
        return jsonify({"error": f"Failed to add to favourites: {str(e)}"}), 500


# ---------------------------
# REMOVE PROPERTY FROM FAVOURITES
# ---------------------------
@favourite_bp.route("/<property_id>", methods=["DELETE"])
@jwt_required()
@tenant_only
def remove_from_favourites(property_id):
    """
    Remove a property from user's favourites
    """
    try:
        user_id = get_jwt_identity()
        
        # Validate property ID
        if not ObjectId.is_valid(property_id):
            return jsonify({"error": "Invalid property ID"}), 400
        
        # Remove from favourites
        result = mongo.db.favourites.delete_one({
            "user_id": user_id,
            "property_id": property_id
        })
        
        if result.deleted_count == 0:
            return jsonify({"error": "Property not in favourites"}), 404
        
        return jsonify({"message": "Property removed from favourites"}), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to remove from favourites: {str(e)}"}), 500


# ---------------------------
# GET ALL USER'S FAVOURITES
# ---------------------------
@favourite_bp.route("/", methods=["GET"])
@jwt_required()
@tenant_only
def get_favourites():
    """
    Get all properties in user's favourites with full property details
    """
    try:
        user_id = get_jwt_identity()
        
        # Pagination
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        skip = (page - 1) * per_page
        
        # Get favourites with property details using aggregation
        pipeline = [
            # Match user's favourites
            {"$match": {"user_id": user_id}},
            
            # Convert property_id string to ObjectId for lookup
            {"$addFields": {
                "property_object_id": {"$toObjectId": "$property_id"}
            }},
            
            # Join with properties collection
            {"$lookup": {
                "from": "properties",
                "localField": "property_object_id",
                "foreignField": "_id",
                "as": "property"
            }},
            
            # Unwind property array
            {"$unwind": "$property"},
            
            # Only include active properties
            {"$match": {"property.status": "active"}},
            
            # Sort by when added to favourites (newest first)
            {"$sort": {"created_at": -1}},
            
            # Pagination
            {"$skip": skip},
            {"$limit": per_page},
            
            # Project final shape
            {"$project": {
                "_id": 1,
                "property_id": 1,
                "created_at": 1,
                "property": 1
            }}
        ]
        
        favourites = list(mongo.db.favourites.aggregate(pipeline))
        
        # Get total count
        total_count = mongo.db.favourites.count_documents({"user_id": user_id})
        
        # Get base URL for images
        base_url = request.host_url.rstrip('/')
        
        # Format response
        result = []
        for fav in favourites:
            property_data = fav["property"]
            
            # Convert ObjectId to string
            property_data["_id"] = str(property_data["_id"])
            property_data["landlord_id"] = str(property_data["landlord_id"])
            property_data["created_at"] = property_data["created_at"].isoformat() if isinstance(property_data["created_at"], datetime) else property_data["created_at"]
            property_data["updated_at"] = property_data["updated_at"].isoformat() if isinstance(property_data["updated_at"], datetime) else property_data["updated_at"]
            
            # Convert image paths to full URLs
            if property_data.get("images"):
                property_data["images"] = [
                    f"{base_url}{img}" if not img.startswith('http') else img
                    for img in property_data["images"]
                ]
            
            # Convert video paths
            if property_data.get("videos"):
                property_data["videos"] = [
                    f"{base_url}{vid}" if not vid.startswith('http') else vid
                    for vid in property_data["videos"]
                ]
            
            result.append({
                "favourite_id": str(fav["_id"]),
                "added_at": fav["created_at"].isoformat() if isinstance(fav["created_at"], datetime) else fav["created_at"],
                "property": property_data
            })
        
        return jsonify({
            "favourites": result,
            "count": len(result),
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "total_pages": (total_count + per_page - 1) // per_page
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get favourites: {str(e)}"}), 500


# ---------------------------
# CHECK IF PROPERTY IS IN FAVOURITES
# ---------------------------
@favourite_bp.route("/check/<property_id>", methods=["GET"])
@jwt_required()
@tenant_only
def check_favourite(property_id):
    """
    Check if a property is in user's favourites
    """
    try:
        user_id = get_jwt_identity()
        
        # Validate property ID
        if not ObjectId.is_valid(property_id):
            return jsonify({"error": "Invalid property ID"}), 400
        
        # Check if in favourites
        favourite = mongo.db.favourites.find_one({
            "user_id": user_id,
            "property_id": property_id
        })
        
        return jsonify({
            "is_favourite": favourite is not None,
            "favourite_id": str(favourite["_id"]) if favourite else None
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to check favourite: {str(e)}"}), 500


# ---------------------------
# GET FAVOURITES COUNT
# ---------------------------
@favourite_bp.route("/count", methods=["GET"])
@jwt_required()
@tenant_only
def get_favourites_count():
    """
    Get total count of user's favourites
    """
    try:
        user_id = get_jwt_identity()
        
        count = mongo.db.favourites.count_documents({"user_id": user_id})
        
        return jsonify({"count": count}), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get favourites count: {str(e)}"}), 500


# ---------------------------
# CLEAR ALL FAVOURITES
# ---------------------------
@favourite_bp.route("/clear", methods=["DELETE"])
@jwt_required()
@tenant_only
def clear_favourites():
    """
    Remove all properties from user's favourites
    """
    try:
        user_id = get_jwt_identity()
        
        result = mongo.db.favourites.delete_many({"user_id": user_id})
        
        return jsonify({
            "message": "All favourites cleared",
            "deleted_count": result.deleted_count
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to clear favourites: {str(e)}"}), 500