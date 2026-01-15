# property_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from extensions import mongo
from models.property import Property
from utils.decorators import landlord_only
from utils.validators import validate_property_data
from utils.property_moderation import PropertyModerator
from config.moderation_config import ModerationConfig
from bson import ObjectId
from datetime import datetime
import os

property_bp = Blueprint("property", __name__)
# Initialize moderator
moderator = PropertyModerator()

    
    #  ---------------------------
# VALIDATE AND AUTO-GEOCODE ON PROPERTY CREATION
# ---------------------------
# # Modify the create_property endpoint to auto-geocode if coordinates not provided
# @property_bp.route("/", methods=["POST"])
# @jwt_required()
# @landlord_only
# def create_property():
#     try:
#         user_id = get_jwt_identity()
#         data = request.get_json()
        
#         # Validate property data
#         is_valid, errors = validate_property_data(data)
#         if not is_valid:
#             return jsonify({"error": errors}), 400
        
#         # Auto-geocode if coordinates not provided
#         if not data.get("latitude") or not data.get("longitude"):
#             print("⚠️ No coordinates provided. Attempting to geocode address...")
            
#             geocode_result = geocode_address(
#                 data.get("address"),
#                 data.get("city"),
#                 data.get("state"),
#                 data.get("country")
#             )
            
#             if geocode_result:
#                 data["latitude"] = geocode_result["latitude"]
#                 data["longitude"] = geocode_result["longitude"]
#                 print(f"✅ Auto-geocoded: {geocode_result['latitude']}, {geocode_result['longitude']}")
#             else:
#                 print("⚠️ Auto-geocoding failed. Property will be created without coordinates.")
        
#         # Create property object
#         property_obj = Property(
#             landlord_id=user_id,
#             title=data.get("title"),
#             description=data.get("description"),
#             property_type=data.get("property_type"),
#             address=data.get("address"),
#             city=data.get("city"),
#             state=data.get("state"),
#             zip_code=data.get("zip_code"),
#             country=data.get("country"),
#             latitude=data.get("latitude"),
#             longitude=data.get("longitude"),
#             price=data.get("price"),
#             bedrooms=data.get("bedrooms"),
#             bathrooms=data.get("bathrooms"),
#             area_sqft=data.get("area_sqft"),
#             images=data.get("images", []),
#             videos=data.get("videos", []),
#             amenities=data.get("amenities", []),
#             is_featured=data.get("is_featured", False)
#         )
        
#         # Insert into database
#         result = mongo.db.properties.insert_one(property_obj.to_dict())
        
#         return jsonify({
#             "message": "Property created successfully",
#             "property_id": str(result.inserted_id),
#             "coordinates_added": bool(data.get("latitude") and data.get("longitude"))
#         }), 201
        
#     except Exception as e:
#         return jsonify({"error": f"Failed to create property: {str(e)}"}), 500
# Initialize moderator
moderator = PropertyModerator()

