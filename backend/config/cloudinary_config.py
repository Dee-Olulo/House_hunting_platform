# config/cloudinary_config.py
import cloudinary
import cloudinary.uploader
import cloudinary.api
import os
from dotenv import load_dotenv

load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET'),
    secure=True
)

# Upload configurations
CLOUDINARY_IMAGE_CONFIG = {
    'folder': 'properties/images',
    'resource_type': 'image',
    'allowed_formats': ['jpg', 'jpeg', 'png', 'gif', 'webp'],
    'transformation': [
        {'quality': 'auto', 'fetch_format': 'auto'},
        {'width': 1200, 'height': 900, 'crop': 'limit'}
    ]
}

CLOUDINARY_VIDEO_CONFIG = {
    'folder': 'properties/videos',
    'resource_type': 'video',
    'allowed_formats': ['mp4', 'mov', 'avi', 'wmv', 'webm'],
    'transformation': [
        {'quality': 'auto'},
        {'width': 1280, 'height': 720, 'crop': 'limit'}
    ]
}

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB
MAX_VIDEO_DURATION = 300  # 5 minutes in seconds