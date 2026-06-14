# models/user.py
# Defines the structure of a User document stored in MongoDB.
# . Routes/services instantiate it, call to_dict(), and pass
# the result to mongo.db.users.insert_one() / update_one() etc.
#
# Roles:
#   tenant   -> can browse properties and make bookings
#   landlord -> can list and manage properties
#   admin    -> full platform access

from bson.objectid import ObjectId

class User:
    """
    Represents a user document in the MongoDB 'users' collection.
    Roles: tenant | landlord | admin
    """

    def __init__(self, email, password, role):
        # Email serves as the unique identifier for login
        self.email = email

        # Password must already be hashed (via bcrypt) before passing it in.
        # This class never receives or stores a plaintext password.
        self.password = password

        # Role controls what the user can access across the platform
        self.role = role

    def to_dict(self):
        # Converts the User object into a plain dictionary suitable for
        # inserting into MongoDB. Additional fields (e.g. is_verified,
        # created_at) are typically added at the route/service level
        # before the insert so this model stays minimal and reusable.
        return {
            "email": self.email,
            "password": self.password,
            "role": self.role
        }