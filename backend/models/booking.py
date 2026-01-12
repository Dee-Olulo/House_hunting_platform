from datetime import datetime
from bson import ObjectId


class Booking:
    """
    Booking Model for Property Viewing/Rental Requests
    Status flow: pending -> confirmed/rejected -> completed/cancelled
    """
    
    def __init__(
        self,
        property_id,
        tenant_id,
        landlord_id,
        booking_type,
        booking_date,
        booking_time,
        status="pending",
        tenant_name=None,
        tenant_email=None,
        tenant_phone=None,
        message=None,
        notes=None,
        cancellation_reason=None,
        rejection_reason=None,
        created_at=None,
        updated_at=None,
        confirmed_at=None,
        completed_at=None,
        cancelled_at=None,
        _id=None
    ):
        self._id = _id or ObjectId()
        self.property_id = property_id
        self.tenant_id = tenant_id
        self.landlord_id = landlord_id
        self.booking_type = booking_type  # viewing, rental_inquiry
        self.booking_date = booking_date  # Date for the viewing/meeting
        self.booking_time = booking_time  # Time for the viewing/meeting
        self.status = status  # pending, confirmed, rejected, completed, cancelled
        
        # Tenant contact information
        self.tenant_name = tenant_name
        self.tenant_email = tenant_email
        self.tenant_phone = tenant_phone
        
        # Additional information
        self.message = message  # Message from tenant
        self.notes = notes  # Landlord's internal notes
        
        # Cancellation/Rejection tracking
        self.cancellation_reason = cancellation_reason
        self.rejection_reason = rejection_reason
        
        # Timestamps
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.confirmed_at = confirmed_at
        self.completed_at = completed_at
        self.cancelled_at = cancelled_at
    
    def to_dict(self):
        """Convert booking object to dictionary for MongoDB"""
        return {
            "_id": self._id,
            "property_id": self.property_id,
            "tenant_id": self.tenant_id,
            "landlord_id": self.landlord_id,
            "booking_type": self.booking_type,
            "booking_date": self.booking_date,
            "booking_time": self.booking_time,
            "status": self.status,
            "tenant_name": self.tenant_name,
            "tenant_email": self.tenant_email,
            "tenant_phone": self.tenant_phone,
            "message": self.message,
            "notes": self.notes,
            "cancellation_reason": self.cancellation_reason,
            "rejection_reason": self.rejection_reason,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "confirmed_at": self.confirmed_at,
            "completed_at": self.completed_at,
            "cancelled_at": self.cancelled_at
        }
    
    @staticmethod
    def from_dict(data):
        """Create Booking object from dictionary"""
        return Booking(
            property_id=data.get("property_id"),
            tenant_id=data.get("tenant_id"),
            landlord_id=data.get("landlord_id"),
            booking_type=data.get("booking_type"),
            booking_date=data.get("booking_date"),
            booking_time=data.get("booking_time"),
            status=data.get("status", "pending"),
            tenant_name=data.get("tenant_name"),
            tenant_email=data.get("tenant_email"),
            tenant_phone=data.get("tenant_phone"),
            message=data.get("message"),
            notes=data.get("notes"),
            cancellation_reason=data.get("cancellation_reason"),
            rejection_reason=data.get("rejection_reason"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            confirmed_at=data.get("confirmed_at"),
            completed_at=data.get("completed_at"),
            cancelled_at=data.get("cancelled_at"),
            _id=data.get("_id")
        )