@property_bp.route("/", methods=["POST"])
@jwt_required()
@landlord_only
def create_property():
    """
    Create property with automatic moderation
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        print("\n" + "="*60)
        print("🏠 CREATE PROPERTY - AUTO-MODERATION ENABLED")
        print("="*60)
        print(f"User ID: {user_id}")
        print(f"Property Title: {data.get('title')}")
        
        # Step 1: Validate property data (existing validation)
        is_valid, errors = validate_property_data(data)
        if not is_valid:
            print(f"❌ Validation failed: {errors}")
            return jsonify({"error": errors}), 400
        
        print("✅ Basic validation passed")
        
        # Step 2: Auto-moderation (NEW)
        if ModerationConfig.AUTO_MODERATION_ENABLED:
            print("\n🤖 Running auto-moderation...")
            
            moderation_status, moderation_score, moderation_issues = moderator.moderate_property(data)
            moderation_summary = moderator.get_moderation_summary(
                moderation_status, 
                moderation_score, 
                moderation_issues
            )
            
            print(f"   Status: {moderation_status}")
            print(f"   Score: {moderation_score}/100")
            print(f"   Issues: {len(moderation_issues)}")
            
            if moderation_issues:
                for issue in moderation_issues[:5]:  # Show first 5
                    print(f"      - {issue}")
        else:
            # If moderation disabled, approve by default
            moderation_status = 'approved'
            moderation_score = 100
            moderation_issues = []
            moderation_summary = {
                'status': 'approved',
                'score': 100,
                'message': 'Auto-moderation disabled',
                'issues': []
            }
            print("⚠️ Auto-moderation is disabled - approving by default")
        
        # Step 3: Auto-geocode if coordinates not provided
        if not data.get("latitude") or not data.get("longitude"):
            print("\n🗺️ No coordinates provided. Attempting to geocode...")
            
            try:
                from utils.location_utils import geocode_address
                geocode_result = geocode_address(
                    data.get("address"),
                    data.get("city"),
                    data.get("state"),
                    data.get("country")
                )
                
                if geocode_result:
                    data["latitude"] = geocode_result["latitude"]
                    data["longitude"] = geocode_result["longitude"]
                    print(f"   ✅ Geocoded: {geocode_result['latitude']}, {geocode_result['longitude']}")
                else:
                    print("   ⚠️ Geocoding failed. Property will be created without coordinates.")
            except Exception as e:
                print(f"   ⚠️ Geocoding error: {str(e)}")
        
        # Step 4: Determine property status based on moderation
        if moderation_status == 'approved':
            property_status = 'active'  # Immediately active
        elif moderation_status == 'pending_review':
            property_status = 'pending'  # Pending admin review
        else:  # rejected
            property_status = 'inactive'  # Not visible
        
        print(f"\n📋 Property status will be: {property_status}")
        
        # Step 5: Create property object with moderation data
        property_obj = Property(
            landlord_id=user_id,
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
            is_featured=data.get("is_featured", False),
            # Property status
            status=property_status,
            # Moderation data (NEW)
            moderation_status=moderation_status,
            moderation_score=moderation_score,
            moderation_issues=moderation_issues,
            moderation_notes=moderation_summary['message'],
            moderated_at=datetime.utcnow()
        )
        
        # Step 6: Insert into database
        result = mongo.db.properties.insert_one(property_obj.to_dict())
        property_id = str(result.inserted_id)
        
        print(f"\n✅ Property created with ID: {property_id}")
        print("="*60 + "\n")
        
        # Step 7: Prepare response
        response = {
            "message": "Property created successfully",
            "property_id": property_id,
            "status": property_status,
            "moderation": moderation_summary,
            "coordinates_added": bool(data.get("latitude") and data.get("longitude"))
        }
        
        # Step 8: Send notifications based on moderation result
        # TODO: Implement notification sending
        # if moderation_status == 'approved':
        #     send_notification(user_id, "Property approved and listed!")
        # elif moderation_status == 'pending_review':
        #     send_notification(user_id, "Property submitted for review")
        #     notify_admin(property_id, "New property needs review")
        # else:  # rejected
        #     send_notification(user_id, f"Property needs improvement: {', '.join(moderation_issues[:3])}")
        
        return jsonify(response), 201
        
    except Exception as e:
        print(f"\n❌ Error creating property: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to create property: {str(e)}"}), 500


# ============================================================================
# NEW ENDPOINT: Get property moderation status
# ============================================================================

@property_bp.route("/<property_id>/moderation", methods=["GET"])
@jwt_required()
def get_property_moderation(property_id):
    """Get moderation details for a property"""
    try:
        user_id = get_jwt_identity()
        
        # Validate property ID
        if not ObjectId.is_valid(property_id):
            return jsonify({"error": "Invalid property ID"}), 400
        
        # Get property
        property_data = mongo.db.properties.find_one({"_id": ObjectId(property_id)})
        
        if not property_data:
            return jsonify({"error": "Property not found"}), 404
        
        # Check if user owns the property or is admin
        if str(property_data["landlord_id"]) != user_id:
            # TODO: Add admin check here
            return jsonify({"error": "Unauthorized"}), 403
        
        # Extract moderation data
        moderation_data = {
            "property_id": property_id,
            "moderation_status": property_data.get("moderation_status", "unknown"),
            "moderation_score": property_data.get("moderation_score", 0),
            "moderation_issues": property_data.get("moderation_issues", []),
            "moderation_notes": property_data.get("moderation_notes", ""),
            "moderated_at": property_data.get("moderated_at"),
            "status": property_data.get("status")
        }
        
        return jsonify(moderation_data), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get moderation data: {str(e)}"}), 500


# ============================================================================
# NEW ENDPOINT: Re-moderate property (after landlord makes changes)
# ============================================================================

@property_bp.route("/<property_id>/remoderate", methods=["POST"])
@jwt_required()
@landlord_only
def remoderate_property(property_id):
    """Re-run moderation after property updates"""
    try:
        user_id = get_jwt_identity()
        
        # Validate property ID
        if not ObjectId.is_valid(property_id):
            return jsonify({"error": "Invalid property ID"}), 400
        
        # Get property
        property_data = mongo.db.properties.find_one({"_id": ObjectId(property_id)})
        
        if not property_data:
            return jsonify({"error": "Property not found"}), 404
        
        # Check ownership
        if str(property_data["landlord_id"]) != user_id:
            return jsonify({"error": "Unauthorized"}), 403
        
        # Run moderation
        moderation_status, moderation_score, moderation_issues = moderator.moderate_property(property_data)
        moderation_summary = moderator.get_moderation_summary(
            moderation_status, 
            moderation_score, 
            moderation_issues
        )
        
        # Determine new status
        if moderation_status == 'approved':
            new_status = 'active'
        elif moderation_status == 'pending_review':
            new_status = 'pending'
        else:
            new_status = 'inactive'
        
        # Update property
        mongo.db.properties.update_one(
            {"_id": ObjectId(property_id)},
            {"$set": {
                "moderation_status": moderation_status,
                "moderation_score": moderation_score,
                "moderation_issues": moderation_issues,
                "moderation_notes": moderation_summary['message'],
                "moderated_at": datetime.utcnow(),
                "status": new_status,
                "updated_at": datetime.utcnow()
            }}
        )
        
        return jsonify({
            "message": "Property re-moderated successfully",
            "moderation": moderation_summary,
            "status": new_status
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to remoderate property: {str(e)}"}), 500

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
    
# routes/property_routes.py (ADD THESE NEW ENDPOINTS)

# Add these imports at the top
from utils.location_utils import (
    geocode_address, 
    reverse_geocode, 
    calculate_distance,
    find_properties_nearby,
    validate_coordinates,
    get_bounding_box
)

# ---------------------------
# GEOCODE ADDRESS (Convert address to coordinates)
# ---------------------------
@property_bp.route("/geocode", methods=["POST"])
def geocode_property_address():
    """
    Convert address to coordinates
    Request body: {
        "address": "123 Main St",
        "city": "New York",
        "state": "NY",
        "country": "USA"
    }
    """
    try:
        data = request.get_json()
        
        address = data.get("address")
        city = data.get("city")
        state = data.get("state")
        country = data.get("country")
        
        if not address:
            return jsonify({"error": "Address is required"}), 400
        
        # Geocode the address
        result = geocode_address(address, city, state, country)
        
        if result:
            return jsonify({
                "success": True,
                "data": result
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Could not geocode address. Please check the address and try again."
            }), 404
            
    except Exception as e:
        return jsonify({"error": f"Geocoding failed: {str(e)}"}), 500


# ---------------------------
# REVERSE GEOCODE (Convert coordinates to address)
# ---------------------------
@property_bp.route("/reverse-geocode", methods=["POST"])
def reverse_geocode_coordinates():
    """
    Convert coordinates to address
    Request body: {
        "latitude": 40.7128,
        "longitude": -74.0060
    }
    """
    try:
        data = request.get_json()
        
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        
        if latitude is None or longitude is None:
            return jsonify({"error": "Latitude and longitude are required"}), 400
        
        # Validate coordinates
        is_valid, error_msg = validate_coordinates(latitude, longitude)
        if not is_valid:
            return jsonify({"error": error_msg}), 400
        
        # Reverse geocode
        result = reverse_geocode(latitude, longitude)
        
        if result:
            return jsonify({
                "success": True,
                "data": result
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Could not reverse geocode coordinates"
            }), 404
            
    except Exception as e:
        return jsonify({"error": f"Reverse geocoding failed: {str(e)}"}), 500


# ---------------------------
# SEARCH PROPERTIES BY LOCATION (Nearby search)
# ---------------------------
@property_bp.route("/nearby", methods=["POST"])
def search_properties_nearby():
    """
    Search properties near a location
    Request body: {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "radius_km": 10,
        "property_type": "apartment" (optional),
        "min_price": 1000 (optional),
        "max_price": 5000 (optional),
        "bedrooms": 2 (optional),
        "page": 1,
        "per_page": 20
    }
    """
    try:
        data = request.get_json()
        
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        radius_km = data.get("radius_km", 10)  # Default 10km radius
        
        if latitude is None or longitude is None:
            return jsonify({"error": "Latitude and longitude are required"}), 400
        
        # Validate coordinates
        is_valid, error_msg = validate_coordinates(latitude, longitude)
        if not is_valid:
            return jsonify({"error": error_msg}), 400
        
        # Validate radius
        try:
            radius_km = float(radius_km)
            if radius_km <= 0 or radius_km > 100:
                return jsonify({"error": "Radius must be between 0 and 100 km"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid radius value"}), 400
        
        # Get bounding box for efficient querying
        bbox = get_bounding_box(latitude, longitude, radius_km)
        
        # Build query with optional filters
        query = {
            "status": "active",
            "latitude": {"$gte": bbox["min_lat"], "$lte": bbox["max_lat"]},
            "longitude": {"$gte": bbox["min_lon"], "$lte": bbox["max_lon"]}
        }
        
        # Add optional filters
        if data.get("property_type"):
            query["property_type"] = data["property_type"]
        
        if data.get("min_price") or data.get("max_price"):
            query["price"] = {}
            if data.get("min_price"):
                query["price"]["$gte"] = float(data["min_price"])
            if data.get("max_price"):
                query["price"]["$lte"] = float(data["max_price"])
        
        if data.get("bedrooms"):
            query["bedrooms"] = int(data["bedrooms"])
        
        # Get properties from database
        properties = list(mongo.db.properties.find(query))
        
        # Filter by actual distance and add distance field
        nearby_properties = find_properties_nearby(
            properties, latitude, longitude, radius_km
        )
        
        # Pagination
        page = data.get("page", 1)
        per_page = data.get("per_page", 20)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        paginated_properties = nearby_properties[start_idx:end_idx]
        
        # Convert ObjectId to string
        for prop in paginated_properties:
            prop["_id"] = str(prop["_id"])
            prop["landlord_id"] = str(prop["landlord_id"])
            prop["created_at"] = prop["created_at"].isoformat() if isinstance(prop["created_at"], datetime) else prop["created_at"]
            prop["updated_at"] = prop["updated_at"].isoformat() if isinstance(prop["updated_at"], datetime) else prop["updated_at"]
        
        return jsonify({
            "properties": paginated_properties,
            "count": len(paginated_properties),
            "total": len(nearby_properties),
            "page": page,
            "per_page": per_page,
            "total_pages": (len(nearby_properties) + per_page - 1) // per_page,
            "search_center": {
                "latitude": latitude,
                "longitude": longitude,
                "radius_km": radius_km
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Nearby search failed: {str(e)}"}), 500


# ---------------------------
# GET PROPERTY WITH DISTANCE FROM USER
# ---------------------------
@property_bp.route("/<property_id>/distance", methods=["POST"])
def get_property_distance(property_id):
    """
    Get distance from user's location to property
    Request body: {
        "latitude": 40.7128,
        "longitude": -74.0060
    }
    """
    try:
        data = request.get_json()
        
        user_lat = data.get("latitude")
        user_lon = data.get("longitude")
        
        if user_lat is None or user_lon is None:
            return jsonify({"error": "User latitude and longitude are required"}), 400
        
        # Validate coordinates
        is_valid, error_msg = validate_coordinates(user_lat, user_lon)
        if not is_valid:
            return jsonify({"error": error_msg}), 400
        
        # Validate property ID
        if not ObjectId.is_valid(property_id):
            return jsonify({"error": "Invalid property ID"}), 400
        
        # Get property
        property_data = mongo.db.properties.find_one({"_id": ObjectId(property_id)})
        
        if not property_data:
            return jsonify({"error": "Property not found"}), 404
        
        # Check if property has coordinates
        if not property_data.get("latitude") or not property_data.get("longitude"):
            return jsonify({
                "error": "Property does not have location coordinates"
            }), 400
        
        # Calculate distance
        distance = calculate_distance(
            user_lat, user_lon,
            property_data["latitude"], property_data["longitude"]
        )
        
        return jsonify({
            "property_id": property_id,
            "distance_km": distance,
            "property_location": {
                "latitude": property_data["latitude"],
                "longitude": property_data["longitude"],
                "address": property_data.get("address"),
                "city": property_data.get("city")
            },
            "user_location": {
                "latitude": user_lat,
                "longitude": user_lon
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to calculate distance: {str(e)}"}), 500


#