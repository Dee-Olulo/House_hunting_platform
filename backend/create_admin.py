# create_admin.py
# Used to seed an admin user into the MongoDB database.
# Run manually from the terminal: python create_admin.py
# Safe to run multiple times -- it exits early if the admin already exists.

# Standard library imports
from datetime import datetime

# Flask app factory and extensions
from app import create_app
from extensions import mongo, bcrypt

# Initialize the Flask app using the factory pattern.
# This is required so that Flask extensions (mongo, bcrypt) are bound
# to an app instance and can be used outside of a normal request cycle.
app = create_app()

def create_admin():
    # Open a manual app context so Flask-bound resources (DB, extensions)
    # are accessible.
    with app.app_context():

        # admin credentials 
        email = "admin@househunting.com"
        password = "#_admin123"

        #check if this admin already exists.
        existing_admin = mongo.db.users.find_one({"email": email})
        if existing_admin:
            print(f"Warning: Admin user already exists: {email}")
            return  

        # Hash the plain-text password using bcrypt before storing it.
        # bcrypt produces a one-way hash .
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        # Build the admin user document to be stored in MongoDB.
        admin_user = {
            "email": email,
            "password": hashed_password,   # Stored as a bcrypt hash, never plain text.
            "role": "admin",                
            "created_at": datetime.utcnow(), 
            "is_verified": True          
        }

        # Insert the document into the users collection in MongoDB.
        # insert_one() returns a result object containing the new document's ID.
        result = mongo.db.users.insert_one(admin_user)

        # Confirm success and print the key details for reference.
        print(f"Admin created successfully!")
        print(f"Email: {email}")
        print(f"Password: {password}")          
        print(f"User ID: {result.inserted_id}") 

# Entry point guard -- ensures create_admin() only runs when this file
# is executed directly (python create_admin.py), not when imported as a module.
if __name__ == "__main__":
    create_admin()