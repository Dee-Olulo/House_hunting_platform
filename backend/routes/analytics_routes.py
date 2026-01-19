# backend/routes/analytics_routes.py
"""
Analytics Routes - Comprehensive Platform Analytics
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import mongo
from utils.decorators import admin_only
from bson import ObjectId
from datetime import datetime, timedelta
from collections import defaultdict

analytics_bp = Blueprint("analytics", __name__)

# ============================================================================
# USER ENGAGEMENT METRICS
# ============================================================================

@analytics_bp.route("/users/engagement", methods=["GET"])
@jwt_required()
@admin_only
def get_user_engagement():
    """Get user engagement metrics"""
    try:
        days = request.args.get("days", 30, type=int)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Total active users (logged in during period)
        # Note: You'll need to track user login activity in your auth
        total_users = mongo.db.users.count_documents({})
        
        # New users in period
        new_users = mongo.db.users.count_documents({
            "created_at": {"$gte": start_date, "$lte": end_date}
        })
        
        # Users by role
        users_by_role = list(mongo.db.users.aggregate([
            {"$group": {
                "_id": "$role",
                "count": {"$sum": 1}
            }}
        ]))
        
        # Daily new users trend
        daily_new_users = list(mongo.db.users.aggregate([
            {"$match": {"created_at": {"$gte": start_date, "$lte": end_date}}},
            {"$group": {
                "_id": {
                    "year": {"$year": "$created_at"},
                    "month": {"$month": "$created_at"},
                    "day": {"$dayOfMonth": "$created_at"}
                },
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]))
        
        # Format daily data
        formatted_daily = []
        for item in daily_new_users:
            date_obj = datetime(item["_id"]["year"], item["_id"]["month"], item["_id"]["day"])
            formatted_daily.append({
                "date": date_obj.strftime("%Y-%m-%d"),
                "count": item["count"]
            })
        
        # User activity (bookings created)
        active_users_count = len(mongo.db.bookings.distinct("tenant_id", {
            "created_at": {"$gte": start_date, "$lte": end_date}
        }))
        
        # Retention rate (users who came back)
        # Simple version: users with multiple bookings
        repeat_users = len(list(mongo.db.bookings.aggregate([
            {"$group": {
                "_id": "$tenant_id",
                "booking_count": {"$sum": 1}
            }},
            {"$match": {"booking_count": {"$gt": 1}}}
        ])))
        
        retention_rate = (repeat_users / total_users * 100) if total_users > 0 else 0
        
        return jsonify({
            "total_users": total_users,
            "new_users": new_users,
            "active_users": active_users_count,
            "retention_rate": round(retention_rate, 2),
            "users_by_role": users_by_role,
            "daily_trend": formatted_daily,
            "period_days": days
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get user engagement: {str(e)}"}), 500


# ============================================================================
# PROPERTY PERFORMANCE METRICS
# ============================================================================

@analytics_bp.route("/properties/performance", methods=["GET"])
@jwt_required()
@admin_only
def get_property_performance():
    """Get property performance metrics"""
    try:
        days = request.args.get("days", 30, type=int)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Total properties
        total_properties = mongo.db.properties.count_documents({})
        active_properties = mongo.db.properties.count_documents({"status": "active"})
        
        # New properties in period
        new_properties = mongo.db.properties.count_documents({
            "created_at": {"$gte": start_date, "$lte": end_date}
        })
        
        # Properties by status
        properties_by_status = list(mongo.db.properties.aggregate([
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }}
        ]))
        
        # Most booked properties
        most_booked = list(mongo.db.bookings.aggregate([
            {"$match": {"created_at": {"$gte": start_date, "$lte": end_date}}},
            {"$group": {
                "_id": "$property_id",
                "booking_count": {"$sum": 1}
            }},
            {"$sort": {"booking_count": -1}},
            {"$limit": 10}
        ]))
        
        # Enrich with property details
        for item in most_booked:
            property_id = item["_id"]
            property_doc = mongo.db.properties.find_one(
                {"_id": ObjectId(property_id)},
                {"title": 1, "city": 1, "price": 1}
            )
            if property_doc:
                item["property_id"] = property_id
                item["title"] = property_doc.get("title", "Unknown")
                item["city"] = property_doc.get("city", "Unknown")
                item["price"] = property_doc.get("price", 0)
                item.pop("_id")
        
        # Conversion rate (bookings / active properties)
        total_bookings = mongo.db.bookings.count_documents({
            "created_at": {"$gte": start_date, "$lte": end_date}
        })
        conversion_rate = (total_bookings / active_properties * 100) if active_properties > 0 else 0
        
        # Daily property listings
        daily_properties = list(mongo.db.properties.aggregate([
            {"$match": {"created_at": {"$gte": start_date, "$lte": end_date}}},
            {"$group": {
                "_id": {
                    "year": {"$year": "$created_at"},
                    "month": {"$month": "$created_at"},
                    "day": {"$dayOfMonth": "$created_at"}
                },
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]))
        
        # Format daily data
        formatted_daily = []
        for item in daily_properties:
            date_obj = datetime(item["_id"]["year"], item["_id"]["month"], item["_id"]["day"])
            formatted_daily.append({
                "date": date_obj.strftime("%Y-%m-%d"),
                "count": item["count"]
            })
        
        # Average property price
        avg_price_result = list(mongo.db.properties.aggregate([
            {"$group": {
                "_id": None,
                "avg_price": {"$avg": "$price"}
            }}
        ]))
        avg_price = round(avg_price_result[0]["avg_price"], 2) if avg_price_result else 0
        
        return jsonify({
            "total_properties": total_properties,
            "active_properties": active_properties,
            "new_properties": new_properties,
            "conversion_rate": round(conversion_rate, 2),
            "avg_price": avg_price,
            "properties_by_status": properties_by_status,
            "most_booked": most_booked,
            "daily_trend": formatted_daily,
            "period_days": days
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get property performance: {str(e)}"}), 500


# ============================================================================
# GEOGRAPHIC DISTRIBUTION
# ============================================================================

@analytics_bp.route("/geography/distribution", methods=["GET"])
@jwt_required()
@admin_only
def get_geographic_distribution():
    """Get geographic distribution of properties and searches"""
    try:
        # Properties by city
        properties_by_city = list(mongo.db.properties.aggregate([
            {"$group": {
                "_id": "$city",
                "count": {"$sum": 1},
                "avg_price": {"$avg": "$price"}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 20}
        ]))
        
        # Format data
        formatted_cities = []
        for item in properties_by_city:
            formatted_cities.append({
                "city": item["_id"] or "Unknown",
                "property_count": item["count"],
                "avg_price": round(item["avg_price"], 2)
            })
        
        # Properties by type
        properties_by_type = list(mongo.db.properties.aggregate([
            {"$group": {
                "_id": "$property_type",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]))
        
        # Most popular cities (by bookings)
        popular_cities = list(mongo.db.bookings.aggregate([
            {"$lookup": {
                "from": "properties",
                "localField": "property_id",
                "foreignField": "_id",
                "as": "property"
            }},
            {"$unwind": "$property"},
            {"$group": {
                "_id": "$property.city",
                "booking_count": {"$sum": 1}
            }},
            {"$sort": {"booking_count": -1}},
            {"$limit": 10}
        ]))
        
        formatted_popular = []
        for item in popular_cities:
            formatted_popular.append({
                "city": item["_id"] or "Unknown",
                "booking_count": item["booking_count"]
            })
        
        return jsonify({
            "properties_by_city": formatted_cities,
            "properties_by_type": properties_by_type,
            "popular_cities": formatted_popular
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get geographic distribution: {str(e)}"}), 500


# ============================================================================
# BOOKING TRENDS
# ============================================================================

@analytics_bp.route("/bookings/trends", methods=["GET"])
@jwt_required()
@admin_only
def get_booking_trends():
    """Get booking trends and statistics"""
    try:
        days = request.args.get("days", 30, type=int)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Total bookings
        total_bookings = mongo.db.bookings.count_documents({})
        period_bookings = mongo.db.bookings.count_documents({
            "created_at": {"$gte": start_date, "$lte": end_date}
        })
        
        # Bookings by status
        bookings_by_status = list(mongo.db.bookings.aggregate([
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }}
        ]))
        
        # Daily bookings trend
        daily_bookings = list(mongo.db.bookings.aggregate([
            {"$match": {"created_at": {"$gte": start_date, "$lte": end_date}}},
            {"$group": {
                "_id": {
                    "year": {"$year": "$created_at"},
                    "month": {"$month": "$created_at"},
                    "day": {"$dayOfMonth": "$created_at"}
                },
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]))
        
        # Format daily data
        formatted_daily = []
        for item in daily_bookings:
            date_obj = datetime(item["_id"]["year"], item["_id"]["month"], item["_id"]["day"])
            formatted_daily.append({
                "date": date_obj.strftime("%Y-%m-%d"),
                "count": item["count"]
            })
        
        # Conversion rate
        confirmed_bookings = mongo.db.bookings.count_documents({
            "status": "confirmed",
            "created_at": {"$gte": start_date, "$lte": end_date}
        })
        conversion_rate = (confirmed_bookings / period_bookings * 100) if period_bookings > 0 else 0
        
        return jsonify({
            "total_bookings": total_bookings,
            "period_bookings": period_bookings,
            "confirmed_bookings": confirmed_bookings,
            "conversion_rate": round(conversion_rate, 2),
            "bookings_by_status": bookings_by_status,
            "daily_trend": formatted_daily,
            "period_days": days
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get booking trends: {str(e)}"}), 500


# ============================================================================
# SUMMARY METRICS
# ============================================================================

@analytics_bp.route("/summary", methods=["GET"])
@jwt_required()
@admin_only
def get_analytics_summary():
    """Get comprehensive analytics summary"""
    try:
        days = request.args.get("days", 30, type=int)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get all key metrics
        total_users = mongo.db.users.count_documents({})
        total_properties = mongo.db.properties.count_documents({})
        total_bookings = mongo.db.bookings.count_documents({})
        
        new_users = mongo.db.users.count_documents({
            "created_at": {"$gte": start_date}
        })
        
        new_properties = mongo.db.properties.count_documents({
            "created_at": {"$gte": start_date}
        })
        
        new_bookings = mongo.db.bookings.count_documents({
            "created_at": {"$gte": start_date}
        })
        
        # Growth percentages
        prev_start = start_date - timedelta(days=days)
        prev_users = mongo.db.users.count_documents({
            "created_at": {"$gte": prev_start, "$lt": start_date}
        })
        user_growth = ((new_users - prev_users) / prev_users * 100) if prev_users > 0 else 100
        
        prev_properties = mongo.db.properties.count_documents({
            "created_at": {"$gte": prev_start, "$lt": start_date}
        })
        property_growth = ((new_properties - prev_properties) / prev_properties * 100) if prev_properties > 0 else 100
        
        prev_bookings = mongo.db.bookings.count_documents({
            "created_at": {"$gte": prev_start, "$lt": start_date}
        })
        booking_growth = ((new_bookings - prev_bookings) / prev_bookings * 100) if prev_bookings > 0 else 100
        
        return jsonify({
            "overview": {
                "total_users": total_users,
                "total_properties": total_properties,
                "total_bookings": total_bookings
            },
            "period_stats": {
                "new_users": new_users,
                "new_properties": new_properties,
                "new_bookings": new_bookings,
                "period_days": days
            },
            "growth": {
                "user_growth": round(user_growth, 2),
                "property_growth": round(property_growth, 2),
                "booking_growth": round(booking_growth, 2)
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get analytics summary: {str(e)}"}), 500