# create_admin.py
from flask import app
from app import create_app  # Import your Flask app instance
from extensions import mongo, bcrypt
from datetime import datetime
app = create_app()
def create_admin():
    with app.app_context():  # Important: Run within Flask app context
        email = "admin@househunting.com"
        password = "#_admin123"  # Change this!
        
        # Check if admin already exists
        existing_admin = mongo.db.users.find_one({"email": email})
        if existing_admin:
            print(f"⚠️  Admin user already exists: {email}")
            return
        
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        
        admin_user = {
            "email": email,
            "password": hashed_password,
            "role": "admin",
            "created_at": datetime.utcnow(),
            "is_verified": True  # Auto-verify admin
        }
        
        result = mongo.db.users.insert_one(admin_user)
        print(f"✅ Admin created successfully!")
        print(f"📧 Email: {email}")
        print(f"🔑 Password: {password}")
        print(f"🆔 User ID: {result.inserted_id}")

if __name__ == "__main__":
    create_admin()