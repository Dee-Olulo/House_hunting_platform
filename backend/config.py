import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # flack configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

    # MongoDB
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/house_hunting")

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-key")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

     # CORS Configuration
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:4200").split(",")
     
     # Application Configuration
    DEBUG = os.getenv("FLASK_DEBUG", "True") == "True"
    HOST = os.getenv("FLASK_HOST", "0.0.0.0")
    PORT = int(os.getenv("FLASK_PORT", "5000"))