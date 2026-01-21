# backend/routes/mpesa_routes.py
"""
M-Pesa Payment Routes
Handle subscription payments via M-Pesa
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import mongo
from bson import ObjectId
from datetime import datetime
from utils.mpesa import MPesaClient, handle_mpesa_callback, format_phone_number
from utils.decorators import landlord_only

mpesa_bp = Blueprint("mpesa", __name__)

# ============================================================================
# INITIATE PAYMENT
# ============================================================================

@mpesa_bp.route("/initiate-payment", methods=["POST"])
@jwt_required()
@landlord_only
def initiate_mpesa_payment():
    """
    Initiate M-Pesa STK Push for subscription payment
    
    Request body:
    {
        "payment_id": "payment_id_from_subscription",
        "phone_number": "0712345678"
    }
    """
    try:
        landlord_id = get_jwt_identity()
        data = request.get_json()
        
        payment_id = data.get('payment_id')
        phone_number = data.get('phone_number')
        
        if not payment_id or not phone_number:
            return jsonify({"error": "Payment ID and phone number required"}), 400
        
        # Validate payment
        if not ObjectId.is_valid(payment_id):
            return jsonify({"error": "Invalid payment ID"}), 400
        
        payment = mongo.db.payments.find_one({
            "_id": ObjectId(payment_id),
            "landlord_id": landlord_id,
            "type": "subscription",
            "status": "pending"
        })
        
        if not payment:
            return jsonify({"error": "Payment not found or already processed"}), 404
        
        # Format phone number
        try:
            formatted_phone = format_phone_number(phone_number)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        
        # Initialize M-Pesa client
        mpesa = MPesaClient()
        
        # Initiate STK Push
        amount = int(payment['amount'])
        account_reference = payment_id[:10]  # Use part of payment ID
        transaction_desc = f"{payment['tier'].title()} Subscription"
        
        stk_response = mpesa.stk_push(
            phone_number=formatted_phone,
            amount=amount,
            account_reference=account_reference,
            transaction_desc=transaction_desc
        )
        
        # Check if STK Push was successful
        if stk_response.get('ResponseCode') == '0':
            # Update payment with M-Pesa details
            mongo.db.payments.update_one(
                {"_id": ObjectId(payment_id)},
                {"$set": {
                    "mpesa_checkout_request_id": stk_response.get('CheckoutRequestID'),
                    "mpesa_merchant_request_id": stk_response.get('MerchantRequestID'),
                    "status": "processing",
                    "phone_number": formatted_phone,
                    "stk_push_initiated_at": datetime.utcnow()
                }}
            )
            
            print(f"✅ STK Push initiated for payment {payment_id}")
            
            return jsonify({
                "message": "Payment request sent to your phone. Please enter your M-Pesa PIN.",
                "checkout_request_id": stk_response.get('CheckoutRequestID'),
                "merchant_request_id": stk_response.get('MerchantRequestID')
            }), 200
        else:
            return jsonify({
                "error": "Failed to initiate payment",
                "details": stk_response.get('ResponseDescription', 'Unknown error')
            }), 400
        
    except Exception as e:
        print(f"❌ Error initiating M-Pesa payment: {str(e)}")
        return jsonify({"error": f"Payment initiation failed: {str(e)}"}), 500


# ============================================================================
# CHECK PAYMENT STATUS
# ============================================================================

@mpesa_bp.route("/check-status/<payment_id>", methods=["GET"])
@jwt_required()
@landlord_only
def check_payment_status(payment_id):
    """Check the status of a payment"""
    try:
        landlord_id = get_jwt_identity()
        
        if not ObjectId.is_valid(payment_id):
            return jsonify({"error": "Invalid payment ID"}), 400
        
        payment = mongo.db.payments.find_one({
            "_id": ObjectId(payment_id),
            "landlord_id": landlord_id
        })
        
        if not payment:
            return jsonify({"error": "Payment not found"}), 404
        
        # If payment has checkout request ID, query M-Pesa
        if payment.get('mpesa_checkout_request_id') and payment['status'] == 'processing':
            mpesa = MPesaClient()
            
            try:
                query_result = mpesa.query_transaction(payment['mpesa_checkout_request_id'])
                
                # Update payment status based on query result
                result_code = query_result.get('ResultCode')
                
                if result_code == '0':
                    # Payment successful
                    mongo.db.payments.update_one(
                        {"_id": ObjectId(payment_id)},
                        {"$set": {
                            "status": "completed",
                            "completed_at": datetime.utcnow(),
                            "mpesa_result": query_result
                        }}
                    )
                    
                    # Activate subscription
                    activate_subscription(landlord_id, payment)
                    
                    return jsonify({
                        "status": "completed",
                        "message": "Payment successful"
                    }), 200
                elif result_code == '1032':
                    # User cancelled
                    mongo.db.payments.update_one(
                        {"_id": ObjectId(payment_id)},
                        {"$set": {
                            "status": "cancelled",
                            "cancelled_at": datetime.utcnow()
                        }}
                    )
                    return jsonify({
                        "status": "cancelled",
                        "message": "Payment cancelled by user"
                    }), 200
                else:
                    # Still processing or failed
                    return jsonify({
                        "status": payment['status'],
                        "message": query_result.get('ResultDesc', 'Processing...')
                    }), 200
                    
            except Exception as e:
                print(f"Error querying M-Pesa: {str(e)}")
        
        # Return current status
        return jsonify({
            "status": payment['status'],
            "amount": payment['amount'],
            "tier": payment.get('tier'),
            "created_at": payment['created_at'].isoformat() if payment.get('created_at') else None
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to check status: {str(e)}"}), 500


# ============================================================================
# M-PESA CALLBACK (WEBHOOK)
# ============================================================================

@mpesa_bp.route("/callback", methods=["POST"])
def mpesa_callback():
    """
    Receive M-Pesa payment callbacks
    This endpoint is called by Safaricom when payment is completed
    """
    try:
        callback_data = request.get_json()
        
        print(f"📥 M-Pesa Callback received: {callback_data}")
        
        # Parse callback
        parsed = handle_mpesa_callback(callback_data)
        
        checkout_request_id = parsed['checkout_request_id']
        
        # Find payment by checkout request ID
        payment = mongo.db.payments.find_one({
            "mpesa_checkout_request_id": checkout_request_id
        })
        
        if not payment:
            print(f"❌ Payment not found for checkout request: {checkout_request_id}")
            return jsonify({"ResultCode": 1, "ResultDesc": "Payment not found"}), 404
        
        payment_id = str(payment['_id'])
        landlord_id = payment['landlord_id']
        
        if parsed['success']:
            # Payment successful
            mongo.db.payments.update_one(
                {"_id": ObjectId(payment_id)},
                {"$set": {
                    "status": "completed",
                    "completed_at": datetime.utcnow(),
                    "mpesa_receipt_number": parsed['mpesa_receipt'],
                    "mpesa_transaction_date": parsed['transaction_date'],
                    "mpesa_phone_number": parsed['phone_number'],
                    "mpesa_callback_data": callback_data
                }}
            )
            
            # Activate subscription
            activate_subscription(landlord_id, payment)
            
            print(f"✅ Payment completed: {payment_id}")
            
        else:
            # Payment failed
            mongo.db.payments.update_one(
                {"_id": ObjectId(payment_id)},
                {"$set": {
                    "status": "failed",
                    "failed_at": datetime.utcnow(),
                    "failure_reason": parsed['result_desc'],
                    "mpesa_callback_data": callback_data
                }}
            )
            
            print(f"❌ Payment failed: {payment_id} - {parsed['result_desc']}")
        
        # Acknowledge receipt
        return jsonify({"ResultCode": 0, "ResultDesc": "Success"}), 200
        
    except Exception as e:
        print(f"❌ Error handling callback: {str(e)}")
        return jsonify({"ResultCode": 1, "ResultDesc": str(e)}), 500


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def activate_subscription(landlord_id, payment):
    """Activate subscription after successful payment"""
    try:
        subscription = {
            "tier": payment["tier"],
            "status": "active",
            "billing_cycle": payment["billing_cycle"],
            "started_at": payment["subscription_period"]["start"],
            "expires_at": payment["subscription_period"]["end"],
            "auto_renew": True,
            "last_payment_id": str(payment["_id"]),
            "last_payment_date": datetime.utcnow()
        }
        
        mongo.db.users.update_one(
            {"_id": ObjectId(landlord_id)},
            {"$set": {"subscription": subscription}}
        )
        
        print(f"✅ Subscription activated for landlord: {landlord_id}")
        
        # TODO: Send confirmation email/notification
        
    except Exception as e:
        print(f"❌ Error activating subscription: {str(e)}")
        raise