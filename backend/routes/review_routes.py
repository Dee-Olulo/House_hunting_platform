# backend/routes/review_routes.py
"""
Review & Rating System - FIXED VERSION
Properly handles tenant anonymization
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import mongo
from bson import ObjectId
from datetime import datetime
from utils.decorators import landlord_only

review_bp = Blueprint("reviews", __name__)

# ============================================================================
# HELPER FUNCTION - ANONYMIZE TENANT NAME
# ============================================================================

def get_anonymous_tenant_name(tenant_email):
    """
    Create an anonymous tenant identifier from email
    Example: john.doe@example.com -> "John D."
    """
    if not tenant_email:
        return "Tenant"
    
    try:
        username = tenant_email.split('@')[0]
        # Split by dots or underscores
        parts = username.replace('_', '.').split('.')
        
        if len(parts) > 1:
            # "John D." from john.doe
            first_name = parts[0].capitalize()
            last_initial = parts[1][0].upper() if parts[1] else ''
            return f"{first_name} {last_initial}." if last_initial else first_name
        else:
            # Just capitalize single name
            return username.capitalize()
    except:
        return "Tenant"

# ============================================================================
# CREATE REVIEW
# ============================================================================

@review_bp.route("/create", methods=["POST"])
@jwt_required()
def create_review():
    """
    Create a review for a landlord
    Only tenants who have completed bookings can review
    """
    try:
        tenant_id = get_jwt_identity()
        data = request.get_json()
        
        landlord_id = data.get('landlord_id')
        property_id = data.get('property_id')
        rating = data.get('rating')
        title = data.get('title', '')
        comment = data.get('comment', '')
        categories = data.get('categories', {})
        
        # Validation
        if not landlord_id or not property_id or not rating:
            return jsonify({"error": "Landlord ID, property ID, and rating are required"}), 400
        
        if not ObjectId.is_valid(landlord_id) or not ObjectId.is_valid(property_id):
            return jsonify({"error": "Invalid ID format"}), 400
        
        if not isinstance(rating, (int, float)) or rating < 1 or rating > 5:
            return jsonify({"error": "Rating must be between 1 and 5"}), 400
        
        # Check if tenant has a completed booking with this landlord
        booking = mongo.db.bookings.find_one({
            "tenant_id": tenant_id,
            "landlord_id": landlord_id,
            "property_id": ObjectId(property_id),
            "status": "completed"
        })
        
        if not booking:
            return jsonify({"error": "You must have a completed booking to leave a review"}), 403
        
        # Check if tenant has already reviewed this landlord for this property
        existing_review = mongo.db.reviews.find_one({
            "tenant_id": tenant_id,
            "landlord_id": landlord_id,
            "property_id": ObjectId(property_id)
        })
        
        if existing_review:
            return jsonify({"error": "You have already reviewed this landlord for this property"}), 400
        
        # Get tenant info
        tenant = mongo.db.users.find_one({"_id": ObjectId(tenant_id)}, {"email": 1})
        property_doc = mongo.db.properties.find_one({"_id": ObjectId(property_id)}, {"title": 1})
        
        tenant_email = tenant.get("email", "unknown@example.com")
        
        # Create review
        review = {
            "tenant_id": tenant_id,
            "tenant_email": tenant_email,  # Store for internal use only
            "tenant_name": get_anonymous_tenant_name(tenant_email),  # Public display name
            "landlord_id": landlord_id,
            "property_id": ObjectId(property_id),
            "property_title": property_doc.get("title", "Unknown Property") if property_doc else "Unknown Property",
            "rating": float(rating),
            "title": title.strip(),
            "comment": comment.strip(),
            "categories": {
                "communication": float(categories.get("communication", 0)),
                "responsiveness": float(categories.get("responsiveness", 0)),
                "property_accuracy": float(categories.get("property_accuracy", 0)),
                "cleanliness": float(categories.get("cleanliness", 0)),
                "value_for_money": float(categories.get("value_for_money", 0))
            },
            "is_verified": True,
            "is_public": True,
            "helpful_count": 0,
            "reported_count": 0,
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = mongo.db.reviews.insert_one(review)
        review_id = str(result.inserted_id)
        
        # Update landlord's average rating
        update_landlord_rating(landlord_id)
        
        # Send notification to landlord
        notification = {
            "user_id": landlord_id,
            "title": "New Review Received",
            "message": f"You received a {rating}-star review",
            "notification_type": "new_review",
            "link": "/landlord/reviews",
            "is_read": False,
            "created_at": datetime.utcnow()
        }
        mongo.db.notifications.insert_one(notification)
        
        print(f"✅ Review created: {review_id} - {rating} stars by {review['tenant_name']}")
        
        return jsonify({
            "message": "Review submitted successfully",
            "review_id": review_id,
            "rating": rating
        }), 201
        
    except Exception as e:
        print(f"❌ Error creating review: {str(e)}")
        return jsonify({"error": f"Failed to create review: {str(e)}"}), 500


# ============================================================================
# GET LANDLORD REVIEWS (PUBLIC)
# ============================================================================

@review_bp.route("/landlord/<landlord_id>", methods=["GET"])
def get_landlord_reviews(landlord_id):
    """Get all reviews for a specific landlord (public endpoint)"""
    try:
        if not ObjectId.is_valid(landlord_id):
            return jsonify({"error": "Invalid landlord ID"}), 400
        
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        sort_by = request.args.get("sort_by", "newest")
        
        query = {
            "landlord_id": landlord_id,
            "is_public": True,
            "status": "active"
        }
        
        # Build sort
        sort_map = {
            "oldest": [("created_at", 1)],
            "highest": [("rating", -1)],
            "lowest": [("rating", 1)],
            "newest": [("created_at", -1)]
        }
        sort_criteria = sort_map.get(sort_by, [("created_at", -1)])
        
        total_count = mongo.db.reviews.count_documents(query)
        
        skip = (page - 1) * per_page
        reviews = list(mongo.db.reviews.find(query)
                      .sort(sort_criteria)
                      .skip(skip)
                      .limit(per_page))
        
        # Format reviews for public display
        for review in reviews:
            review["_id"] = str(review["_id"])
            review["property_id"] = str(review["property_id"])
            
            # Keep the pre-generated anonymous name
            # tenant_name is already anonymized from creation
            
            # Remove internal email field for public API
            review.pop("tenant_email", None)
            
            # Format dates
            if review.get("created_at"):
                review["created_at"] = review["created_at"].isoformat()
            if review.get("updated_at"):
                review["updated_at"] = review["updated_at"].isoformat()
        
        stats = calculate_landlord_stats(landlord_id)
        
        return jsonify({
            "reviews": reviews,
            "count": len(reviews),
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "total_pages": (total_count + per_page - 1) // per_page,
            "statistics": stats
        }), 200
        
    except Exception as e:
        print(f"❌ Error getting reviews: {str(e)}")
        return jsonify({"error": f"Failed to get reviews: {str(e)}"}), 500


# ============================================================================
# GET MY REVIEWS (TENANT)
# ============================================================================

@review_bp.route("/my-reviews", methods=["GET"])
@jwt_required()
def get_my_reviews():
    """Get reviews written by the current tenant"""
    try:
        tenant_id = get_jwt_identity()
        
        reviews = list(mongo.db.reviews.find({"tenant_id": tenant_id})
                      .sort("created_at", -1))
        
        for review in reviews:
            review["_id"] = str(review["_id"])
            review["property_id"] = str(review["property_id"])
            
            # Tenant can see their own email
            if review.get("created_at"):
                review["created_at"] = review["created_at"].isoformat()
            if review.get("updated_at"):
                review["updated_at"] = review["updated_at"].isoformat()
        
        return jsonify({"reviews": reviews}), 200
        
    except Exception as e:
        print(f"❌ Error getting tenant reviews: {str(e)}")
        return jsonify({"error": f"Failed to get reviews: {str(e)}"}), 500


# ============================================================================
# GET REVIEWS ABOUT ME (LANDLORD)
# ============================================================================

@review_bp.route("/about-me", methods=["GET"])
@jwt_required()
@landlord_only
def get_reviews_about_me():
    """Get all reviews received by the landlord"""
    try:
        landlord_id = get_jwt_identity()
        
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        
        query = {"landlord_id": landlord_id, "status": "active"}
        
        total_count = mongo.db.reviews.count_documents(query)
        
        skip = (page - 1) * per_page
        reviews = list(mongo.db.reviews.find(query)
                      .sort("created_at", -1)
                      .skip(skip)
                      .limit(per_page))
        
        for review in reviews:
            review["_id"] = str(review["_id"])
            review["property_id"] = str(review["property_id"])
            
            # Landlord sees anonymous tenant names (not emails)
            review.pop("tenant_email", None)
            
            if review.get("created_at"):
                review["created_at"] = review["created_at"].isoformat()
            if review.get("updated_at"):
                review["updated_at"] = review["updated_at"].isoformat()
        
        stats = calculate_landlord_stats(landlord_id)
        
        return jsonify({
            "reviews": reviews,
            "count": len(reviews),
            "total": total_count,
            "page": page,
            "total_pages": (total_count + per_page - 1) // per_page,
            "statistics": stats
        }), 200
        
    except Exception as e:
        print(f"❌ Error getting landlord reviews: {str(e)}")
        return jsonify({"error": f"Failed to get reviews: {str(e)}"}), 500


# ============================================================================
# UPDATE REVIEW
# ============================================================================

@review_bp.route("/<review_id>", methods=["PUT"])
@jwt_required()
def update_review(review_id):
    """Update own review (tenant only)"""
    try:
        tenant_id = get_jwt_identity()
        
        if not ObjectId.is_valid(review_id):
            return jsonify({"error": "Invalid review ID"}), 400
        
        review = mongo.db.reviews.find_one({
            "_id": ObjectId(review_id),
            "tenant_id": tenant_id
        })
        
        if not review:
            return jsonify({"error": "Review not found or unauthorized"}), 404
        
        data = request.get_json()
        
        update_data = {"updated_at": datetime.utcnow()}
        
        if "rating" in data:
            rating = data["rating"]
            if not isinstance(rating, (int, float)) or rating < 1 or rating > 5:
                return jsonify({"error": "Rating must be between 1 and 5"}), 400
            update_data["rating"] = float(rating)
        
        if "title" in data:
            update_data["title"] = data["title"].strip()
        
        if "comment" in data:
            update_data["comment"] = data["comment"].strip()
        
        if "categories" in data:
            update_data["categories"] = {
                "communication": float(data["categories"].get("communication", 0)),
                "responsiveness": float(data["categories"].get("responsiveness", 0)),
                "property_accuracy": float(data["categories"].get("property_accuracy", 0)),
                "cleanliness": float(data["categories"].get("cleanliness", 0)),
                "value_for_money": float(data["categories"].get("value_for_money", 0))
            }
        
        mongo.db.reviews.update_one(
            {"_id": ObjectId(review_id)},
            {"$set": update_data}
        )
        
        update_landlord_rating(review["landlord_id"])
        
        return jsonify({"message": "Review updated successfully"}), 200
        
    except Exception as e:
        print(f"❌ Error updating review: {str(e)}")
        return jsonify({"error": f"Failed to update review: {str(e)}"}), 500


# ============================================================================
# DELETE REVIEW
# ============================================================================

@review_bp.route("/<review_id>", methods=["DELETE"])
@jwt_required()
def delete_review(review_id):
    """Delete own review (tenant only)"""
    try:
        tenant_id = get_jwt_identity()
        
        if not ObjectId.is_valid(review_id):
            return jsonify({"error": "Invalid review ID"}), 400
        
        review = mongo.db.reviews.find_one({
            "_id": ObjectId(review_id),
            "tenant_id": tenant_id
        })
        
        if not review:
            return jsonify({"error": "Review not found or unauthorized"}), 404
        
        mongo.db.reviews.update_one(
            {"_id": ObjectId(review_id)},
            {"$set": {"status": "deleted", "deleted_at": datetime.utcnow()}}
        )
        
        update_landlord_rating(review["landlord_id"])
        
        return jsonify({"message": "Review deleted successfully"}), 200
        
    except Exception as e:
        print(f"❌ Error deleting review: {str(e)}")
        return jsonify({"error": f"Failed to delete review: {str(e)}"}), 500


# ============================================================================
# MARK REVIEW AS HELPFUL
# ============================================================================

@review_bp.route("/<review_id>/helpful", methods=["POST"])
@jwt_required()
def mark_helpful(review_id):
    """Mark a review as helpful"""
    try:
        if not ObjectId.is_valid(review_id):
            return jsonify({"error": "Invalid review ID"}), 400
        
        mongo.db.reviews.update_one(
            {"_id": ObjectId(review_id)},
            {"$inc": {"helpful_count": 1}}
        )
        
        return jsonify({"message": "Marked as helpful"}), 200
        
    except Exception as e:
        print(f"❌ Error marking helpful: {str(e)}")
        return jsonify({"error": f"Failed to mark as helpful: {str(e)}"}), 500


# ============================================================================
# REPORT REVIEW
# ============================================================================

@review_bp.route("/<review_id>/report", methods=["POST"])
@jwt_required()
def report_review(review_id):
    """Report inappropriate review"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        reason = data.get("reason", "")
        
        if not ObjectId.is_valid(review_id):
            return jsonify({"error": "Invalid review ID"}), 400
        
        mongo.db.reviews.update_one(
            {"_id": ObjectId(review_id)},
            {"$inc": {"reported_count": 1}}
        )
        
        report = {
            "review_id": ObjectId(review_id),
            "reported_by": user_id,
            "reason": reason,
            "created_at": datetime.utcnow(),
            "status": "pending"
        }
        mongo.db.review_reports.insert_one(report)
        
        review = mongo.db.reviews.find_one({"_id": ObjectId(review_id)})
        if review and review.get("reported_count", 0) >= 3:
            mongo.db.reviews.update_one(
                {"_id": ObjectId(review_id)},
                {"$set": {"status": "hidden"}}
            )
        
        return jsonify({"message": "Review reported"}), 200
        
    except Exception as e:
        print(f"❌ Error reporting review: {str(e)}")
        return jsonify({"error": f"Failed to report review: {str(e)}"}), 500


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def update_landlord_rating(landlord_id):
    """Update landlord's overall rating based on reviews"""
    try:
        pipeline = [
            {
                "$match": {
                    "landlord_id": landlord_id,
                    "status": "active"
                }
            },
            {
                "$group": {
                    "_id": None,
                    "avg_rating": {"$avg": "$rating"},
                    "total_reviews": {"$sum": 1},
                    "avg_communication": {"$avg": "$categories.communication"},
                    "avg_responsiveness": {"$avg": "$categories.responsiveness"},
                    "avg_property_accuracy": {"$avg": "$categories.property_accuracy"},
                    "avg_cleanliness": {"$avg": "$categories.cleanliness"},
                    "avg_value_for_money": {"$avg": "$categories.value_for_money"}
                }
            }
        ]
        
        result = list(mongo.db.reviews.aggregate(pipeline))
        
        if result:
            stats = result[0]
            mongo.db.users.update_one(
                {"_id": ObjectId(landlord_id)},
                {"$set": {
                    "rating": round(stats.get("avg_rating", 0), 2),
                    "total_reviews": stats.get("total_reviews", 0),
                    "rating_breakdown": {
                        "communication": round(stats.get("avg_communication", 0), 2),
                        "responsiveness": round(stats.get("avg_responsiveness", 0), 2),
                        "property_accuracy": round(stats.get("avg_property_accuracy", 0), 2),
                        "cleanliness": round(stats.get("avg_cleanliness", 0), 2),
                        "value_for_money": round(stats.get("avg_value_for_money", 0), 2)
                    }
                }}
            )
        else:
            mongo.db.users.update_one(
                {"_id": ObjectId(landlord_id)},
                {"$set": {"rating": 0, "total_reviews": 0}}
            )
        
    except Exception as e:
        print(f"❌ Error updating landlord rating: {str(e)}")


