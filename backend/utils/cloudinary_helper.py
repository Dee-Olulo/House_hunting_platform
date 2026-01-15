import cloudinary
import cloudinary.uploader
import os
from werkzeug.utils import secure_filename
import tempfile

# Configure Cloudinary (add your credentials in your main app or config)
# cloudinary.config(
#     cloud_name = "your_cloud_name",
#     api_key = "your_api_key",
#     api_secret = "your_api_secret"
# )


def upload_image_to_cloudinary(file):
    """Upload a single image to Cloudinary"""
    try:
        result = cloudinary.uploader.upload(
            file,
            folder="property_images",
            resource_type="image"
        )
        return {
            "url": result["secure_url"],
            "public_id": result["public_id"],
            "filename": result.get("original_filename", "")
        }
    except Exception as e:
        print(f"Error uploading image to Cloudinary: {str(e)}")
        raise


def upload_video_to_cloudinary(file):
    """Upload a single video to Cloudinary"""
    try:
        # For videos, we need to save to a temporary file first
        # because Cloudinary's video upload requires a file path
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        try:
            file.save(temp_file.name)
            temp_file.close()
            
            result = cloudinary.uploader.upload(
                temp_file.name,
                folder="property_videos",
                resource_type="video",
                chunk_size=6000000  # 6MB chunks for better reliability
            )
            
            return {
                "url": result["secure_url"],
                "public_id": result["public_id"],
                "filename": result.get("original_filename", "")
            }
        finally:
            # Clean up temp file
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
                
    except Exception as e:
        print(f"Error uploading video to Cloudinary: {str(e)}")
        raise


def upload_multiple_images(files):
    """Upload multiple images to Cloudinary"""
    uploaded_files = []
    errors = []
    
    for file in files:
        try:
            result = upload_image_to_cloudinary(file)
            uploaded_files.append({
                "original_name": file.filename,
                "url": result["url"],
                "filename": result["filename"]
            })
        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")
    
    return uploaded_files, errors


def upload_multiple_videos(files):
    """Upload multiple videos to Cloudinary"""
    uploaded_files = []
    errors = []
    
    for file in files:
        try:
            print(f"Uploading video to Cloudinary: {file.filename}")
            
            # Create a temporary file to save the video
            # FileStorage objects need to be saved to disk for Cloudinary video upload
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            
            try:
                # Save the uploaded file to the temp file
                file.save(temp_file.name)
                temp_file.close()
                
                print(f"Temp file created: {temp_file.name}")
                
                # Upload to Cloudinary using the temp file path
                result = cloudinary.uploader.upload(
                    temp_file.name,
                    folder="property_videos",
                    resource_type="video",
                    chunk_size=6000000  # 6MB chunks
                )
                
                print(f"Cloudinary upload successful: {result['secure_url']}")
                
                uploaded_files.append({
                    "original_name": file.filename,
                    "url": result["secure_url"],
                    "filename": result.get("original_filename", file.filename)
                })
                
            finally:
                # Always clean up the temp file
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
                    print(f"Temp file cleaned up: {temp_file.name}")
                    
        except Exception as e:
            error_msg = f"{file.filename}: {str(e)}"
            print(f"❌ Error uploading video: {error_msg}")
            errors.append(error_msg)
    
    return uploaded_files, errors


def delete_from_cloudinary(url, resource_type="image"):
    """Delete a file from Cloudinary using its URL"""
    try:
        # Extract public_id from URL
        # Example URL: https://res.cloudinary.com/demo/image/upload/v1234567890/property_images/abc123.jpg
        # Public ID would be: property_images/abc123
        
        parts = url.split("/upload/")
        if len(parts) < 2:
            return False
            
        # Get everything after /upload/ and remove version number if present
        path_parts = parts[1].split("/")
        if path_parts[0].startswith("v"):
            path_parts = path_parts[1:]  # Remove version
            
        public_id = "/".join(path_parts)
        
        # Remove file extension
        public_id = os.path.splitext(public_id)[0]
        
        print(f"Deleting from Cloudinary: {public_id} (type: {resource_type})")
        
        result = cloudinary.uploader.destroy(
            public_id,
            resource_type=resource_type
        )
        
        return result.get("result") == "ok"
        
    except Exception as e:
        print(f"Error deleting from Cloudinary: {str(e)}")
        return False