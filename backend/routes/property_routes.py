# property_routes.py
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
# # GET ALL PROPERTIES (PUBLIC)
# # ---------------------------
# @property_bp.route("/", methods=["GET"], strict_slashes=False)
# def get_all_properties():
#     try:
#         # Get query parameters for filtering
#         city = request.args.get("city")
#         state = request.args.get("state")
#         min_price = request.args.get("min_price", type=float)
#         max_price = request.args.get("max_price", type=float)
#         bedrooms = request.args.get("bedrooms", type=int)
#         bathrooms = request.args.get("bathrooms", type=int)
#         property_type = request.args.get("property_type")
#         status = request.args.get("status", "active")
#         # Sorting
#         sort_by = request.args.get("sort_by", "newest")  # newest, price_low, price_high, bedrooms
        
#         # Pagination
#         page = request.args.get("page", 1, type=int)
#         per_page = request.args.get("per_page", 20, type=int)
        
#         # Search query (for title/description)
#         search = request.args.get("search")
        
#         # Build query
#         query = {"status": status}
        
#         if city:
#             query["city"] = {"$regex": city, "$options": "i"}
#         # State filter
#         if state:
#             query["state"] = {"$regex": state, "$options": "i"}
        
#         if min_price is not None or max_price is not None:
#             query["price"] = {}
#             if min_price is not None:
#                 query["price"]["$gte"] = min_price
#             if max_price is not None:
#                 query["price"]["$lte"] = max_price
        
#         # Bedrooms filter
#         if bedrooms is not None:
#             query["bedrooms"] = bedrooms
        
#         # Property type filter
#         if property_type:
#             query["property_type"] = property_type

        
#         # Search filter
#         if search:
#             query["$or"] = [
#                 {"title": {"$regex": search, "$options": "i"}},
#                 {"description": {"$regex": search, "$options": "i"}}
#             ]
        
#         # Build sort criteria
#         sort_criteria = []
#         if sort_by == "price_low":
#             sort_criteria = [("price", 1)]
#         elif sort_by == "price_high":
#             sort_criteria = [("price", -1)]
#         elif sort_by == "bedrooms":
#             sort_criteria = [("bedrooms", -1)]
#         else:  # newest (default)
#             sort_criteria = [("created_at", -1)]

#         # Apply pagination
#         skip = (page - 1) * per_page
#         properties_cursor = mongo.db.properties.find(query).sort(sort_criteria).skip(skip).limit(per_page)
#         properties = list(properties_cursor)

#         # Get total count for pagination
#         total_count = mongo.db.properties.count_documents(query)

#         # Convert ObjectId to string
#         # Convert ObjectId to string
#         for prop in properties:
#             prop["_id"] = str(prop["_id"])
#             prop["landlord_id"] = str(prop["landlord_id"])
#             prop["created_at"] = prop["created_at"].isoformat() if isinstance(prop["created_at"], datetime) else prop["created_at"]
#             prop["updated_at"] = prop["updated_at"].isoformat() if isinstance(prop["updated_at"], datetime) else prop["updated_at"]
        
#         return jsonify({
#             "properties": properties,
#             "count": len(properties),
#             "total": total_count,
#             "page": page,
#             "per_page": per_page,
#             "total_pages": (total_count + per_page - 1) // per_page,
#             "filters_applied": {
#                 "city": city,
#                 "state": state,
#                 "min_price": min_price,
#                 "max_price": max_price,
#                 "bedrooms": bedrooms,
#                 "bathrooms": bathrooms,
#                 "property_type": property_type,
#                 "search": search,
#                 "sort_by": sort_by
#             }
#         }), 200
#     except Exception as e:
#         return jsonify({"error": f"Failed to fetch properties: {str(e)}"}), 500

    
    #     # Get properties
    #     properties = list(mongo.db.properties.find(query))
        
    #     # Convert ObjectId to string
    #     for prop in properties:
    #         prop["_id"] = str(prop["_id"])
    #         prop["landlord_id"] = str(prop["landlord_id"])
    #         prop["created_at"] = prop["created_at"].isoformat() if isinstance(prop["created_at"], datetime) else prop["created_at"]
    #         prop["updated_at"] = prop["updated_at"].isoformat() if isinstance(prop["updated_at"], datetime) else prop["updated_at"]
        
    #     return jsonify({
    #         "properties": properties,
    #         "count": len(properties)
    #     }), 200
        
    # except Exception as e:
    #     return jsonify({"error": f"Failed to fetch properties: {str(e)}"}), 500
