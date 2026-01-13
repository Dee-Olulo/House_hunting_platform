import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

class EmailService:
    """
    Email Service for sending notifications
    Uses SMTP (Gmail, SendGrid, or other providers)
    """
    
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("SENDER_EMAIL", "noreply@househunting.com")
        self.sender_password = os.getenv("SENDER_PASSWORD", "")
        self.sender_name = os.getenv("SENDER_NAME", "House Hunting Platform")
        self.enabled = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
    
    def send_email(self, to_email, subject, html_content, text_content=None):
        """
        Send email using SMTP
        """
        if not self.enabled:
            print(f"📧 [EMAIL DISABLED] Would send to {to_email}: {subject}")
            return True
        
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = to_email
            
            # Add plain text version
            if text_content:
                part1 = MIMEText(text_content, "plain")
                message.attach(part1)
            
            # Add HTML version
            part2 = MIMEText(html_content, "html")
            message.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, to_email, message.as_string())
            
            print(f"✅ Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email to {to_email}: {str(e)}")
            return False
    
    # ==========================================
    # BOOKING NOTIFICATION EMAILS
    # ==========================================
    
    def send_booking_confirmation_email(self, tenant_email, tenant_name, booking_data, property_data):
        """Send email when booking is confirmed by landlord"""
        subject = f"Booking Confirmed - {property_data['title']}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .details {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ Booking Confirmed!</h1>
                </div>
                <div class="content">
                    <p>Hi {tenant_name},</p>
                    <p>Great news! Your booking request has been confirmed by the landlord.</p>
                    
                    <div class="details">
                        <h3>📍 Property Details</h3>
                        <p><strong>{property_data['title']}</strong></p>
                        <p>{property_data['address']}, {property_data['city']}</p>
                        
                        <h3>📅 Booking Details</h3>
                        <p><strong>Date:</strong> {booking_data['booking_date']}</p>
                        <p><strong>Time:</strong> {booking_data['booking_time']}</p>
                        <p><strong>Type:</strong> {booking_data['booking_type']}</p>
                    </div>
                    
                    <p>Please arrive on time at the scheduled date and time.</p>
                    
                    <center>
                        <a href="http://localhost:4200/tenant/bookings" class="button">View Booking Details</a>
                    </center>
                </div>
                <div class="footer">
                    <p>House Hunting Platform | This is an automated message</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Booking Confirmed!
        
        Hi {tenant_name},
        
        Your booking request has been confirmed.
        
        Property: {property_data['title']}
        Location: {property_data['address']}, {property_data['city']}
        Date: {booking_data['booking_date']}
        Time: {booking_data['booking_time']}
        
        Please arrive on time.
        
        View details: http://localhost:4200/tenant/bookings
        """
        
        return self.send_email(tenant_email, subject, html_content, text_content)
    
    def send_booking_rejection_email(self, tenant_email, tenant_name, booking_data, property_data, rejection_reason):
        """Send email when booking is rejected by landlord"""
        subject = f"Booking Update - {property_data['title']}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .details {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>❌ Booking Update</h1>
                </div>
                <div class="content">
                    <p>Hi {tenant_name},</p>
                    <p>Unfortunately, your booking request for <strong>{property_data['title']}</strong> has been declined.</p>
                    
                    <div class="details">
                        <h3>💬 Reason</h3>
                        <p>{rejection_reason}</p>
                        
                        <h3>📅 Original Request</h3>
                        <p><strong>Date:</strong> {booking_data['booking_date']}</p>
                        <p><strong>Time:</strong> {booking_data['booking_time']}</p>
                    </div>
                    
                    <p>Don't worry! There are many other great properties available. Keep exploring!</p>
                    
                    <center>
                        <a href="http://localhost:4200/tenant/dashboard" class="button">Browse Properties</a>
                    </center>
                </div>
                <div class="footer">
                    <p>House Hunting Platform | This is an automated message</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(tenant_email, subject, html_content)
    
    def send_new_booking_notification_email(self, landlord_email, landlord_name, booking_data, property_data):
        """Send email to landlord when new booking is created"""
        subject = f"New Booking Request - {property_data['title']}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .details {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔔 New Booking Request!</h1>
                </div>
                <div class="content">
                    <p>Hi there,</p>
                    <p>You have a new booking request for your property <strong>{property_data['title']}</strong>.</p>
                    
                    <div class="details">
                        <h3>👤 Tenant Information</h3>
                        <p><strong>Name:</strong> {booking_data['tenant_name']}</p>
                        <p><strong>Email:</strong> {booking_data['tenant_email']}</p>
                        <p><strong>Phone:</strong> {booking_data.get('tenant_phone', 'Not provided')}</p>
                        
                        <h3>📅 Requested Date & Time</h3>
                        <p><strong>Date:</strong> {booking_data['booking_date']}</p>
                        <p><strong>Time:</strong> {booking_data['booking_time']}</p>
                        <p><strong>Type:</strong> {booking_data['booking_type']}</p>
                        
                        {f"<h3>💬 Message</h3><p>{booking_data.get('message')}</p>" if booking_data.get('message') else ""}
                    </div>
                    
                    <p>Please review and respond to this booking request.</p>
                    
                    <center>
                        <a href="http://localhost:4200/landlord/bookings" class="button">Manage Bookings</a>
                    </center>
                </div>
                <div class="footer">
                    <p>House Hunting Platform | This is an automated message</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(landlord_email, subject, html_content)
    
    # ==========================================
    # PROPERTY NOTIFICATION EMAILS
    # ==========================================
    
    def send_property_expiring_email(self, landlord_email, landlord_name, property_data, days_until_expiry):
        """Send email when property listing is about to expire"""
        subject = f"Property Expiring Soon - {property_data['title']}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #f2994a 0%, #f2c94c 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⚠️ Property Expiring Soon</h1>
                </div>
                <div class="content">
                    <p>Hi {landlord_name},</p>
                    <p>Your property listing <strong>{property_data['title']}</strong> will expire in {days_until_expiry} days.</p>
                    <p>To keep your property active and visible to potential tenants, please confirm your listing.</p>
                    
                    <center>
                        <a href="http://localhost:4200/landlord/properties" class="button">Renew Listing</a>
                    </center>
                </div>
                <div class="footer">
                    <p>House Hunting Platform | This is an automated message</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(landlord_email, subject, html_content)
    
    def send_welcome_email(self, user_email, user_name, user_role):
        """Send welcome email to new users"""
        subject = "Welcome to House Hunting Platform!"
        
        role_specific_content = ""
        if user_role == "landlord":
            role_specific_content = """
            <p>As a landlord, you can:</p>
            <ul>
                <li>List your properties with photos and details</li>
                <li>Manage booking requests from tenants</li>
                <li>Track property views and inquiries</li>
                <li>Communicate with potential tenants</li>
            </ul>
            """
        else:
            role_specific_content = """
            <p>As a tenant, you can:</p>
            <ul>
                <li>Browse thousands of available properties</li>
                <li>Request property viewings</li>
                <li>Save your favorite listings</li>
                <li>Track your booking requests</li>
            </ul>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Welcome!</h1>
                </div>
                <div class="content">
                    <p>Hi {user_name},</p>
                    <p>Welcome to House Hunting Platform! We're excited to have you on board.</p>
                    
                    {role_specific_content}
                    
                    <center>
                        <a href="http://localhost:4200/login" class="button">Get Started</a>
                    </center>
                </div>
                <div class="footer">
                    <p>House Hunting Platform | This is an automated message</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(user_email, subject, html_content)