def calculate_landlord_stats(landlord_id):
    """Calculate detailed statistics for a landlord"""
    try:
        pipeline = [
            {
                "$match": {
                    "landlord_id": landlord_id,
                    "status": "active"
                }
            },
            {
                "$facet": {
                    "overall": [
                        {
                            "$group": {
                                "_id": None,
                                "avg_rating": {"$avg": "$rating"},
                                "total_reviews": {"$sum": 1}
                            }
                        }
                    ],
                    "rating_distribution": [
                        {
                            "$group": {
                                "_id": "$rating",
                                "count": {"$sum": 1}
                            }
                        },
                        {"$sort": {"_id": -1}}
                    ],
                    "categories": [
                        {
                            "$group": {
                                "_id": None,
                                "communication": {"$avg": "$categories.communication"},
                                "responsiveness": {"$avg": "$categories.responsiveness"},
                                "property_accuracy": {"$avg": "$categories.property_accuracy"},
                                "cleanliness": {"$avg": "$categories.cleanliness"},
                                "value_for_money": {"$avg": "$categories.value_for_money"}
                            }
                        }
                    ]
                }
            }
        ]
        
        result = list(mongo.db.reviews.aggregate(pipeline))
        
        if result and result[0]:
            data = result[0]
            overall = data["overall"][0] if data["overall"] else {}
            categories = data["categories"][0] if data["categories"] else {}
            
            distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            for item in data["rating_distribution"]:
                distribution[int(item["_id"])] = item["count"]
            
            return {
                "average_rating": round(overall.get("avg_rating", 0), 2),
                "total_reviews": overall.get("total_reviews", 0),
                "rating_distribution": distribution,
                "category_ratings": {
                    "communication": round(categories.get("communication", 0), 2),
                    "responsiveness": round(categories.get("responsiveness", 0), 2),
                    "property_accuracy": round(categories.get("property_accuracy", 0), 2),
                    "cleanliness": round(categories.get("cleanliness", 0), 2),
                    "value_for_money": round(categories.get("value_for_money", 0), 2)
                }
            }
        
        return {
            "average_rating": 0,
            "total_reviews": 0,
            "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            "category_ratings": {
                "communication": 0,
                "responsiveness": 0,
                "property_accuracy": 0,
                "cleanliness": 0,
                "value_for_money": 0
            }
        }
        
    except Exception as e:
        print(f"❌ Error calculating stats: {str(e)}")
        return {}