# GET ALL PROPERTIES (PUBLIC)
# ---------------------------
@property_bp.route("/", methods=["GET"], strict_slashes=False)
def get_all_properties():
    try:
        # Get query parameters for filtering
        city = request.args.get("city")
        state = request.args.get("state")
        min_price = request.args.get("min_price", type=float)
        max_price = request.args.get("max_price", type=float)
        bedrooms = request.args.get("bedrooms", type=int)
        bathrooms = request.args.get("bathrooms", type=int)
        property_type = request.args.get("property_type")
        status = request.args.get("status", "active")
        # Sorting
        sort_by = request.args.get("sort_by", "newest")  # newest, price_low, price_high, bedrooms
        
        # Pagination
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        
        # Search query (for title/description)
        search = request.args.get("search")
        
        # Build query
        query = {"status": status}
        
        if city:
            query["city"] = {"$regex": city, "$options": "i"}
        # State filter
        if state:
            query["state"] = {"$regex": state, "$options": "i"}
        
        if min_price is not None or max_price is not None:
            query["price"] = {}
            if min_price is not None:
                query["price"]["$gte"] = min_price
            if max_price is not None:
                query["price"]["$lte"] = max_price
        
        # Bedrooms filter
        if bedrooms is not None:
            query["bedrooms"] = bedrooms
        
        # Property type filter
        if property_type:
            query["property_type"] = property_type

        
        # Search filter
        if search:
            query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]
        
        # Build sort criteria
        sort_criteria = []
        if sort_by == "price_low":
            sort_criteria = [("price", 1)]
        elif sort_by == "price_high":
            sort_criteria = [("price", -1)]
        elif sort_by == "bedrooms":
            sort_criteria = [("bedrooms", -1)]
        else:  # newest (default)
            sort_criteria = [("created_at", -1)]

        # Apply pagination
        skip = (page - 1) * per_page
        properties_cursor = mongo.db.properties.find(query).sort(sort_criteria).skip(skip).limit(per_page)
        properties = list(properties_cursor)

        # Get total count for pagination
        total_count = mongo.db.properties.count_documents(query)

        # Get the base URL for images
        base_url = request.host_url.rstrip('/')
        
        # Convert ObjectId to string and fix image URLs
        for prop in properties:
            prop["_id"] = str(prop["_id"])
            prop["landlord_id"] = str(prop["landlord_id"])
            prop["created_at"] = prop["created_at"].isoformat() if isinstance(prop["created_at"], datetime) else prop["created_at"]
            prop["updated_at"] = prop["updated_at"].isoformat() if isinstance(prop["updated_at"], datetime) else prop["updated_at"]
            
            # Convert relative image paths to full URLs
            if prop.get("images"):
                prop["images"] = [
                    f"{base_url}{img}" if not img.startswith('http') else img
                    for img in prop["images"]
                ]
            
            # Convert video paths if they exist
            if prop.get("videos"):
                prop["videos"] = [
                    f"{base_url}{vid}" if not vid.startswith('http') else vid
                    for vid in prop["videos"]
                ]
        
        return jsonify({
            "properties": properties,
            "count": len(properties),
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "total_pages": (total_count + per_page - 1) // per_page,
            "filters_applied": {
                "city": city,
                "state": state,
                "min_price": min_price,
                "max_price": max_price,
                "bedrooms": bedrooms,
                "bathrooms": bathrooms,
                "property_type": property_type,
                "search": search,
                "sort_by": sort_by
            }
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
        #  Get user ID directly (it's a string)
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
    
    # ---------------------------
# ADVANCED SEARCH ENDPOINT
# ---------------------------
@property_bp.route("/search", methods=["POST"])
def search_properties():
    """
    Advanced search endpoint with POST body
    Allows complex queries and filters
    """
    try:
        data = request.get_json()
        
        # Build query from POST data
        query = {"status": "active"}
        
        # Location filters
        if data.get("city"):
            query["city"] = {"$regex": data["city"], "$options": "i"}
        
        if data.get("state"):
            query["state"] = {"$regex": data["state"], "$options": "i"}
        
        if data.get("country"):
            query["country"] = {"$regex": data["country"], "$options": "i"}
        
        # Price range
        if data.get("min_price") or data.get("max_price"):
            query["price"] = {}
            if data.get("min_price"):
                query["price"]["$gte"] = float(data["min_price"])
            if data.get("max_price"):
                query["price"]["$lte"] = float(data["max_price"])
        
        # Bedrooms range
        if data.get("min_bedrooms"):
            query["bedrooms"] = {"$gte": int(data["min_bedrooms"])}
        
        if data.get("max_bedrooms"):
            if "bedrooms" not in query:
                query["bedrooms"] = {}
            query["bedrooms"]["$lte"] = int(data["max_bedrooms"])
        
        # Bathrooms
        if data.get("min_bathrooms"):
            query["bathrooms"] = {"$gte": float(data["min_bathrooms"])}
        
        # Area (sqft)
        if data.get("min_area") or data.get("max_area"):
            query["area_sqft"] = {}
            if data.get("min_area"):
                query["area_sqft"]["$gte"] = float(data["min_area"])
            if data.get("max_area"):
                query["area_sqft"]["$lte"] = float(data["max_area"])
        
        # Property type (multiple types)
        if data.get("property_types") and len(data["property_types"]) > 0:
            query["property_type"] = {"$in": data["property_types"]}
        
        # Amenities (property must have ALL specified amenities)
        if data.get("amenities") and len(data["amenities"]) > 0:
            query["amenities"] = {"$all": data["amenities"]}
        
        # Text search
        if data.get("search_text"):
            query["$or"] = [
                {"title": {"$regex": data["search_text"], "$options": "i"}},
                {"description": {"$regex": data["search_text"], "$options": "i"}},
                {"address": {"$regex": data["search_text"], "$options": "i"}}
            ]
        
        # Featured properties only
        if data.get("featured_only"):
            query["is_featured"] = True
        
        # Sorting
        sort_by = data.get("sort_by", "newest")
        if sort_by == "price_low":
            sort_criteria = [("price", 1)]
        elif sort_by == "price_high":
            sort_criteria = [("price", -1)]
        elif sort_by == "bedrooms_high":
            sort_criteria = [("bedrooms", -1)]
        elif sort_by == "area_high":
            sort_criteria = [("area_sqft", -1)]
        elif sort_by == "popular":
            sort_criteria = [("views", -1)]
        else:  # newest
            sort_criteria = [("created_at", -1)]
        
        # Pagination
        page = data.get("page", 1)
        per_page = data.get("per_page", 20)
        skip = (page - 1) * per_page
        
        # Execute query
        properties_cursor = mongo.db.properties.find(query).sort(sort_criteria).skip(skip).limit(per_page)
        properties = list(properties_cursor)
        
        # Get total count
        total_count = mongo.db.properties.count_documents(query)
        
        # Convert ObjectId to string
        for prop in properties:
            prop["_id"] = str(prop["_id"])
            prop["landlord_id"] = str(prop["landlord_id"])
            prop["created_at"] = prop["created_at"].isoformat() if isinstance(prop["created_at"], datetime) else prop["created_at"]
            prop["updated_at"] = prop["updated_at"].isoformat() if isinstance(prop["updated_at"], datetime) else prop["updated_at"]
        
        return jsonify({
            "properties": properties,
            "count": len(properties),
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "total_pages": (total_count + per_page - 1) // per_page
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Search failed: {str(e)}"}), 500

# ---------------------------
# GET FILTER OPTIONS (for dropdowns)
# ---------------------------
@property_bp.route("/filters/options", methods=["GET"])
def get_filter_options():
    """
    Get available filter options from existing properties
    Returns unique values for cities, types, etc.
    """
    try:
        # Get unique cities
        cities = mongo.db.properties.distinct("city", {"status": "active"})
        
        # Get unique states
        states = mongo.db.properties.distinct("state", {"status": "active"})
        
        # Get unique property types
        property_types = mongo.db.properties.distinct("property_type", {"status": "active"})
        
        # Get price range
        price_pipeline = [
            {"$match": {"status": "active"}},
            {"$group": {
                "_id": None,
                "min_price": {"$min": "$price"},
                "max_price": {"$max": "$price"}
            }}
        ]
        price_range = list(mongo.db.properties.aggregate(price_pipeline))
        
        # Get bedroom range
        bedroom_pipeline = [
            {"$match": {"status": "active"}},
            {"$group": {
                "_id": None,
                "min_bedrooms": {"$min": "$bedrooms"},
                "max_bedrooms": {"$max": "$bedrooms"}
            }}
        ]
        bedroom_range = list(mongo.db.properties.aggregate(bedroom_pipeline))
        
        # Get all unique amenities
        all_amenities = mongo.db.properties.distinct("amenities", {"status": "active"})
        
        return jsonify({
            "cities": sorted(cities),
            "states": sorted(states),
            "property_types": sorted(property_types),
            "price_range": price_range[0] if price_range else {"min_price": 0, "max_price": 0},
            "bedroom_range": bedroom_range[0] if bedroom_range else {"min_bedrooms": 0, "max_bedrooms": 0},
            "amenities": sorted(all_amenities)
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get filter options: {str(e)}"}), 500

# ---------------------------
# GET PROPERTY STATISTICS
# ---------------------------
@property_bp.route("/stats", methods=["GET"])
def get_property_stats():
    """
    Get statistics about properties
    Total count, average price, etc.
    """
    try:
        # Total properties
        total_properties = mongo.db.properties.count_documents({"status": "active"})
        
        # Average price
        avg_price_pipeline = [
            {"$match": {"status": "active"}},
            {"$group": {
                "_id": None,
                "avg_price": {"$avg": "$price"},
                "min_price": {"$min": "$price"},
                "max_price": {"$max": "$price"}
            }}
        ]
        price_stats = list(mongo.db.properties.aggregate(avg_price_pipeline))
        
        # Properties by type
        type_pipeline = [
            {"$match": {"status": "active"}},
            {"$group": {
                "_id": "$property_type",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]
        by_type = list(mongo.db.properties.aggregate(type_pipeline))
        
        # Properties by city (top 10)
        city_pipeline = [
            {"$match": {"status": "active"}},
            {"$group": {
                "_id": "$city",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        by_city = list(mongo.db.properties.aggregate(city_pipeline))
        
        return jsonify({
            "total_properties": total_properties,
            "price_stats": price_stats[0] if price_stats else {},
            "by_type": by_type,
            "top_cities": by_city
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get statistics: {str(e)}"}), 500