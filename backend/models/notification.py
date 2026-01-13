from datetime import datetime
from bson import ObjectId

class Notification:
    """
    In-app Notification Model
    Types: booking_confirmed, booking_rejected, booking_cancelled, 
           property_inquiry, new_booking, booking_reminder, property_expiring
    """
    
    def __init__(
        self,
        user_id,
        notification_type,
        title,
        message,
        link=None,
        data=None,
        is_read=False,
        read_at=None,
        created_at=None,
        expires_at=None,
        _id=None
    ):
        self._id = _id or ObjectId()
        self.user_id = user_id  # User who receives the notification
        self.notification_type = notification_type
        self.title = title
        self.message = message
        self.link = link  # Optional link to relevant page (e.g., /bookings/123)
        self.data = data or {}  # Additional metadata (property_id, booking_id, etc.)
        self.is_read = is_read
        self.read_at = read_at
        self.created_at = created_at or datetime.utcnow()
        self.expires_at = expires_at  # Optional expiration date
    
    def to_dict(self):
        """Convert notification object to dictionary for MongoDB"""
        return {
            "_id": self._id,
            "user_id": self.user_id,
            "notification_type": self.notification_type,
            "title": self.title,
            "message": self.message,
            "link": self.link,
            "data": self.data,
            "is_read": self.is_read,
            "read_at": self.read_at,
            "created_at": self.created_at,
            "expires_at": self.expires_at
        }
    
    @staticmethod
    def from_dict(data):
        """Create Notification object from dictionary"""
        return Notification(
            user_id=data.get("user_id"),
            notification_type=data.get("notification_type"),
            title=data.get("title"),
            message=data.get("message"),
            link=data.get("link"),
            data=data.get("data", {}),
            is_read=data.get("is_read", False),
            read_at=data.get("read_at"),
            created_at=data.get("created_at"),
            expires_at=data.get("expires_at"),
            _id=data.get("_id")
        )