from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from extensions import mongo
from bson import ObjectId
from datetime import datetime
from utils.validators import validate_payment_data, validate_refund_data
from utils.decorators import admin_only, landlord_only, tenant_only
import os
import json
from utils.payment_gateways import (
    initiate_mpesa_stk_push, 
    query_mpesa_transaction_status,
    register_mpesa_urls,
    mpesa_b2c_payment
)

payment_bp = Blueprint("payment", __name__)

# ==================== PAYMENT ENDPOINTS ====================

@payment_bp.route("/create", methods=["POST"])
@jwt_required()
@tenant_only
def create_payment():
    """Create a new payment transaction"""
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        
        # Validate payment data
        is_valid, errors = validate_payment_data(data)
        if not is_valid:
            return jsonify({"error": "Validation failed", "details": errors}), 400
        
        # Verify property exists
        property_id = data.get("property_id")
        property_doc = mongo.db.properties.find_one({"_id": ObjectId(property_id)})
        if not property_doc:
            return jsonify({"error": "Property not found"}), 404
        
        # Verify booking exists (if booking_id provided)
        booking_id = data.get("booking_id")
        if booking_id:
            booking_doc = mongo.db.bookings.find_one({"_id": ObjectId(booking_id)})
            if not booking_doc:
                return jsonify({"error": "Booking not found"}), 404
            
            # Verify booking belongs to user
            if str(booking_doc.get("tenant_id")) != user_id:
                return jsonify({"error": "Unauthorized access to booking"}), 403
        
        # Create payment record
        payment_doc = {
            "tenant_id": ObjectId(user_id),
            "property_id": ObjectId(property_id),
            "landlord_id": property_doc.get("landlord_id"),
            "booking_id": ObjectId(booking_id) if booking_id else None,
            "amount": float(data["amount"]),
            "currency": data.get("currency", "USD"),
            "payment_type": data["payment_type"],  # deposit, rent, booking_fee
            "payment_method": data["payment_method"],  # card, bank_transfer, mpesa, paypal
            "status": "pending",  # pending, processing, completed, failed, refunded
            "transaction_id": None,  # Will be set by payment gateway
            "gateway_reference": None,
            "description": data.get("description", ""),
            "metadata": data.get("metadata", {}),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = mongo.db.payments.insert_one(payment_doc)
        payment_doc["_id"] = result.inserted_id
        
        # In test mode, auto-complete payment
        test_mode = os.getenv("PAYMENT_TEST_MODE", "True") == "True"
        if test_mode:
            payment_doc["status"] = "completed"
            payment_doc["transaction_id"] = f"TEST_{result.inserted_id}"
            payment_doc["gateway_reference"] = f"test_ref_{datetime.utcnow().timestamp()}"
            payment_doc["completed_at"] = datetime.utcnow()
            
            mongo.db.payments.update_one(
                {"_id": result.inserted_id},
                {"$set": {
                    "status": "completed",
                    "transaction_id": payment_doc["transaction_id"],
                    "gateway_reference": payment_doc["gateway_reference"],
                    "completed_at": payment_doc["completed_at"]
                }}
            )
        
        # Convert ObjectId to string for JSON response
        payment_doc["_id"] = str(payment_doc["_id"])
        payment_doc["tenant_id"] = str(payment_doc["tenant_id"])
        payment_doc["property_id"] = str(payment_doc["property_id"])
        payment_doc["landlord_id"] = str(payment_doc["landlord_id"])
        if payment_doc["booking_id"]:
            payment_doc["booking_id"] = str(payment_doc["booking_id"])
        
        return jsonify({
            "message": "Payment created successfully",
            "payment": payment_doc,
            "test_mode": test_mode
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@payment_bp.route("/process/<payment_id>", methods=["POST"])
@jwt_required()
@tenant_only
def process_payment(payment_id):
    """Process a pending payment (simulate payment gateway)"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        
        # Find payment
        payment = mongo.db.payments.find_one({"_id": ObjectId(payment_id)})
        if not payment:
            return jsonify({"error": "Payment not found"}), 404
        
        # Verify ownership
        if str(payment["tenant_id"]) != user_id:
            return jsonify({"error": "Unauthorized"}), 403
        
        # Check if already processed
        if payment["status"] != "pending":
            return jsonify({"error": f"Payment already {payment['status']}"}), 400
        
        # Update status to processing
        mongo.db.payments.update_one(
            {"_id": ObjectId(payment_id)},
            {"$set": {"status": "processing", "updated_at": datetime.utcnow()}}
        )
        
        # Simulate payment gateway processing
        # In production, this would integrate with Stripe, PayPal, M-Pesa, etc.
        test_mode = os.getenv("PAYMENT_TEST_MODE", "True") == "True"
        
        if test_mode:
            # Auto-succeed in test mode
            success = True
            transaction_id = f"TEST_{payment_id}_{datetime.utcnow().timestamp()}"
            gateway_ref = f"test_gateway_ref_{payment_id}"
        else:
            # Here you would integrate with actual payment gateway
            # Example: Stripe, PayPal, M-Pesa API calls
            success = data.get("simulate_success", True)
            transaction_id = data.get("transaction_id", f"TXN_{payment_id}")
            gateway_ref = data.get("gateway_reference", f"ref_{payment_id}")
        
        if success:
            # Payment successful
            update_data = {
                "status": "completed",
                "transaction_id": transaction_id,
                "gateway_reference": gateway_ref,
                "completed_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            mongo.db.payments.update_one(
                {"_id": ObjectId(payment_id)},
                {"$set": update_data}
            )
            
            # If this was a booking payment, update booking status
            if payment.get("booking_id"):
                mongo.db.bookings.update_one(
                    {"_id": payment["booking_id"]},
                    {"$set": {"payment_status": "paid", "updated_at": datetime.utcnow()}}
                )
            
            return jsonify({
                "message": "Payment processed successfully",
                "status": "completed",
                "transaction_id": transaction_id
            }), 200
        else:
            # Payment failed
            mongo.db.payments.update_one(
                {"_id": ObjectId(payment_id)},
                {"$set": {
                    "status": "failed",
                    "failure_reason": data.get("failure_reason", "Payment declined"),
                    "updated_at": datetime.utcnow()
                }}
            )
            
            return jsonify({
                "message": "Payment failed",
                "status": "failed",
                "reason": data.get("failure_reason", "Payment declined")
            }), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@payment_bp.route("/tenant/history", methods=["GET"])
@jwt_required()
@tenant_only
def get_tenant_payment_history():
    """Get payment history for logged-in tenant"""
    try:
        user_id = get_jwt_identity()
        
        # Get query parameters
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))
        status = request.args.get("status")  # Optional filter
        
        # Build query
        query = {"tenant_id": ObjectId(user_id)}
        if status:
            query["status"] = status
        
        # Get total count
        total = mongo.db.payments.count_documents(query)
        
        # Get payments with pagination
        payments = list(mongo.db.payments.find(query)
                       .sort("created_at", -1)
                       .skip((page - 1) * limit)
                       .limit(limit))
        
        # Enrich with property details
        for payment in payments:
            property_doc = mongo.db.properties.find_one(
                {"_id": payment["property_id"]},
                {"title": 1, "address": 1, "city": 1}
            )
            payment["property_details"] = property_doc if property_doc else None
            
            # Convert ObjectIds to strings
            payment["_id"] = str(payment["_id"])
            payment["tenant_id"] = str(payment["tenant_id"])
            payment["property_id"] = str(payment["property_id"])
            payment["landlord_id"] = str(payment["landlord_id"])
            if payment.get("booking_id"):
                payment["booking_id"] = str(payment["booking_id"])
        
        return jsonify({
            "payments": payments,
            "pagination": {
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@payment_bp.route("/landlord/history", methods=["GET"])
@jwt_required()
@landlord_only
def get_landlord_payment_history():
    """Get payment history for landlord's properties"""
    try:
        user_id = get_jwt_identity()
        
        # Get query parameters
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))
        status = request.args.get("status")
        property_id = request.args.get("property_id")
        
        # Build query
        query = {"landlord_id": ObjectId(user_id)}
        if status:
            query["status"] = status
        if property_id:
            query["property_id"] = ObjectId(property_id)
        
        # Get total count
        total = mongo.db.payments.count_documents(query)
        
        # Get payments
        payments = list(mongo.db.payments.find(query)
                       .sort("created_at", -1)
                       .skip((page - 1) * limit)
                       .limit(limit))
        
        # Enrich with tenant and property details
        for payment in payments:
            # Get tenant info
            tenant = mongo.db.users.find_one(
                {"_id": payment["tenant_id"]},
                {"name": 1, "email": 1}
            )
            payment["tenant_details"] = tenant if tenant else None
            
            # Get property info
            property_doc = mongo.db.properties.find_one(
                {"_id": payment["property_id"]},
                {"title": 1, "address": 1}
            )
            payment["property_details"] = property_doc if property_doc else None
            
            # Convert ObjectIds
            payment["_id"] = str(payment["_id"])
            payment["tenant_id"] = str(payment["tenant_id"])
            payment["property_id"] = str(payment["property_id"])
            payment["landlord_id"] = str(payment["landlord_id"])
            if payment.get("booking_id"):
                payment["booking_id"] = str(payment["booking_id"])
        
        return jsonify({
            "payments": payments,
            "pagination": {
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@payment_bp.route("/<payment_id>", methods=["GET"])
@jwt_required()
def get_payment_details(payment_id):
    """Get details of a specific payment"""
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        # Find payment
        payment = mongo.db.payments.find_one({"_id": ObjectId(payment_id)})
        if not payment:
            return jsonify({"error": "Payment not found"}), 404
        
        # Check authorization
        if role == "tenant" and str(payment["tenant_id"]) != user_id:
            return jsonify({"error": "Unauthorized"}), 403
        elif role == "landlord" and str(payment["landlord_id"]) != user_id:
            return jsonify({"error": "Unauthorized"}), 403
        
        # Enrich payment data
        property_doc = mongo.db.properties.find_one(
            {"_id": payment["property_id"]},
            {"title": 1, "address": 1, "city": 1}
        )
        payment["property_details"] = property_doc
        
        tenant = mongo.db.users.find_one(
            {"_id": payment["tenant_id"]},
            {"name": 1, "email": 1}
        )
        payment["tenant_details"] = tenant
        
        # Convert ObjectIds
        payment["_id"] = str(payment["_id"])
        payment["tenant_id"] = str(payment["tenant_id"])
        payment["property_id"] = str(payment["property_id"])
        payment["landlord_id"] = str(payment["landlord_id"])
        if payment.get("booking_id"):
            payment["booking_id"] = str(payment["booking_id"])
        
        return jsonify({"payment": payment}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@payment_bp.route("/refund/<payment_id>", methods=["POST"])
@jwt_required()
def request_refund(payment_id):
    """Request a refund for a payment"""
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        data = request.get_json()
        
        # Validate refund data
        is_valid, errors = validate_refund_data(data)
        if not is_valid:
            return jsonify({"error": "Validation failed", "details": errors}), 400
        
        # Find payment
        payment = mongo.db.payments.find_one({"_id": ObjectId(payment_id)})
        if not payment:
            return jsonify({"error": "Payment not found"}), 404
        
        # Check authorization (tenant can request, admin can approve)
        if role == "tenant" and str(payment["tenant_id"]) != user_id:
            return jsonify({"error": "Unauthorized"}), 403
        
        # Check if payment can be refunded
        if payment["status"] != "completed":
            return jsonify({"error": "Only completed payments can be refunded"}), 400
        
        # Check if already refunded
        if payment.get("refund_status") in ["refunded", "pending_refund"]:
            return jsonify({"error": "Refund already processed or pending"}), 400
        
        # Create refund request
        refund_amount = data.get("amount", payment["amount"])
        
        mongo.db.payments.update_one(
            {"_id": ObjectId(payment_id)},
            {"$set": {
                "refund_status": "pending_refund",
                "refund_amount": float(refund_amount),
                "refund_reason": data["reason"],
                "refund_requested_at": datetime.utcnow(),
                "refund_requested_by": ObjectId(user_id),
                "updated_at": datetime.utcnow()
            }}
        )
        
        return jsonify({
            "message": "Refund request submitted successfully",
            "refund_status": "pending_refund"
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@payment_bp.route("/refund/<payment_id>/approve", methods=["POST"])
@jwt_required()
@admin_only
def approve_refund(payment_id):
    """Approve a refund request (admin only)"""
    try:
        # Find payment
        payment = mongo.db.payments.find_one({"_id": ObjectId(payment_id)})
        if not payment:
            return jsonify({"error": "Payment not found"}), 404
        
        # Check if refund is pending
        if payment.get("refund_status") != "pending_refund":
            return jsonify({"error": "No pending refund request"}), 400
        
        # Process refund (in test mode, auto-approve)
        test_mode = os.getenv("PAYMENT_TEST_MODE", "True") == "True"
        
        if test_mode:
            refund_success = True
            refund_transaction_id = f"REFUND_TEST_{payment_id}"
        else:
            # Integrate with payment gateway for actual refund
            refund_success = True  # Placeholder
            refund_transaction_id = f"REFUND_{payment_id}"
        
        if refund_success:
            mongo.db.payments.update_one(
                {"_id": ObjectId(payment_id)},
                {"$set": {
                    "status": "refunded",
                    "refund_status": "refunded",
                    "refund_transaction_id": refund_transaction_id,
                    "refunded_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }}
            )
            
            return jsonify({
                "message": "Refund processed successfully",
                "refund_transaction_id": refund_transaction_id
            }), 200
        else:
            return jsonify({"error": "Refund processing failed"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@payment_bp.route("/stats", methods=["GET"])
@jwt_required()
def get_payment_stats():
    """Get payment statistics for user"""
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        if role == "tenant":
            query = {"tenant_id": ObjectId(user_id)}
        elif role == "landlord":
            query = {"landlord_id": ObjectId(user_id)}
        else:
            query = {}  # Admin sees all
        
        # Calculate statistics
        total_payments = mongo.db.payments.count_documents(query)
        completed = mongo.db.payments.count_documents({**query, "status": "completed"})
        pending = mongo.db.payments.count_documents({**query, "status": "pending"})
        failed = mongo.db.payments.count_documents({**query, "status": "failed"})
        refunded = mongo.db.payments.count_documents({**query, "status": "refunded"})
        
        # Calculate total amount
        pipeline = [
            {"$match": {**query, "status": "completed"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        total_amount_result = list(mongo.db.payments.aggregate(pipeline))
        total_amount = total_amount_result[0]["total"] if total_amount_result else 0
        
        return jsonify({
            "stats": {
                "total_payments": total_payments,
                "completed": completed,
                "pending": pending,
                "failed": failed,
                "refunded": refunded,
                "total_amount": total_amount
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    # ==================== M-PESA DARAJA API ROUTES ====================

@payment_bp.route("/mpesa/stk-push", methods=["POST"])
@jwt_required()
@tenant_only
def mpesa_stk_push():
    """
    Initiate M-Pesa STK Push payment
    User receives prompt on their phone to enter M-Pesa PIN
    """
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        
        # Get required fields
        payment_id = data.get("payment_id")
        phone_number = data.get("phone_number")
        
        if not payment_id or not phone_number:
            return jsonify({
                "error": "payment_id and phone_number are required"
            }), 400
        
        # Get payment record
        payment = mongo.db.payments.find_one({"_id": ObjectId(payment_id)})
        if not payment:
            return jsonify({"error": "Payment not found"}), 404
        
        # Verify ownership
        if str(payment["tenant_id"]) != user_id:
            return jsonify({"error": "Unauthorized"}), 403
        
        # Check if payment is pending
        if payment["status"] != "pending":
            return jsonify({
                "error": f"Payment is already {payment['status']}"
            }), 400
        
        # Get property details for reference
        property_doc = mongo.db.properties.find_one({"_id": payment["property_id"]})
        property_title = property_doc.get("title", "Property") if property_doc else "Property"
        
        # Initiate STK Push
        account_ref = f"PAY{str(payment['_id'])[:8]}"  # Max 12 chars
        description = f"{payment['payment_type'][:10]}"  # Max 13 chars
        
        result = initiate_mpesa_stk_push(
            phone_number=phone_number,
            amount=payment["amount"],
            account_reference=account_ref,
            description=description
        )
        
        if result["success"]:
            # Update payment with M-Pesa details
            mongo.db.payments.update_one(
                {"_id": ObjectId(payment_id)},
                {"$set": {
                    "status": "processing",
                    "payment_method": "mpesa",
                    "gateway_reference": result["checkout_request_id"],
                    "metadata.merchant_request_id": result["merchant_request_id"],
                    "metadata.mpesa_phone": phone_number,
                    "updated_at": datetime.utcnow()
                }}
            )
            
            return jsonify({
                "success": True,
                "message": "STK Push sent. Please check your phone and enter M-Pesa PIN",
                "checkout_request_id": result["checkout_request_id"],
                "merchant_request_id": result["merchant_request_id"],
                "customer_message": result.get("customer_message")
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": result["error"],
                "error_code": result.get("error_code")
            }), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@payment_bp.route("/mpesa/query/<payment_id>", methods=["GET"])
@jwt_required()
def query_mpesa_payment(payment_id):
    """
    Query M-Pesa payment status
    Check if customer completed the payment
    """
    try:
        user_id = get_jwt_identity()
        
        # Get payment
        payment = mongo.db.payments.find_one({"_id": ObjectId(payment_id)})
        if not payment:
            return jsonify({"error": "Payment not found"}), 404
        
        # Verify authorization
        claims = get_jwt()
        role = claims.get("role")
        
        if role == "tenant" and str(payment["tenant_id"]) != user_id:
            return jsonify({"error": "Unauthorized"}), 403
        elif role == "landlord" and str(payment["landlord_id"]) != user_id:
            return jsonify({"error": "Unauthorized"}), 403
        
        # Check if payment has M-Pesa reference
        checkout_request_id = payment.get("gateway_reference")
        if not checkout_request_id:
            return jsonify({
                "error": "No M-Pesa transaction reference found"
            }), 400
        
        # Query M-Pesa
        result = query_mpesa_transaction_status(checkout_request_id)
        
        if result["success"]:
            # Update payment status based on result
            if result["result_code"] == "0":
                # Payment successful
                mongo.db.payments.update_one(
                    {"_id": ObjectId(payment_id)},
                    {"$set": {
                        "status": "completed",
                        "transaction_id": checkout_request_id,
                        "completed_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                        "metadata.result_desc": result["result_desc"]
                    }}
                )
                
                # Update booking if exists
                if payment.get("booking_id"):
                    mongo.db.bookings.update_one(
                        {"_id": payment["booking_id"]},
                        {"$set": {"payment_status": "paid"}}
                    )
                
                return jsonify({
                    "success": True,
                    "status": "completed",
                    "message": "Payment completed successfully",
                    "result_desc": result["result_desc"]
                }), 200
            else:
                # Payment failed or cancelled
                mongo.db.payments.update_one(
                    {"_id": ObjectId(payment_id)},
                    {"$set": {
                        "status": "failed",
                        "failure_reason": result["result_desc"],
                        "updated_at": datetime.utcnow()
                    }}
                )
                
                return jsonify({
                    "success": False,
                    "status": "failed",
                    "message": result["result_desc"],
                    "result_code": result["result_code"]
                }), 400
        else:
            return jsonify({
                "success": False,
                "error": result["error"]
            }), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@payment_bp.route("/mpesa/callback", methods=["POST"])
def mpesa_callback():
    """
    M-Pesa callback endpoint
    Safaricom Daraja API calls this after payment completion
    """
    try:
        data = request.get_json()
        
        # Log the callback for debugging
        print("M-Pesa Callback received:", json.dumps(data, indent=2))
        
        # Extract callback data
        callback_data = data.get("Body", {}).get("stkCallback", {})
        result_code = callback_data.get("ResultCode")
        result_desc = callback_data.get("ResultDesc")
        checkout_request_id = callback_data.get("CheckoutRequestID")
        
        if not checkout_request_id:
            return jsonify({"ResultCode": 1, "ResultDesc": "Invalid callback data"}), 400
        
        # Find payment by checkout_request_id
        payment = mongo.db.payments.find_one({"gateway_reference": checkout_request_id})
        
        if not payment:
            print(f"Payment not found for CheckoutRequestID: {checkout_request_id}")
            return jsonify({"ResultCode": 1, "ResultDesc": "Payment not found"}), 404
        
        if result_code == 0:
            # Payment successful - extract metadata
            callback_metadata = callback_data.get("CallbackMetadata", {}).get("Item", [])
            
            mpesa_receipt = None
            phone_number = None
            amount = None
            
            for item in callback_metadata:
                if item.get("Name") == "MpesaReceiptNumber":
                    mpesa_receipt = item.get("Value")
                elif item.get("Name") == "PhoneNumber":
                    phone_number = item.get("Value")
                elif item.get("Name") == "Amount":
                    amount = item.get("Value")
            
            # Update payment to completed
            mongo.db.payments.update_one(
                {"_id": payment["_id"]},
                {"$set": {
                    "status": "completed",
                    "transaction_id": mpesa_receipt,
                    "completed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "metadata.mpesa_receipt": mpesa_receipt,
                    "metadata.mpesa_phone": phone_number,
                    "metadata.mpesa_amount": amount,
                    "metadata.result_desc": result_desc
                }}
            )
            
            # Update booking status if exists
            if payment.get("booking_id"):
                mongo.db.bookings.update_one(
                    {"_id": payment["booking_id"]},
                    {"$set": {
                        "payment_status": "paid",
                        "updated_at": datetime.utcnow()
                    }}
                )
            
            print(f"Payment {payment['_id']} completed successfully. Receipt: {mpesa_receipt}")
            
        else:
            # Payment failed or cancelled
            mongo.db.payments.update_one(
                {"_id": payment["_id"]},
                {"$set": {
                    "status": "failed",
                    "failure_reason": result_desc,
                    "updated_at": datetime.utcnow(),
                    "metadata.result_code": result_code
                }}
            )
            
            print(f"Payment {payment['_id']} failed. Reason: {result_desc}")
        
        # Send success response to Safaricom
        return jsonify({
            "ResultCode": 0,
            "ResultDesc": "Success"
        }), 200
        
    except Exception as e:
        print(f"M-Pesa callback error: {str(e)}")
        return jsonify({
            "ResultCode": 1,
            "ResultDesc": f"Error: {str(e)}"
        }), 500


@payment_bp.route("/mpesa/validation", methods=["POST"])
def mpesa_validation():
    """
    M-Pesa C2B validation endpoint
    Called by Safaricom to validate payment before processing
    """
    try:
        data = request.get_json()
        print("M-Pesa Validation:", json.dumps(data, indent=2))
        
        # You can add custom validation logic here
        # For example, check if the account number exists
        
        # Accept all payments for now
        return jsonify({
            "ResultCode": 0,
            "ResultDesc": "Accepted"
        }), 200
        
    except Exception as e:
        print(f"Validation error: {str(e)}")
        return jsonify({
            "ResultCode": 1,
            "ResultDesc": f"Rejected: {str(e)}"
        }), 400


@payment_bp.route("/mpesa/confirmation", methods=["POST"])
def mpesa_confirmation():
    """
    M-Pesa C2B confirmation endpoint
    Called by Safaricom after payment is processed
    """
    try:
        data = request.get_json()
        print("M-Pesa Confirmation:", json.dumps(data, indent=2))
        
        # Extract transaction details
        trans_id = data.get("TransID")
        trans_amount = data.get("TransAmount")
        business_short_code = data.get("BusinessShortCode")
        bill_ref_number = data.get("BillRefNumber")
        phone_number = data.get("MSISDN")
        
        # You can process the payment here
        # For example, find payment by bill reference and mark as paid
        
        return jsonify({
            "ResultCode": 0,
            "ResultDesc": "Success"
        }), 200
        
    except Exception as e:
        print(f"Confirmation error: {str(e)}")
        return jsonify({
            "ResultCode": 1,
            "ResultDesc": f"Error: {str(e)}"
        }), 500


@payment_bp.route("/mpesa/refund", methods=["POST"])
@jwt_required()
@admin_only
def mpesa_refund():
    """
    Process M-Pesa B2C refund (Business to Customer)
    Admin only - sends money back to customer
    """
    try:
        data = request.get_json()
        payment_id = data.get("payment_id")
        
        if not payment_id:
            return jsonify({"error": "payment_id is required"}), 400
        
        # Get payment
        payment = mongo.db.payments.find_one({"_id": ObjectId(payment_id)})
        if not payment:
            return jsonify({"error": "Payment not found"}), 404
        
        # Check if payment can be refunded
        if payment["status"] != "completed":
            return jsonify({"error": "Only completed payments can be refunded"}), 400
        
        if payment.get("refund_status") == "refunded":
            return jsonify({"error": "Payment already refunded"}), 400
        
        # Get phone number from payment metadata
        phone_number = payment.get("metadata", {}).get("mpesa_phone")
        if not phone_number:
            return jsonify({"error": "M-Pesa phone number not found in payment"}), 400
        
        # Process B2C refund
        refund_amount = payment.get("refund_amount", payment["amount"])
        
        result = mpesa_b2c_payment(
            phone_number=phone_number,
            amount=refund_amount,
            occasion="Refund",
            remarks=f"Refund for payment {str(payment['_id'])[:8]}"
        )
        
        if result["success"]:
            # Update payment status
            mongo.db.payments.update_one(
                {"_id": ObjectId(payment_id)},
                {"$set": {
                    "status": "refunded",
                    "refund_status": "refunded",
                    "refund_transaction_id": result["conversation_id"],
                    "refunded_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "metadata.refund_conversation_id": result["conversation_id"]
                }}
            )
            
            return jsonify({
                "success": True,
                "message": "Refund initiated successfully",
                "conversation_id": result["conversation_id"]
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": result["error"]
            }), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@payment_bp.route("/mpesa/register-urls", methods=["POST"])
@jwt_required()
@admin_only
def mpesa_register_urls():
    """
    Register M-Pesa callback URLs with Safaricom
    Admin only - should be called once during setup
    """
    try:
        result = register_mpesa_urls()
        
        if result["success"]:
            return jsonify({
                "success": True,
                "message": "M-Pesa URLs registered successfully",
                "response": result["response_description"]
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": result["error"]
            }), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500