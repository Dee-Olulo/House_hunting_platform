# backend/utils/mpesa.py
"""
M-Pesa Daraja API Integration
STK Push (Lipa Na M-Pesa Online)
"""

import requests
import base64
from datetime import datetime
from flask import current_app
import json

class MPesaClient:
    """M-Pesa Daraja API Client"""
    
    def __init__(self):
        # Get credentials from environment variables
        self.consumer_key = current_app.config.get('MPESA_CONSUMER_KEY')
        self.consumer_secret = current_app.config.get('MPESA_CONSUMER_SECRET')
        self.shortcode = current_app.config.get('MPESA_SHORTCODE')
        self.passkey = current_app.config.get('MPESA_PASSKEY')
        self.callback_url = current_app.config.get('MPESA_CALLBACK_URL')
        
        # API URLs
        self.environment = current_app.config.get('MPESA_ENVIRONMENT', 'sandbox')
        if self.environment == 'production':
            self.base_url = 'https://api.safaricom.co.ke'
        else:
            self.base_url = 'https://sandbox.safaricom.co.ke'
    
    def get_access_token(self):
        """Get OAuth access token from M-Pesa API"""
        try:
            url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
            
            # Create basic auth string
            auth_string = f"{self.consumer_key}:{self.consumer_secret}"
            auth_bytes = auth_string.encode('ascii')
            auth_base64 = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                'Authorization': f'Basic {auth_base64}'
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            return result['access_token']
            
        except Exception as e:
            print(f"❌ Error getting access token: {str(e)}")
            raise
    
    def generate_password(self):
        """Generate password for STK Push"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        data_to_encode = f"{self.shortcode}{self.passkey}{timestamp}"
        encoded = base64.b64encode(data_to_encode.encode()).decode('utf-8')
        return encoded, timestamp
    
    def stk_push(self, phone_number, amount, account_reference, transaction_desc):
        """
        Initiate STK Push (Lipa Na M-Pesa Online)
        
        Args:
            phone_number (str): Phone number in format 254XXXXXXXXX
            amount (int): Amount to charge
            account_reference (str): Account reference (e.g., payment_id)
            transaction_desc (str): Transaction description
        
        Returns:
            dict: Response from M-Pesa API
        """
        try:
            # Get access token
            access_token = self.get_access_token()
            
            # Generate password and timestamp
            password, timestamp = self.generate_password()
            
            # Prepare request
            url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'BusinessShortCode': self.shortcode,
                'Password': password,
                'Timestamp': timestamp,
                'TransactionType': 'CustomerPayBillOnline',
                'Amount': int(amount),
                'PartyA': phone_number,  # Customer phone number
                'PartyB': self.shortcode,  # Your paybill/till number
                'PhoneNumber': phone_number,  # Phone number to receive prompt
                'CallBackURL': self.callback_url,
                'AccountReference': account_reference,
                'TransactionDesc': transaction_desc
            }
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            
            print(f"✅ STK Push initiated: {result}")
            return result
            
        except Exception as e:
            print(f"❌ Error initiating STK Push: {str(e)}")
            raise
    
    def query_transaction(self, checkout_request_id):
        """
        Query the status of an STK Push transaction
        
        Args:
            checkout_request_id (str): CheckoutRequestID from STK Push response
        
        Returns:
            dict: Transaction status
        """
        try:
            # Get access token
            access_token = self.get_access_token()
            
            # Generate password and timestamp
            password, timestamp = self.generate_password()
            
            url = f"{self.base_url}/mpesa/stkpushquery/v1/query"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'BusinessShortCode': self.shortcode,
                'Password': password,
                'Timestamp': timestamp,
                'CheckoutRequestID': checkout_request_id
            }
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            return result
            
        except Exception as e:
            print(f"❌ Error querying transaction: {str(e)}")
            raise


# ============================================================================
# M-PESA CALLBACK HANDLER
# ============================================================================

def handle_mpesa_callback(callback_data):
    """
    Handle M-Pesa callback/webhook
    
    The callback structure from M-Pesa:
    {
        "Body": {
            "stkCallback": {
                "MerchantRequestID": "...",
                "CheckoutRequestID": "...",
                "ResultCode": 0,  # 0 = success, others = failure
                "ResultDesc": "The service request is processed successfully.",
                "CallbackMetadata": {
                    "Item": [
                        {"Name": "Amount", "Value": 1000},
                        {"Name": "MpesaReceiptNumber", "Value": "..."},
                        {"Name": "TransactionDate", "Value": 20231215123456},
                        {"Name": "PhoneNumber", "Value": 254712345678}
                    ]
                }
            }
        }
    }
    """
    try:
        stk_callback = callback_data.get('Body', {}).get('stkCallback', {})
        
        result_code = stk_callback.get('ResultCode')
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        merchant_request_id = stk_callback.get('MerchantRequestID')
        result_desc = stk_callback.get('ResultDesc')
        
        # Extract callback metadata
        callback_metadata = stk_callback.get('CallbackMetadata', {})
        items = callback_metadata.get('Item', [])
        
        # Parse metadata items
        metadata = {}
        for item in items:
            name = item.get('Name')
            value = item.get('Value')
            metadata[name] = value
        
        response = {
            'result_code': result_code,
            'checkout_request_id': checkout_request_id,
            'merchant_request_id': merchant_request_id,
            'result_desc': result_desc,
            'amount': metadata.get('Amount'),
            'mpesa_receipt': metadata.get('MpesaReceiptNumber'),
            'transaction_date': metadata.get('TransactionDate'),
            'phone_number': metadata.get('PhoneNumber'),
            'success': result_code == 0
        }
        
        return response
        
    except Exception as e:
        print(f"❌ Error handling callback: {str(e)}")
        raise


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def format_phone_number(phone):
    """
    Format phone number to M-Pesa format (254XXXXXXXXX)
    
    Args:
        phone (str): Phone number in various formats
    
    Returns:
        str: Formatted phone number
    """
    # Remove spaces, dashes, plus signs
    phone = phone.replace(' ', '').replace('-', '').replace('+', '')
    
    # Handle different formats
    if phone.startswith('0'):
        # 0712345678 -> 254712345678
        phone = '254' + phone[1:]
    elif phone.startswith('254'):
        # Already in correct format
        pass
    elif phone.startswith('7') or phone.startswith('1'):
        # 712345678 -> 254712345678
        phone = '254' + phone
    
    # Validate length (should be 12 digits: 254XXXXXXXXX)
    if len(phone) != 12:
        raise ValueError(f"Invalid phone number format: {phone}")
    
    return phone


def validate_mpesa_config():
    """Validate that all M-Pesa configuration is present"""
    required_configs = [
        'MPESA_CONSUMER_KEY',
        'MPESA_CONSUMER_SECRET',
        'MPESA_SHORTCODE',
        'MPESA_PASSKEY',
        'MPESA_CALLBACK_URL'
    ]
    
    missing = []
    for config in required_configs:
        if not current_app.config.get(config):
            missing.append(config)
    
    if missing:
        raise ValueError(f"Missing M-Pesa configuration: {', '.join(missing)}")
    
    return True