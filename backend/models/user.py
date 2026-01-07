from bson.objectid import ObjectId

class User:
    """
    MongoDB User Model
    Roles: tenant | landlord | admin
    """

    def __init__(self, email, password, role):
        self.email = email
        self.password = password
        self.role = role

    def to_dict(self):
        return {
            "email": self.email,
            "password": self.password,
            "role": self.role
        }
