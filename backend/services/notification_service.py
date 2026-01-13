from models.notification import Notification
from services.email_service import EmailService
from extensions import mongo
from datetime import datetime, timedelta

class NotificationService:
    """
    Centralized Notification Service
    Handles both in-app and email notifications
    """
    
    def __init__(self):
        self.email_service = EmailService()
    
    def create_notification(self, user_id, notification_type, title, message, link=None, data=None):
        """
        Create an in-app notification
        """
        try:
            notification = Notification(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=message,
                link=link,
                data=data or {}
            )
            
            result = mongo.db.notifications.insert_one(notification.to_dict())
            print(f"✅ In-app notification created for user {user_id}: {title}")
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"❌ Failed to create notification: {str(e)}")
            return None
    
    # ==========================================
    # BOOKING NOTIFICATIONS
    # ==========================================
    
    def notify_booking_confirmed(self, booking_data, property_data, tenant_data, landlord_data):
        """
        Send notifications when booking is confirmed
        - Email to tenant
        - In-app notification to tenant
        """
        try:
            tenant_id = booking_data['tenant_id']
            tenant_email = booking_data['tenant_email']
            tenant_name = booking_data['tenant_name']
            
            # Create in-app notification for tenant
            self.create_notification(
                user_id=tenant_id,
                notification_type="booking_confirmed",
                title="Booking Confirmed! 🎉",
                message=f"Your booking for {property_data['title']} on {booking_data['booking_date']} has been confirmed.",
                link=f"/tenant/bookings/{booking_data['_id']}",
                data={
                    "booking_id": str(booking_data['_id']),
                    "property_id": str(property_data['_id'])
                }
            )
            
            # Send email to tenant
            self.email_service.send_booking_confirmation_email(
                tenant_email=tenant_email,
                tenant_name=tenant_name,
                booking_data=booking_data,
                property_data=property_data
            )
            
            print(f"✅ Booking confirmation notifications sent to {tenant_name}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send booking confirmation notifications: {str(e)}")
            return False
    
    def notify_booking_rejected(self, booking_data, property_data, tenant_data, rejection_reason):
        """
        Send notifications when booking is rejected
        - Email to tenant
        - In-app notification to tenant
        """
        try:
            tenant_id = booking_data['tenant_id']
            tenant_email = booking_data['tenant_email']
            tenant_name = booking_data['tenant_name']
            
            # Create in-app notification for tenant
            self.create_notification(
                user_id=tenant_id,
                notification_type="booking_rejected",
                title="Booking Update",
                message=f"Your booking request for {property_data['title']} has been declined. Reason: {rejection_reason}",
                link=f"/tenant/bookings/{booking_data['_id']}",
                data={
                    "booking_id": str(booking_data['_id']),
                    "property_id": str(property_data['_id'])
                }
            )
            
            # Send email to tenant
            self.email_service.send_booking_rejection_email(
                tenant_email=tenant_email,
                tenant_name=tenant_name,
                booking_data=booking_data,
                property_data=property_data,
                rejection_reason=rejection_reason
            )
            
            print(f"✅ Booking rejection notifications sent to {tenant_name}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send booking rejection notifications: {str(e)}")
            return False
    
    def notify_new_booking(self, booking_data, property_data, landlord_data):
        """
        Send notifications when new booking is created
        - Email to landlord
        - In-app notification to landlord
        """
        try:
            landlord_id = booking_data['landlord_id']
            landlord_email = landlord_data.get('email')
            landlord_name = landlord_data.get('name', 'Landlord')
            
            # Create in-app notification for landlord
            self.create_notification(
                user_id=landlord_id,
                notification_type="new_booking",
                title="New Booking Request! 🔔",
                message=f"{booking_data['tenant_name']} has requested to view {property_data['title']} on {booking_data['booking_date']}.",
                link=f"/landlord/bookings/{booking_data['_id']}",
                data={
                    "booking_id": str(booking_data['_id']),
                    "property_id": str(property_data['_id']),
                    "tenant_id": booking_data['tenant_id']
                }
            )
            
            # Send email to landlord
            self.email_service.send_new_booking_notification_email(
                landlord_email=landlord_email,
                landlord_name=landlord_name,
                booking_data=booking_data,
                property_data=property_data
            )
            
            print(f"✅ New booking notifications sent to landlord")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send new booking notifications: {str(e)}")
            return False
    
    def notify_booking_cancelled(self, booking_data, property_data, landlord_data, cancellation_reason):
        """
        Send notifications when booking is cancelled by tenant
        - In-app notification to landlord
        """
        try:
            landlord_id = booking_data['landlord_id']
            
            # Create in-app notification for landlord
            self.create_notification(
                user_id=landlord_id,
                notification_type="booking_cancelled",
                title="Booking Cancelled",
                message=f"{booking_data['tenant_name']} has cancelled their booking for {property_data['title']}. Reason: {cancellation_reason}",
                link=f"/landlord/bookings/{booking_data['_id']}",
                data={
                    "booking_id": str(booking_data['_id']),
                    "property_id": str(property_data['_id'])
                }
            )
            
            print(f"✅ Booking cancellation notification sent to landlord")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send booking cancellation notification: {str(e)}")
            return False
    
    def notify_booking_reminder(self, booking_data, property_data, user_data, user_role):
        """
        Send booking reminder 24 hours before scheduled time
        - In-app notification
        - Email notification
        """
        try:
            user_id = user_data.get('_id')
            
            message = f"Reminder: You have a booking for {property_data['title']} tomorrow at {booking_data['booking_time']}."
            
            # Create in-app notification
            self.create_notification(
                user_id=str(user_id),
                notification_type="booking_reminder",
                title="Booking Reminder ⏰",
                message=message,
                link=f"/{user_role}/bookings/{booking_data['_id']}",
                data={
                    "booking_id": str(booking_data['_id']),
                    "property_id": str(property_data['_id'])
                }
            )
            
            print(f"✅ Booking reminder sent to {user_data.get('email')}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send booking reminder: {str(e)}")
            return False
    
    # ==========================================
    # PROPERTY NOTIFICATIONS
    # ==========================================
    
    def notify_property_expiring(self, property_data, landlord_data, days_until_expiry):
        """
        Notify landlord that property listing is expiring soon
        """
        try:
            landlord_id = str(property_data['landlord_id'])
            landlord_email = landlord_data.get('email')
            landlord_name = landlord_data.get('name', 'Landlord')
            
            # Create in-app notification
            self.create_notification(
                user_id=landlord_id,
                notification_type="property_expiring",
                title="Property Expiring Soon ⚠️",
                message=f"Your listing '{property_data['title']}' will expire in {days_until_expiry} days. Please confirm to keep it active.",
                link=f"/landlord/properties",
                data={
                    "property_id": str(property_data['_id']),
                    "days_remaining": days_until_expiry
                }
            )
            
            # Send email
            self.email_service.send_property_expiring_email(
                landlord_email=landlord_email,
                landlord_name=landlord_name,
                property_data=property_data,
                days_until_expiry=days_until_expiry
            )
            
            print(f"✅ Property expiring notification sent to landlord")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send property expiring notification: {str(e)}")
            return False
    
    # ==========================================
    # USER NOTIFICATIONS
    # ==========================================
    
    def notify_welcome(self, user_data):
        """
        Send welcome notification to new user
        """
        try:
            user_email = user_data.get('email')
            user_name = user_data.get('name', user_email.split('@')[0])
            user_role = user_data.get('role')
            user_id = str(user_data.get('_id'))
            
            # Create in-app notification
            welcome_message = "Welcome to House Hunting Platform! "
            if user_role == "landlord":
                welcome_message += "Start by adding your first property listing."
                link = "/landlord/properties/add"
            else:
                welcome_message += "Start browsing available properties now."
                link = "/tenant/dashboard"
            
            self.create_notification(
                user_id=user_id,
                notification_type="welcome",
                title="Welcome! 🎉",
                message=welcome_message,
                link=link,
                data={"user_role": user_role}
            )
            
            # Send welcome email
            self.email_service.send_welcome_email(
                user_email=user_email,
                user_name=user_name,
                user_role=user_role
            )
            
            print(f"✅ Welcome notifications sent to {user_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send welcome notifications: {str(e)}")
            return False
    
    # ==========================================
    # UTILITY METHODS
    # ==========================================
    
    def get_unread_count(self, user_id):
        """
        Get count of unread notifications for a user
        """
        try:
            count = mongo.db.notifications.count_documents({
                "user_id": user_id,
                "is_read": False
            })
            return count
        except Exception as e:
            print(f"❌ Failed to get unread count: {str(e)}")
            return 0
    
    def mark_as_read(self, notification_id, user_id):
        """
        Mark a notification as read
        """
        try:
            mongo.db.notifications.update_one(
                {"_id": notification_id, "user_id": user_id},
                {"$set": {
                    "is_read": True,
                    "read_at": datetime.utcnow()
                }}
            )
            return True
        except Exception as e:
            print(f"❌ Failed to mark notification as read: {str(e)}")
            return False
    
    def mark_all_as_read(self, user_id):
        """
        Mark all notifications as read for a user
        """
        try:
            mongo.db.notifications.update_many(
                {"user_id": user_id, "is_read": False},
                {"$set": {
                    "is_read": True,
                    "read_at": datetime.utcnow()
                }}
            )
            return True
        except Exception as e:
            print(f"❌ Failed to mark all as read: {str(e)}")
            return False
    
    def delete_notification(self, notification_id, user_id):
        """
        Delete a notification
        """
        try:
            result = mongo.db.notifications.delete_one({
                "_id": notification_id,
                "user_id": user_id
            })
            return result.deleted_count > 0
        except Exception as e:
            print(f"❌ Failed to delete notification: {str(e)}")
            return False
    
    def cleanup_old_notifications(self, days=30):
        """
        Delete notifications older than specified days
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            result = mongo.db.notifications.delete_many({
                "created_at": {"$lt": cutoff_date}
            })
            print(f"✅ Deleted {result.deleted_count} old notifications")
            return result.deleted_count
        except Exception as e:
            print(f"❌ Failed to cleanup old notifications: {str(e)}")
            return 0