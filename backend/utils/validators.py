import re
from datetime import datetime, timedelta

def validate_role(role):
    return role in ["tenant", "landlord", "admin"]

def validate_email(email):
    return email and "@" in email

def validate_password(password):
    return password and len(password) >= 6

# Property data validation
def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password - minimum 6 characters"""
    return len(password) >= 6

def validate_role(role):
    """Validate user role"""
    allowed_roles = ["admin", "landlord", "tenant"]
    return role in allowed_roles

def validate_property_data(data, is_update=False):
    """
    Validate property data
    is_update: If True, allows partial validation (for updates)
    """
    errors = []
    
    # Required fields for new property
    if not is_update:
        required_fields = [
            "title", "description", "property_type", "address",
            "city", "state", "country", "price", "bedrooms",
            "bathrooms", "area_sqft"
        ]
        
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"{field} is required")
    
    # Validate title
    if "title" in data:
        if not isinstance(data["title"], str) or len(data["title"]) < 5:
            errors.append("Title must be at least 5 characters long")
        elif len(data["title"]) > 200:
            errors.append("Title must not exceed 200 characters")
    
    # Validate description
    if "description" in data:
        if not isinstance(data["description"], str) or len(data["description"]) < 20:
            errors.append("Description must be at least 20 characters long")
        elif len(data["description"]) > 2000:
            errors.append("Description must not exceed 2000 characters")
    
    # Validate property type
    if "property_type" in data:
        valid_types = ["apartment", "house", "studio", "condo", "townhouse", "villa"]
        if data["property_type"] not in valid_types:
            errors.append(f"Property type must be one of: {', '.join(valid_types)}")
    
    # Validate price
    if "price" in data:
        try:
            price = float(data["price"])
            if price <= 0:
                errors.append("Price must be greater than 0")
            elif price > 1000000000:  # 1 billion max
                errors.append("Price is too high")
        except (ValueError, TypeError):
            errors.append("Price must be a valid number")
    
    # Validate bedrooms
    if "bedrooms" in data:
        try:
            bedrooms = int(data["bedrooms"])
            if bedrooms < 0:
                errors.append("Bedrooms cannot be negative")
            elif bedrooms > 50:
                errors.append("Bedrooms value is too high")
        except (ValueError, TypeError):
            errors.append("Bedrooms must be a valid integer")
    
    # Validate bathrooms
    if "bathrooms" in data:
        try:
            bathrooms = float(data["bathrooms"])
            if bathrooms < 0:
                errors.append("Bathrooms cannot be negative")
            elif bathrooms > 50:
                errors.append("Bathrooms value is too high")
        except (ValueError, TypeError):
            errors.append("Bathrooms must be a valid number")
    
    # Validate area
    if "area_sqft" in data:
        try:
            area = float(data["area_sqft"])
            if area <= 0:
                errors.append("Area must be greater than 0")
            elif area > 1000000:  # 1 million sqft max
                errors.append("Area is too large")
        except (ValueError, TypeError):
            errors.append("Area must be a valid number")
    
    # Validate coordinates (optional but if provided must be valid)
    if "latitude" in data and data["latitude"] is not None:
        try:
            lat = float(data["latitude"])
            if lat < -90 or lat > 90:
                errors.append("Latitude must be between -90 and 90")
        except (ValueError, TypeError):
            errors.append("Latitude must be a valid number")
    
    if "longitude" in data and data["longitude"] is not None:
        try:
            lon = float(data["longitude"])
            if lon < -180 or lon > 180:
                errors.append("Longitude must be between -180 and 180")
        except (ValueError, TypeError):
            errors.append("Longitude must be a valid number")
    
    # Validate images (if provided)
    if "images" in data:
        if not isinstance(data["images"], list):
            errors.append("Images must be a list")
        elif len(data["images"]) > 20:
            errors.append("Maximum 20 images allowed")
    
    # Validate videos (if provided)
    if "videos" in data:
        if not isinstance(data["videos"], list):
            errors.append("Videos must be a list")
        elif len(data["videos"]) > 5:
            errors.append("Maximum 5 videos allowed")
    
    # Validate amenities (if provided)
    if "amenities" in data:
        if not isinstance(data["amenities"], list):
            errors.append("Amenities must be a list")
    
    # Validate status (if provided)
    if "status" in data:
        valid_statuses = ["active", "inactive", "pending", "expired"]
        if data["status"] not in valid_statuses:
            errors.append(f"Status must be one of: {', '.join(valid_statuses)}")
    
    return (len(errors) == 0, errors)

# Booking data validation
def validate_booking_data(data, is_update=False):
    """
    Validate booking request data
    is_update: If True, allows partial validation (for updates)
    """
    errors = []
    
    # Required fields for new booking
    if not is_update:
        required_fields = [
            "property_id", "booking_type", "booking_date", 
            "booking_time", "tenant_name", "tenant_email"
        ]
        
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"{field} is required")
    
    # Validate booking type
    if "booking_type" in data:
        valid_types = ["viewing", "rental_inquiry"]
        if data["booking_type"] not in valid_types:
            errors.append(f"Booking type must be one of: {', '.join(valid_types)}")
    
    # Validate booking date
    if "booking_date" in data:
        try:
            booking_date_str = data["booking_date"]
            # Expected format: YYYY-MM-DD
            booking_date = datetime.strptime(booking_date_str, "%Y-%m-%d")
            
            # Check if date is in the past
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            if booking_date < today:
                errors.append("Booking date cannot be in the past")
            
            # Check if date is too far in the future (e.g., 6 months)
            max_future_date = today + timedelta(days=180)
            if booking_date > max_future_date:
                errors.append("Booking date cannot be more than 6 months in the future")
                
        except ValueError:
            errors.append("Invalid booking date format. Use YYYY-MM-DD")
    
    # Validate booking time
    if "booking_time" in data:
        try:
            # Expected format: HH:MM (24-hour format)
            time_pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'
            if not re.match(time_pattern, data["booking_time"]):
                errors.append("Invalid booking time format. Use HH:MM (24-hour format)")
        except Exception:
            errors.append("Invalid booking time")
    
    # Validate tenant name
    if "tenant_name" in data:
        if not isinstance(data["tenant_name"], str) or len(data["tenant_name"]) < 2:
            errors.append("Tenant name must be at least 2 characters long")
        elif len(data["tenant_name"]) > 100:
            errors.append("Tenant name must not exceed 100 characters")
    
    # Validate tenant email
    if "tenant_email" in data:
        if not validate_email(data["tenant_email"]):
            errors.append("Invalid tenant email format")
    
    # Validate tenant phone (optional but if provided must be valid)
    if "tenant_phone" in data and data["tenant_phone"]:
        phone_pattern = r'^\+?[0-9]{10,15}$'
        if not re.match(phone_pattern, data["tenant_phone"]):
            errors.append("Invalid phone number format")
    
    # Validate message (optional)
    if "message" in data and data["message"]:
        if len(data["message"]) > 1000:
            errors.append("Message must not exceed 1000 characters")
    
    # Validate status (if provided)
    if "status" in data:
        valid_statuses = ["pending", "confirmed", "rejected", "completed", "cancelled"]
        if data["status"] not in valid_statuses:
            errors.append(f"Status must be one of: {', '.join(valid_statuses)}")
    
    # Validate rejection reason (required when rejecting)
    if data.get("status") == "rejected" and not data.get("rejection_reason"):
        errors.append("Rejection reason is required when rejecting a booking")
    
    # Validate cancellation reason (required when cancelling)
    if data.get("status") == "cancelled" and not data.get("cancellation_reason"):
        errors.append("Cancellation reason is required when cancelling a booking")
    
    return (len(errors) == 0, errors)


def validate_phone_number(phone):
    """Validate phone number format"""
    if not phone:
        return False
    phone_pattern = r'^\+?[0-9]{10,15}$'
    return re.match(phone_pattern, phone) is not None