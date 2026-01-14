import os
import requests
from datetime import datetime
import json
import base64

# ==================== STRIPE INTEGRATION ====================

def create_stripe_payment_intent(amount, currency="USD", metadata=None):
    """
    Create a Stripe Payment Intent
    Requires: pip install stripe
    """
    try:
        import stripe
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Stripe uses cents
            currency=currency.lower(),
            metadata=metadata or {},
            automatic_payment_methods={"enabled": True}
        )
        
        return {
            "success": True,
            "client_secret": intent.client_secret,
            "payment_intent_id": intent.id
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def confirm_stripe_payment(payment_intent_id):
    """Confirm a Stripe payment"""
    try:
        import stripe
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        return {
            "success": intent.status == "succeeded",
            "status": intent.status,
            "transaction_id": intent.id
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ==================== PAYPAL INTEGRATION ====================

def create_paypal_payment(amount, currency="USD", description="Payment"):
    """
    Create a PayPal payment
    Requires: pip install paypalrestsdk
    """
    try:
        import paypalrestsdk
        
        paypalrestsdk.configure({
            "mode": os.getenv("PAYPAL_MODE", "sandbox"),
            "client_id": os.getenv("PAYPAL_CLIENT_ID"),
            "client_secret": os.getenv("PAYPAL_CLIENT_SECRET")
        })
        
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "transactions": [{
                "amount": {
                    "total": str(amount),
                    "currency": currency
                },
                "description": description
            }],
            "redirect_urls": {
                "return_url": f"{os.getenv('BACKEND_URL')}/payments/paypal/success",
                "cancel_url": f"{os.getenv('BACKEND_URL')}/payments/paypal/cancel"
            }
        })
        
        if payment.create():
            approval_url = next(
                link.href for link in payment.links if link.rel == "approval_url"
            )
            return {
                "success": True,
                "payment_id": payment.id,
                "approval_url": approval_url
            }
        else:
            return {
                "success": False,
                "error": payment.error
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def execute_paypal_payment(payment_id, payer_id):
    """Execute an approved PayPal payment"""
    try:
        import paypalrestsdk
        
        payment = paypalrestsdk.Payment.find(payment_id)
        
        if payment.execute({"payer_id": payer_id}):
            return {
                "success": True,
                "transaction_id": payment.id,
                "status": payment.state
            }
        else:
            return {
                "success": False,
                "error": payment.error
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ==================== M-PESA DARAJA API INTEGRATION (Kenya) ====================

def get_mpesa_access_token():
    """Get M-Pesa Daraja API OAuth access token"""
    try:
        consumer_key = os.getenv("MPESA_CONSUMER_KEY")
        consumer_secret = os.getenv("MPESA_CONSUMER_SECRET")
        environment = os.getenv("MPESA_ENVIRONMENT", "sandbox")
        
        # API URLs
        if environment == "sandbox":
            api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        else:
            api_url = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        
        # Create authorization header
        credentials = base64.b64encode(f"{consumer_key}:{consumer_secret}".encode()).decode()
        
        headers = {
            "Authorization": f"Basic {credentials}"
        }
        
        response = requests.get(api_url, headers=headers)
        result = response.json()
        
        if response.status_code == 200:
            return {
                "success": True,
                "access_token": result.get("access_token")
            }
        else:
            return {
                "success": False,
                "error": result.get("errorMessage", "Failed to get access token")
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def initiate_mpesa_stk_push(phone_number, amount, account_reference, description):
    """
    Initiate M-Pesa STK Push (Lipa Na M-Pesa Online) using Daraja API
    
    Args:
        phone_number: Format 254XXXXXXXXX (Kenyan phone number)
        amount: Payment amount (minimum 1 KES)
        account_reference: Your reference (max 12 characters)
        description: Transaction description (max 13 characters)
    
    Returns:
        dict with success status and response data
    """
    try:
        # Get access token
        token_response = get_mpesa_access_token()
        if not token_response["success"]:
            return token_response
        
        access_token = token_response["access_token"]
        environment = os.getenv("MPESA_ENVIRONMENT", "sandbox")
        shortcode = os.getenv("MPESA_SHORTCODE")
        passkey = os.getenv("MPESA_PASSKEY")
        callback_url = os.getenv("MPESA_CALLBACK_URL", f"{os.getenv('BACKEND_URL', 'http://localhost:5000')}/payments/mpesa/callback")
        
        # API URL
        if environment == "sandbox":
            api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        else:
            api_url = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        
        # Generate timestamp and password
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password_str = f"{shortcode}{passkey}{timestamp}"
        password = base64.b64encode(password_str.encode()).decode()
        
        # Validate phone number format
        if not phone_number.startswith("254"):
            if phone_number.startswith("0"):
                phone_number = "254" + phone_number[1:]
            elif phone_number.startswith("+254"):
                phone_number = phone_number[1:]
            elif phone_number.startswith("7") or phone_number.startswith("1"):
                phone_number = "254" + phone_number
        
        # Request payload
        payload = {
            "BusinessShortCode": shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": phone_number,
            "PartyB": shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": callback_url,
            "AccountReference": account_reference[:12],  # Max 12 characters
            "TransactionDesc": description[:13]  # Max 13 characters
        }
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(api_url, json=payload, headers=headers)
        result = response.json()
        
        if result.get("ResponseCode") == "0":
            return {
                "success": True,
                "checkout_request_id": result.get("CheckoutRequestID"),
                "merchant_request_id": result.get("MerchantRequestID"),
                "response_description": result.get("ResponseDescription"),
                "customer_message": result.get("CustomerMessage")
            }
        else:
            return {
                "success": False,
                "error": result.get("ResponseDescription", "STK Push failed"),
                "error_code": result.get("ResponseCode"),
                "error_message": result.get("errorMessage")
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def query_mpesa_transaction_status(checkout_request_id):
    """
    Query M-Pesa STK Push transaction status using Daraja API
    
    Args:
        checkout_request_id: CheckoutRequestID from STK Push response
    
    Returns:
        dict with transaction status
    """
    try:
        # Get access token
        token_response = get_mpesa_access_token()
        if not token_response["success"]:
            return token_response
        
        access_token = token_response["access_token"]
        environment = os.getenv("MPESA_ENVIRONMENT", "sandbox")
        shortcode = os.getenv("MPESA_SHORTCODE")
        passkey = os.getenv("MPESA_PASSKEY")
        
        # API URL
        if environment == "sandbox":
            api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query"
        else:
            api_url = "https://api.safaricom.co.ke/mpesa/stkpushquery/v1/query"
        
        # Generate timestamp and password
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password_str = f"{shortcode}{passkey}{timestamp}"
        password = base64.b64encode(password_str.encode()).decode()
        
        # Request payload
        payload = {
            "BusinessShortCode": shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id
        }
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(api_url, json=payload, headers=headers)
        result = response.json()
        
        if result.get("ResponseCode") == "0":
            return {
                "success": True,
                "result_code": result.get("ResultCode"),
                "result_desc": result.get("ResultDesc"),
                "status": "completed" if result.get("ResultCode") == "0" else "failed"
            }
        else:
            return {
                "success": False,
                "error": result.get("ResponseDescription", "Query failed"),
                "error_code": result.get("ResponseCode")
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def register_mpesa_urls():
    """
    Register M-Pesa C2B URLs for payment notifications
    This should be called once during application setup
    """
    try:
        # Get access token
        token_response = get_mpesa_access_token()
        if not token_response["success"]:
            return token_response
        
        access_token = token_response["access_token"]
        environment = os.getenv("MPESA_ENVIRONMENT", "sandbox")
        shortcode = os.getenv("MPESA_SHORTCODE")
        
        # API URL
        if environment == "sandbox":
            api_url = "https://sandbox.safaricom.co.ke/mpesa/c2b/v1/registerurl"
        else:
            api_url = "https://api.safaricom.co.ke/mpesa/c2b/v1/registerurl"
        
        # URLs
        validation_url = f"{os.getenv('BACKEND_URL', 'http://localhost:5000')}/payments/mpesa/validation"
        confirmation_url = f"{os.getenv('BACKEND_URL', 'http://localhost:5000')}/payments/mpesa/confirmation"
        
        payload = {
            "ShortCode": shortcode,
            "ResponseType": "Completed",  # or "Cancelled"
            "ConfirmationURL": confirmation_url,
            "ValidationURL": validation_url
        }
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(api_url, json=payload, headers=headers)
        result = response.json()
        
        if result.get("ResponseCode") == "0":
            return {
                "success": True,
                "response_description": result.get("ResponseDescription")
            }
        else:
            return {
                "success": False,
                "error": result.get("ResponseDescription", "URL registration failed")
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def mpesa_b2c_payment(phone_number, amount, occasion, remarks):
    """
    Make M-Pesa B2C (Business to Customer) payment - sending money to customer
    
    Args:
        phone_number: Format 254XXXXXXXXX
        amount: Amount to send (minimum 10 KES)
        occasion: Occasion for payment
        remarks: Payment remarks
    """
    try:
        # Get access token
        token_response = get_mpesa_access_token()
        if not token_response["success"]:
            return token_response
        
        access_token = token_response["access_token"]
        environment = os.getenv("MPESA_ENVIRONMENT", "sandbox")
        initiator_name = os.getenv("MPESA_INITIATOR_NAME")
        security_credential = os.getenv("MPESA_SECURITY_CREDENTIAL")
        shortcode = os.getenv("MPESA_SHORTCODE")
        
        # API URL
        if environment == "sandbox":
            api_url = "https://sandbox.safaricom.co.ke/mpesa/b2c/v1/paymentrequest"
        else:
            api_url = "https://api.safaricom.co.ke/mpesa/b2c/v1/paymentrequest"
        
        # Validate phone number
        if not phone_number.startswith("254"):
            if phone_number.startswith("0"):
                phone_number = "254" + phone_number[1:]
        
        payload = {
            "InitiatorName": initiator_name,
            "SecurityCredential": security_credential,
            "CommandID": "BusinessPayment",  # or "SalaryPayment", "PromotionPayment"
            "Amount": int(amount),
            "PartyA": shortcode,
            "PartyB": phone_number,
            "Remarks": remarks,
            "QueueTimeOutURL": f"{os.getenv('BACKEND_URL')}/payments/mpesa/b2c/timeout",
            "ResultURL": f"{os.getenv('BACKEND_URL')}/payments/mpesa/b2c/result",
            "Occasion": occasion
        }
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(api_url, json=payload, headers=headers)
        result = response.json()
        
        if result.get("ResponseCode") == "0":
            return {
                "success": True,
                "conversation_id": result.get("ConversationID"),
                "originator_conversation_id": result.get("OriginatorConversationID"),
                "response_description": result.get("ResponseDescription")
            }
        else:
            return {
                "success": False,
                "error": result.get("ResponseDescription", "B2C payment failed")
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ==================== FLUTTERWAVE INTEGRATION ====================

def create_flutterwave_payment(amount, currency, email, phone, name, reference=None):
    """
    Create Flutterwave payment using direct API requests
    Compatible with Python 3.14+
    """
    try:
        url = "https://api.flutterwave.com/v3/payments"
        
        if not reference:
            reference = f"TXN_{int(datetime.now().timestamp() * 1000)}"
        
        headers = {
            "Authorization": f"Bearer {os.getenv('FLUTTERWAVE_SECRET_KEY')}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "tx_ref": reference,
            "amount": str(amount),
            "currency": currency,
            "redirect_url": f"{os.getenv('BACKEND_URL', 'http://localhost:5000')}/payments/flutterwave/callback",
            "payment_options": "card,mobilemoney,ussd,banktransfer",
            "customer": {
                "email": email,
                "phonenumber": phone,
                "name": name
            },
            "customizations": {
                "title": "Property Payment",
                "description": "Payment for property rental/booking",
                "logo": ""
            }
        }
        
        response = requests.post(url, json=payload, headers=headers)
        result = response.json()
        
        if result.get("status") == "success":
            return {
                "success": True,
                "payment_link": result["data"]["link"],
                "tx_ref": reference
            }
        else:
            return {
                "success": False,
                "error": result.get("message", "Unknown error")
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def verify_flutterwave_payment(transaction_id):
    """
    Verify Flutterwave payment using direct API request
    Compatible with Python 3.14+
    """
    try:
        url = f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify"
        
        headers = {
            "Authorization": f"Bearer {os.getenv('FLUTTERWAVE_SECRET_KEY')}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        result = response.json()
        
        if result.get("status") == "success":
            data = result.get("data", {})
            if data.get("status") == "successful":
                return {
                    "success": True,
                    "amount": data.get("amount"),
                    "currency": data.get("currency"),
                    "transaction_id": data.get("id"),
                    "tx_ref": data.get("tx_ref"),
                    "flw_ref": data.get("flw_ref"),
                    "charged_amount": data.get("charged_amount")
                }
        
        return {
            "success": False,
            "error": result.get("message", "Payment verification failed")
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ==================== PAYSTACK INTEGRATION ====================

def initialize_paystack_payment(email, amount, currency="NGN"):
    """
    Initialize Paystack payment
    """
    try:
        url = "https://api.paystack.co/transaction/initialize"
        
        headers = {
            "Authorization": f"Bearer {os.getenv('PAYSTACK_SECRET_KEY')}",
            "Content-Type": "application/json"
        }
        
        data = {
            "email": email,
            "amount": int(amount * 100),  # Paystack uses kobo (for NGN)
            "currency": currency,
            "callback_url": f"{os.getenv('BACKEND_URL')}/payments/paystack/callback"
        }
        
        response = requests.post(url, json=data, headers=headers)
        result = response.json()
        
        if result.get("status"):
            return {
                "success": True,
                "authorization_url": result["data"]["authorization_url"],
                "access_code": result["data"]["access_code"],
                "reference": result["data"]["reference"]
            }
        else:
            return {
                "success": False,
                "error": result.get("message", "Unknown error")
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def verify_paystack_payment(reference):
    """Verify Paystack payment"""
    try:
        url = f"https://api.paystack.co/transaction/verify/{reference}"
        
        headers = {
            "Authorization": f"Bearer {os.getenv('PAYSTACK_SECRET_KEY')}"
        }
        
        response = requests.get(url, headers=headers)
        result = response.json()
        
        if result.get("status") and result["data"]["status"] == "success":
            return {
                "success": True,
                "amount": result["data"]["amount"] / 100,  # Convert from kobo
                "transaction_id": result["data"]["id"],
                "reference": result["data"]["reference"]
            }
        else:
            return {
                "success": False,
                "error": result.get("message", "Payment verification failed")
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }