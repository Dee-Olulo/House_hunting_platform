import os
from datetime import timedelta
# Default MongoDB settings
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "myapp_db"
class Config:
    # Flask secret key (used for sessions, security)
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")

    # Secret key used to sign JWT tokens
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-key")

    # How long a JWT token should be valid
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)

    # MongoDB connection string
    # Database name here is "house_hunting"
    MONGO_URI = os.getenv(
        "MONGO_URI",
        "mongodb://localhost:27017/house_hunting"
    )
