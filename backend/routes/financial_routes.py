# backend/routes/financial_routes.py
"""
Financial Routes - Admin Financial Management
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from extensions import mongo
from utils.decorators import admin_only
from bson import ObjectId
from datetime import datetime, timedelta

financial_bp = Blueprint("financial", __name__)

# ============================================================================
# FINANCIAL OVERVIEW
# ============================================================================

@financial_bp.route("/overview", methods=["GET"])
@jwt_required()
@admin_only
def get_financial_overview():
    """Get comprehensive financial overview"""
    try:
        days = request.args.get("days", 30, type=int)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # ===== SUBSCRIPTION REVENUE =====
        subscription_pipeline = [
            {
                "$match": {
                    "type": "subscription",
                    "status": "completed",
                    "completed_at": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": "$tier",
                    "revenue": {"$sum": "$amount"},
                    "count": {"$sum": 1}
                }
            }
        ]
        
        subscription_revenue = list(mongo.db.payments.aggregate(subscription_pipeline))
        
        total_subscription_revenue = sum(item["revenue"] for item in subscription_revenue)
        
        # ===== COMMISSION REVENUE =====
        # Calculate estimated commission from confirmed bookings
        commission_pipeline = [
            {
                "$match": {
                    "status": "confirmed",
                    "created_at": {"$gte": start_date, "$lte": end_date}
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
                "$lookup": {
                    "from": "users",
                    "localField": "landlord_id",
                    "foreignField": "_id",
                    "as": "landlord"
                }
            },
            {"$unwind": "$landlord"},
            {
                "$group": {
                    "_id": "$landlord.subscription.tier",
                    "bookings": {"$sum": 1},
                    "avg_property_price": {"$avg": "$property.price"}
                }
            }
        ]
        
        commission_data = list(mongo.db.bookings.aggregate(commission_pipeline))
        
        # Calculate commission based on tier rates
        from routes.subscription_routes import SUBSCRIPTION_TIERS
        
        total_commission = 0
        commission_breakdown = []
        
        for item in commission_data:
            tier = item["_id"] or "free"
            commission_rate = SUBSCRIPTION_TIERS.get(tier, SUBSCRIPTION_TIERS["free"])["commission_rate"]
            # Estimate: Assume average rent is 1 month = property price
            estimated_commission = (item["avg_property_price"] * commission_rate / 100) * item["bookings"]
            total_commission += estimated_commission
            
            commission_breakdown.append({
                "tier": tier,
                "bookings": item["bookings"],
                "commission_rate": commission_rate,
                "estimated_revenue": round(estimated_commission, 2)
            })
        
        # ===== ACTIVE SUBSCRIPTIONS =====
        active_subscriptions = {}
        for tier in ["free", "basic", "premium"]:
            count = mongo.db.users.count_documents({
                "role": "landlord",
                "subscription.tier": tier,
                "subscription.status": "active"
            })
            active_subscriptions[tier] = count
        
        # ===== MONTHLY RECURRING REVENUE (MRR) =====
        mrr_pipeline = [
            {
                "$match": {
                    "role": "landlord",
                    "subscription.status": "active",
                    "subscription.tier": {"$in": ["basic", "premium"]},
                    "subscription.billing_cycle": "monthly"
                }
            },
            {
                "$group": {
                    "_id": "$subscription.tier",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        mrr_data = list(mongo.db.users.aggregate(mrr_pipeline))
        
        mrr = 0
        for item in mrr_data:
            tier = item["_id"]
            count = item["count"]
            tier_price = SUBSCRIPTION_TIERS[tier]["price"]
            mrr += tier_price * count
        
        # ===== DAILY REVENUE TREND =====
        daily_revenue = list(mongo.db.payments.aggregate([
            {
                "$match": {
                    "status": "completed",
                    "completed_at": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": {
                        "year": {"$year": "$completed_at"},
                        "month": {"$month": "$completed_at"},
                        "day": {"$dayOfMonth": "$completed_at"}
                    },
                    "revenue": {"$sum": "$amount"}
                }
            },
            {"$sort": {"_id": 1}}
        ]))
        
        # Format daily data
        formatted_daily = []
        for item in daily_revenue:
            date_obj = datetime(item["_id"]["year"], item["_id"]["month"], item["_id"]["day"])
            formatted_daily.append({
                "date": date_obj.strftime("%Y-%m-%d"),
                "revenue": round(item["revenue"], 2)
            })
        
        # ===== TOTAL REVENUE =====
        total_revenue = total_subscription_revenue + total_commission
        
        return jsonify({
            "summary": {
                "total_revenue": round(total_revenue, 2),
                "subscription_revenue": round(total_subscription_revenue, 2),
                "commission_revenue": round(total_commission, 2),
                "mrr": round(mrr, 2),
                "period_days": days
            },
            "subscription_breakdown": subscription_revenue,
            "commission_breakdown": commission_breakdown,
            "active_subscriptions": active_subscriptions,
            "daily_trend": formatted_daily
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get financial overview: {str(e)}"}), 500


# ============================================================================
# SUBSCRIPTION ANALYTICS
# ============================================================================

@financial_bp.route("/subscriptions/analytics", methods=["GET"])
@jwt_required()
@admin_only
def get_subscription_analytics():
    """Get detailed subscription analytics"""
    try:
        # Subscriptions by tier
        tier_distribution = list(mongo.db.users.aggregate([
            {"$match": {"role": "landlord"}},
            {
                "$group": {
                    "_id": "$subscription.tier",
                    "count": {"$sum": 1}
                }
            }
        ]))
        
        # New subscriptions (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        new_subscriptions = list(mongo.db.payments.aggregate([
            {
                "$match": {
                    "type": "subscription",
                    "status": "completed",
                    "completed_at": {"$gte": thirty_days_ago}
                }
            },
            {
                "$group": {
                    "_id": "$tier",
                    "count": {"$sum": 1},
                    "revenue": {"$sum": "$amount"}
                }
            }
        ]))
        
        # Churn rate (cancelled subscriptions)
        cancelled = mongo.db.users.count_documents({
            "role": "landlord",
            "subscription.cancel_at_period_end": True
        })
        
        total_paid = mongo.db.users.count_documents({
            "role": "landlord",
            "subscription.tier": {"$in": ["basic", "premium"]}
        })
        
        churn_rate = (cancelled / total_paid * 100) if total_paid > 0 else 0
        
        # Expiring soon (next 7 days)
        seven_days_later = datetime.utcnow() + timedelta(days=7)
        expiring_soon = mongo.db.users.count_documents({
            "role": "landlord",
            "subscription.expires_at": {
                "$gte": datetime.utcnow(),
                "$lte": seven_days_later
            },
            "subscription.auto_renew": False
        })
        
        return jsonify({
            "tier_distribution": tier_distribution,
            "new_subscriptions": new_subscriptions,
            "churn_rate": round(churn_rate, 2),
            "expiring_soon": expiring_soon,
            "total_paid_subscribers": total_paid
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get subscription analytics: {str(e)}"}), 500


# ============================================================================
# ALL TRANSACTIONS
# ============================================================================

@financial_bp.route("/transactions", methods=["GET"])
@jwt_required()
@admin_only
def get_all_transactions():
    """Get all financial transactions"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        transaction_type = request.args.get("type")
        status = request.args.get("status")
        
        query = {}
        
        if transaction_type:
            query["type"] = transaction_type
        
        if status:
            query["status"] = status
        
        total_count = mongo.db.payments.count_documents(query)
        
        skip = (page - 1) * per_page
        transactions = list(mongo.db.payments.find(query)
                          .sort("created_at", -1)
                          .skip(skip)
                          .limit(per_page))
        
        # Enrich with landlord details
        for txn in transactions:
            landlord = mongo.db.users.find_one(
                {"_id": ObjectId(txn["landlord_id"])},
                {"email": 1}
            )
            
            txn["_id"] = str(txn["_id"])
            txn["landlord_id"] = str(txn["landlord_id"])
            txn["landlord_email"] = landlord["email"] if landlord else "Unknown"
            
            if txn.get("created_at"):
                txn["created_at"] = txn["created_at"].isoformat()
            if txn.get("completed_at"):
                txn["completed_at"] = txn["completed_at"].isoformat()
        
        return jsonify({
            "transactions": transactions,
            "count": len(transactions),
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "total_pages": (total_count + per_page - 1) // per_page
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get transactions: {str(e)}"}), 500


# ============================================================================
# REVENUE REPORT
# ============================================================================

@financial_bp.route("/report", methods=["GET"])
@jwt_required()
@admin_only
def get_revenue_report():
    """Generate comprehensive revenue report"""
    try:
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        
        if start_date_str and end_date_str:
            start_date = datetime.fromisoformat(start_date_str)
            end_date = datetime.fromisoformat(end_date_str)
        else:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
        
        # Total revenue in period
        total_revenue_result = list(mongo.db.payments.aggregate([
            {
                "$match": {
                    "status": "completed",
                    "completed_at": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": "$amount"},
                    "count": {"$sum": 1}
                }
            }
        ]))
        
        total_revenue = total_revenue_result[0]["total"] if total_revenue_result else 0
        transaction_count = total_revenue_result[0]["count"] if total_revenue_result else 0
        
        # Revenue by type
        revenue_by_type = list(mongo.db.payments.aggregate([
            {
                "$match": {
                    "status": "completed",
                    "completed_at": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": "$type",
                    "revenue": {"$sum": "$amount"},
                    "count": {"$sum": 1}
                }
            }
        ]))
        
        # Top paying landlords
        top_landlords = list(mongo.db.payments.aggregate([
            {
                "$match": {
                    "status": "completed",
                    "completed_at": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": "$landlord_id",
                    "total_paid": {"$sum": "$amount"},
                    "transaction_count": {"$sum": 1}
                }
            },
            {"$sort": {"total_paid": -1}},
            {"$limit": 10}
        ]))
        
        # Enrich with landlord emails
        for landlord in top_landlords:
            user = mongo.db.users.find_one(
                {"_id": ObjectId(landlord["_id"])},
                {"email": 1}
            )
            landlord["landlord_id"] = str(landlord.pop("_id"))
            landlord["email"] = user["email"] if user else "Unknown"
        
        return jsonify({
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "summary": {
                "total_revenue": round(total_revenue, 2),
                "transaction_count": transaction_count,
                "average_transaction": round(total_revenue / transaction_count, 2) if transaction_count > 0 else 0
            },
            "revenue_by_type": revenue_by_type,
            "top_landlords": top_landlords
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to generate report: {str(e)}"}), 500