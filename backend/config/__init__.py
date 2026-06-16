# config/__init__.py

# Import required modules
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from the .env file into the application
load_dotenv()


class Config:
    """
    Base configuration class.

    This class contains settings shared across all environments
    (development, production, and testing).
    """

    # =========================
    # Flask Configuration
    # =========================

    # Secret key used by Flask for session management and security.
    # Falls back to a default value if not provided in the environment.
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Enable/disable debug mode based on environment variable.
    # Converts string value ('true'/'false') to a boolean.
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    # =========================
    # MongoDB Configuration
    # =========================

    # MongoDB connection string.
    # Defaults to a local MongoDB instance if not specified.
    MONGO_URI = os.getenv(
        'MONGO_URI',
        'mongodb://localhost:27017/house_hunting'
    )

    # =========================
    # JWT Authentication
    # =========================

    # Secret key used to sign and verify JWT tokens.
    # Uses Flask SECRET_KEY if a dedicated JWT secret is not provided.
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)

    # Access token validity period (1 hour).
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    # Refresh token validity period (30 days).
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # =========================
    # CORS Configuration
    # =========================

    # List of allowed origins for Cross-Origin Resource Sharing (CORS).
    # Multiple origins can be provided as a comma-separated string.
    CORS_ORIGINS = os.getenv(
        'CORS_ORIGINS',
        'http://localhost:4200'
    ).split(',')

    # =========================
    # File Upload Configuration
    # =========================

    # Directory where uploaded files will be stored.
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')

    # Maximum allowed upload size (100 MB).
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024

    # =========================
    # Cloudinary Configuration
    # =========================

    # Cloudinary cloud name used for media storage.
    CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')

    # Cloudinary API key for authentication.
    CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')

    # Cloudinary API secret for authentication.
    CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')


class DevelopmentConfig(Config):
    """
    Development environment configuration.

    Enables debugging features to assist during development.
    """
    DEBUG = True


class ProductionConfig(Config):
    """
    Production environment configuration.

    Debugging is disabled for security and performance reasons.
    """
    DEBUG = False


class TestingConfig(Config):
    """
    Testing environment configuration.

    Uses a separate database to prevent tests from affecting
    development or production data.
    """
    TESTING = True

    # Dedicated MongoDB database for automated tests.
    MONGO_URI = 'mongodb://localhost:27017/house_hunting_test'


# ==================================================
# Configuration Mapping
# ==================================================
# Allows configuration selection based on environment.
# Example:
# app_config = config['development']
#
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}