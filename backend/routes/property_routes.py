from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from extensions import mongo
from models.property import Property
from utils.decorators import landlord_only
from utils.validators import validate_property_data
from bson import ObjectId
from datetime import datetime
import os

property_bp = Blueprint("property", __name__)

# ---------------------------
# CREATE PROPERTY
# ---------------------------
@property_bp.route("/", methods=["POST"])
@jwt_required()
@landlord_only
def create_property():
    try:
        # ✅ FIXED: Get user ID from identity (string)
        user_id = get_jwt_identity()  # Returns string user ID
        claims = get_jwt()  # Get additional claims if needed
        
        data = request.get_json()
        
        # Validate property data
        is_valid, errors = validate_property_data(data)
        if not is_valid:
            return jsonify({"error": errors}), 400
        
        # Create property object
        property_obj = Property(
            landlord_id=user_id,  # ✅ Use user_id directly (it's already a string)
            title=data.get("title"),
            description=data.get("description"),
            property_type=data.get("property_type"),
            address=data.get("address"),
            city=data.get("city"),
            state=data.get("state"),
            zip_code=data.get("zip_code"),
            country=data.get("country"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            price=data.get("price"),
            bedrooms=data.get("bedrooms"),
            bathrooms=data.get("bathrooms"),
            area_sqft=data.get("area_sqft"),
            images=data.get("images", []),
            videos=data.get("videos", []),
            amenities=data.get("amenities", []),
            is_featured=data.get("is_featured", False)
        )
        
        # Insert into database
        result = mongo.db.properties.insert_one(property_obj.to_dict())
        
        return jsonify({
            "message": "Property created successfully",
            "property_id": str(result.inserted_id)
        }), 201
        
    except Exception as e:
        return jsonify({"error": f"Failed to create property: {str(e)}"}), 500

# ---------------------------
# GET ALL PROPERTIES (PUBLIC)
# ---------------------------
@property_bp.route("/", methods=["GET"])
def get_all_properties():
    try:
        # Get query parameters for filtering
        city = request.args.get("city")
        min_price = request.args.get("min_price", type=float)
        max_price = request.args.get("max_price", type=float)
        bedrooms = request.args.get("bedrooms", type=int)
        property_type = request.args.get("property_type")
        status = request.args.get("status", "active")
        
        # Build query
        query = {"status": status}
        
        if city:
            query["city"] = {"$regex": city, "$options": "i"}
        
        if min_price is not None or max_price is not None:
            query["price"] = {}
            if min_price is not None:
                query["price"]["$gte"] = min_price
            if max_price is not None:
                query["price"]["$lte"] = max_price
        
        if bedrooms is not None:
            query["bedrooms"] = bedrooms
        
        if property_type:
            query["property_type"] = property_type
        
        # Get properties
        properties = list(mongo.db.properties.find(query))
        
        # Convert ObjectId to string
        for prop in properties:
            prop["_id"] = str(prop["_id"])
            prop["landlord_id"] = str(prop["landlord_id"])
            prop["created_at"] = prop["created_at"].isoformat() if isinstance(prop["created_at"], datetime) else prop["created_at"]
            prop["updated_at"] = prop["updated_at"].isoformat() if isinstance(prop["updated_at"], datetime) else prop["updated_at"]
        
        return jsonify({
            "properties": properties,
            "count": len(properties)
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to fetch properties: {str(e)}"}), 500

# ---------------------------
# GET SINGLE PROPERTY
# ---------------------------
@property_bp.route("/<property_id>", methods=["GET"])
def get_property(property_id):
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(property_id):
            return jsonify({"error": "Invalid property ID"}), 400
        
        # Get property
        property_data = mongo.db.properties.find_one({"_id": ObjectId(property_id)})
        
        if not property_data:
            return jsonify({"error": "Property not found"}), 404
        
        # Increment views
        mongo.db.properties.update_one(
            {"_id": ObjectId(property_id)},
            {"$inc": {"views": 1}}
        )
        
        # Convert ObjectId to string
        property_data["_id"] = str(property_data["_id"])
        property_data["landlord_id"] = str(property_data["landlord_id"])
        property_data["created_at"] = property_data["created_at"].isoformat() if isinstance(property_data["created_at"], datetime) else property_data["created_at"]
        property_data["updated_at"] = property_data["updated_at"].isoformat() if isinstance(property_data["updated_at"], datetime) else property_data["updated_at"]
        
        return jsonify(property_data), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to fetch property: {str(e)}"}), 500

# ---------------------------
# GET LANDLORD'S PROPERTIES
# ---------------------------
@property_bp.route("/landlord/my-properties", methods=["GET"])
@jwt_required()
@landlord_only
def get_my_properties():
    try:
        # ✅ FIXED: Get user ID directly (it's a string)
        user_id = get_jwt_identity()
        
        # Get properties
        properties = list(mongo.db.properties.find({"landlord_id": user_id}))
        
        # Convert ObjectId to string
        for prop in properties:
            prop["_id"] = str(prop["_id"])
            prop["landlord_id"] = str(prop["landlord_id"])
            prop["created_at"] = prop["created_at"].isoformat() if isinstance(prop["created_at"], datetime) else prop["created_at"]
            prop["updated_at"] = prop["updated_at"].isoformat() if isinstance(prop["updated_at"], datetime) else prop["updated_at"]
        
        return jsonify({
            "properties": properties,
            "count": len(properties)
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to fetch properties: {str(e)}"}), 500

# ---------------------------
# UPDATE PROPERTY
# ---------------------------
@property_bp.route("/<property_id>", methods=["PUT"])
@jwt_required()
@landlord_only
def update_property(property_id):
    try:
        # ✅ FIXED: Get user ID directly (it's a string)
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate ObjectId
        if not ObjectId.is_valid(property_id):
            return jsonify({"error": "Invalid property ID"}), 400
        
        # Check if property exists and belongs to landlord
        property_data = mongo.db.properties.find_one({"_id": ObjectId(property_id)})
        
        if not property_data:
            return jsonify({"error": "Property not found"}), 404
        
        # ✅ FIXED: Compare string to string
        if str(property_data["landlord_id"]) != user_id:
            return jsonify({"error": "Unauthorized to update this property"}), 403
        
        # Validate updated data
        is_valid, errors = validate_property_data(data, is_update=True)
        if not is_valid:
            return jsonify({"error": errors}), 400
        
        # Prepare update data
        update_data = {
            "updated_at": datetime.utcnow()
        }
        
        # Only update fields that are provided
        allowed_fields = [
            "title", "description", "property_type", "address", "city",
            "state", "zip_code", "country", "latitude", "longitude",
            "price", "bedrooms", "bathrooms", "area_sqft", "images",
            "videos", "amenities", "status", "is_featured"
        ]
        
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        # Update property
        mongo.db.properties.update_one(
            {"_id": ObjectId(property_id)},
            {"$set": update_data}
        )
        
        return jsonify({"message": "Property updated successfully"}), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to update property: {str(e)}"}), 500

# ---------------------------
# DELETE PROPERTY
# ---------------------------
@property_bp.route("/<property_id>", methods=["DELETE"])
@jwt_required()
@landlord_only
def delete_property(property_id):
    try:
        # ✅ FIXED: Get user ID directly (it's a string)
        user_id = get_jwt_identity()
        
        # Validate ObjectId
        if not ObjectId.is_valid(property_id):
            return jsonify({"error": "Invalid property ID"}), 400
        
        # Check if property exists and belongs to landlord
        property_data = mongo.db.properties.find_one({"_id": ObjectId(property_id)})
        
        if not property_data:
            return jsonify({"error": "Property not found"}), 404
        
        # ✅ FIXED: Compare string to string
        if str(property_data["landlord_id"]) != user_id:
            return jsonify({"error": "Unauthorized to delete this property"}), 403
        
        # Delete property
        mongo.db.properties.delete_one({"_id": ObjectId(property_id)})
        
        return jsonify({"message": "Property deleted successfully"}), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to delete property: {str(e)}"}), 500

# ---------------------------
# CONFIRM PROPERTY LISTING (30-day renewal)
# ---------------------------
@property_bp.route("/<property_id>/confirm", methods=["POST"])
@jwt_required()
@landlord_only
def confirm_property(property_id):
    try:
        # ✅ FIXED: Get user ID directly (it's a string)
        user_id = get_jwt_identity()
        
        # Validate ObjectId
        if not ObjectId.is_valid(property_id):
            return jsonify({"error": "Invalid property ID"}), 400
        
        # Check if property exists and belongs to landlord
        property_data = mongo.db.properties.find_one({"_id": ObjectId(property_id)})
        
        if not property_data:
            return jsonify({"error": "Property not found"}), 404
        
        # ✅ FIXED: Compare string to string
        if str(property_data["landlord_id"]) != user_id:
            return jsonify({"error": "Unauthorized to confirm this property"}), 403
        
        # Update confirmation date
        mongo.db.properties.update_one(
            {"_id": ObjectId(property_id)},
            {"$set": {
                "last_confirmed_at": datetime.utcnow(),
                "status": "active"
            }}
        )
        
        return jsonify({"message": "Property listing confirmed successfully"}), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to confirm property: {str(e)}"}), 500