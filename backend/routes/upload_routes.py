# from flask import Blueprint, request, jsonify
# from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
# from werkzeug.utils import secure_filename
# import os
# import uuid
# from datetime import datetime

# upload_bp = Blueprint("upload", __name__)

# # Configuration
# UPLOAD_FOLDER = 'uploads'
# ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
# ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'wmv', 'webm'}
# MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
# MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB

# def allowed_file(filename, allowed_extensions):
#     """Check if file extension is allowed"""
#     return '.' in filename and \
#            filename.rsplit('.', 1)[1].lower() in allowed_extensions

# def get_file_extension(filename):
#     """Get file extension"""
#     return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

# def generate_unique_filename(original_filename):
#     """Generate unique filename to avoid collisions"""
#     ext = get_file_extension(original_filename)
#     unique_name = f"{uuid.uuid4().hex}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{ext}"
#     return unique_name

# # ---------------------------
# # UPLOAD IMAGE
# # ---------------------------
# @upload_bp.route("/image", methods=["POST"])
# @jwt_required()
# def upload_image():
#     try:
#         # ✅ OPTIONAL: Get user info if you want to track who uploaded what
#         user_id = get_jwt_identity()  # Returns string user ID
#         # claims = get_jwt()  # Uncomment if you need email/role
        
#         # Check if file is in request
#         if 'file' not in request.files:
#             return jsonify({"error": "No file provided"}), 400
        
#         file = request.files['file']
        
#         if file.filename == '':
#             return jsonify({"error": "No file selected"}), 400
        
#         # Validate file extension
#         if not allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
#             return jsonify({
#                 "error": f"Invalid file type. Allowed types: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
#             }), 400
        
#         # Check file size
#         file.seek(0, os.SEEK_END)
#         file_size = file.tell()
#         file.seek(0)
        
#         if file_size > MAX_IMAGE_SIZE:
#             return jsonify({"error": "File too large. Maximum size is 5MB"}), 400
        
#         # Create upload directory if it doesn't exist
#         images_folder = os.path.join(UPLOAD_FOLDER, 'images')
#         os.makedirs(images_folder, exist_ok=True)
        
#         # Generate unique filename
#         unique_filename = generate_unique_filename(file.filename)
#         file_path = os.path.join(images_folder, unique_filename)
        
#         # Save file
#         file.save(file_path)
        
#         # Return file URL (adjust based on your server setup)
#         file_url = f"/uploads/images/{unique_filename}"
        
#         return jsonify({
#             "message": "Image uploaded successfully",
#             "url": file_url,
#             "filename": unique_filename
#         }), 201
        
#     except Exception as e:
#         return jsonify({"error": f"Failed to upload image: {str(e)}"}), 500

# # ---------------------------
# # UPLOAD VIDEO
# # ---------------------------
# @upload_bp.route("/video", methods=["POST"])
# @jwt_required()
# def upload_video():
#     try:
#         # ✅ OPTIONAL: Get user info if needed
#         user_id = get_jwt_identity()  # Returns string user ID
        
#         # Check if file is in request
#         if 'file' not in request.files:
#             return jsonify({"error": "No file provided"}), 400
        
#         file = request.files['file']
        
#         if file.filename == '':
#             return jsonify({"error": "No file selected"}), 400
        
#         # Validate file extension
#         if not allowed_file(file.filename, ALLOWED_VIDEO_EXTENSIONS):
#             return jsonify({
#                 "error": f"Invalid file type. Allowed types: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}"
#             }), 400
        
#         # Check file size
#         file.seek(0, os.SEEK_END)
#         file_size = file.tell()
#         file.seek(0)
        
#         if file_size > MAX_VIDEO_SIZE:
#             return jsonify({"error": "File too large. Maximum size is 50MB"}), 400
        
#         # Create upload directory if it doesn't exist
#         videos_folder = os.path.join(UPLOAD_FOLDER, 'videos')
#         os.makedirs(videos_folder, exist_ok=True)
        
#         # Generate unique filename
#         unique_filename = generate_unique_filename(file.filename)
#         file_path = os.path.join(videos_folder, unique_filename)
        
#         # Save file
#         file.save(file_path)
        
#         # Return file URL (adjust based on your server setup)
#         file_url = f"/uploads/videos/{unique_filename}"
        
#         return jsonify({
#             "message": "Video uploaded successfully",
#             "url": file_url,
#             "filename": unique_filename
#         }), 201
        
#     except Exception as e:
#         return jsonify({"error": f"Failed to upload video: {str(e)}"}), 500

# # ---------------------------
# # UPLOAD MULTIPLE IMAGES
# # ---------------------------
# @upload_bp.route("/images/multiple", methods=["POST"])
# @jwt_required()
# def upload_multiple_images():
#     try:
#         # ✅ OPTIONAL: Get user info if needed
#         user_id = get_jwt_identity()  # Returns string user ID
        
#         # Check if files are in request
#         if 'files' not in request.files:
#             return jsonify({"error": "No files provided"}), 400
        
#         files = request.files.getlist('files')
        
#         if not files or len(files) == 0:
#             return jsonify({"error": "No files selected"}), 400
        
#         if len(files) > 20:
#             return jsonify({"error": "Maximum 20 files allowed"}), 400
        
#         uploaded_files = []
#         errors = []
        
#         # Create upload directory if it doesn't exist
#         images_folder = os.path.join(UPLOAD_FOLDER, 'images')
#         os.makedirs(images_folder, exist_ok=True)
        
#         for file in files:
#             try:
#                 # Validate file
#                 if file.filename == '':
#                     continue
                
#                 if not allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
#                     errors.append(f"{file.filename}: Invalid file type")
#                     continue
                
#                 # Check file size
#                 file.seek(0, os.SEEK_END)
#                 file_size = file.tell()
#                 file.seek(0)
                
#                 if file_size > MAX_IMAGE_SIZE:
#                     errors.append(f"{file.filename}: File too large")
#                     continue
                
#                 # Generate unique filename and save
#                 unique_filename = generate_unique_filename(file.filename)
#                 file_path = os.path.join(images_folder, unique_filename)
#                 file.save(file_path)
                
#                 file_url = f"/uploads/images/{unique_filename}"
#                 uploaded_files.append({
#                     "original_name": file.filename,
#                     "url": file_url,
#                     "filename": unique_filename
#                 })
                
#             except Exception as e:
#                 errors.append(f"{file.filename}: {str(e)}")
        
#         return jsonify({
#             "message": f"Uploaded {len(uploaded_files)} files successfully",
#             "files": uploaded_files,
#             "errors": errors if errors else None
#         }), 201
        
#     except Exception as e:
#         return jsonify({"error": f"Failed to upload files: {str(e)}"}), 500

# # ---------------------------
# # DELETE FILE
# # ---------------------------
# @upload_bp.route("/delete", methods=["DELETE"])
# @jwt_required()
# def delete_file():
#     try:
#         # ✅ OPTIONAL: Get user info if you want to verify ownership
#         user_id = get_jwt_identity()  # Returns string user ID
        
#         data = request.get_json()
#         file_url = data.get("url")
        
#         if not file_url:
#             return jsonify({"error": "File URL is required"}), 400
        
#         # Extract filename from URL
#         # Assuming URL format: /uploads/images/filename or /uploads/videos/filename
#         if '/uploads/images/' in file_url:
#             filename = file_url.split('/uploads/images/')[-1]
#             file_path = os.path.join(UPLOAD_FOLDER, 'images', filename)
#         elif '/uploads/videos/' in file_url:
#             filename = file_url.split('/uploads/videos/')[-1]
#             file_path = os.path.join(UPLOAD_FOLDER, 'videos', filename)
#         else:
#             return jsonify({"error": "Invalid file URL"}), 400
        
#         # Check if file exists and delete
#         if os.path.exists(file_path):
#             os.remove(file_path)
#             return jsonify({"message": "File deleted successfully"}), 200
#         else:
#             return jsonify({"error": "File not found"}), 404
        
#     except Exception as e:
#         return jsonify({"error": f"Failed to delete file: {str(e)}"}), 500

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime

upload_bp = Blueprint("upload", __name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'wmv', 'webm'}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB

def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_file_extension(filename):
    """Get file extension"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

def generate_unique_filename(original_filename):
    """Generate unique filename to avoid collisions"""
    ext = get_file_extension(original_filename)
    unique_name = f"{uuid.uuid4().hex}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{ext}"
    return unique_name

# ---------------------------
# DEBUG ENDPOINT - Check what backend receives
# ---------------------------
@upload_bp.route("/debug", methods=["POST"])
@jwt_required()
def debug_upload():
    """Debug endpoint to see what the backend is receiving"""
    print("\n=== DEBUG UPLOAD ENDPOINT ===")
    print("Request method:", request.method)
    print("Request content type:", request.content_type)
    print("Request headers:", dict(request.headers))
    print("Request.files:", request.files)
    print("Request.files keys:", list(request.files.keys()))
    print("Request.form:", dict(request.form))
    print("Request.data length:", len(request.data))
    
    # Try to get files with different keys
    files_check = {}
    for key in ['files', 'file', 'images', 'image']:
        files_check[key] = key in request.files
        if key in request.files:
            files_list = request.files.getlist(key)
            print(f"Found {len(files_list)} files with key '{key}'")
    
    return jsonify({
        "content_type": request.content_type,
        "has_files": bool(request.files),
        "files_keys": list(request.files.keys()),
        "form_keys": list(request.form.keys()),
        "files_check": files_check,
        "data_length": len(request.data)
    }), 200

# ---------------------------
# UPLOAD MULTIPLE IMAGES - FIXED
# ---------------------------
@upload_bp.route("/images/multiple", methods=["POST", "OPTIONS"])
@jwt_required()
def upload_multiple_images():
    try:
        # Handle preflight
        if request.method == "OPTIONS":
            return jsonify({"message": "OK"}), 200
        
        print("\n=== UPLOAD MULTIPLE IMAGES ===")
        print("Content-Type:", request.content_type)
        print("Request.files:", request.files)
        print("Request.files.keys():", list(request.files.keys()))
        
        user_id = get_jwt_identity()
        
        # Try multiple possible field names
        files = None
        for field_name in ['files', 'images', 'file']:
            if field_name in request.files:
                files = request.files.getlist(field_name)
                print(f"Found {len(files)} files with field name: {field_name}")
                break
        
        if not files:
            print("ERROR: No files found in request")
            print("Available keys:", list(request.files.keys()))
            return jsonify({
                "error": "No files provided",
                "debug": {
                    "content_type": request.content_type,
                    "files_keys": list(request.files.keys()),
                    "form_keys": list(request.form.keys())
                }
            }), 400
        
        if len(files) == 0:
            return jsonify({"error": "No files selected"}), 400
        
        if len(files) > 20:
            return jsonify({"error": "Maximum 20 files allowed"}), 400
        
        uploaded_files = []
        errors = []
        
        # Create upload directory if it doesn't exist
        images_folder = os.path.join(UPLOAD_FOLDER, 'images')
        os.makedirs(images_folder, exist_ok=True)
        
        for file in files:
            try:
                print(f"Processing file: {file.filename}")
                
                # Validate file
                if file.filename == '':
                    continue
                
                if not allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
                    errors.append(f"{file.filename}: Invalid file type")
                    continue
                
                # Check file size
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)
                
                print(f"File size: {file_size} bytes")
                
                if file_size > MAX_IMAGE_SIZE:
                    errors.append(f"{file.filename}: File too large")
                    continue
                
                # Generate unique filename and save
                unique_filename = generate_unique_filename(file.filename)
                file_path = os.path.join(images_folder, unique_filename)
                file.save(file_path)
                
                print(f"Saved file: {file_path}")
                
                file_url = f"/uploads/images/{unique_filename}"
                uploaded_files.append({
                    "original_name": file.filename,
                    "url": file_url,
                    "filename": unique_filename,
                    "mimetype": file.content_type,
                    "size": file_size
                })
                
            except Exception as e:
                print(f"Error processing file {file.filename}: {str(e)}")
                errors.append(f"{file.filename}: {str(e)}")
        
        print(f"Successfully uploaded {len(uploaded_files)} files")
        
        return jsonify({
            "message": f"Uploaded {len(uploaded_files)} files successfully",
            "files": uploaded_files,
            "errors": errors if errors else None
        }), 201
        
    except Exception as e:
        print(f"ERROR in upload_multiple_images: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to upload files: {str(e)}"}), 500

# ---------------------------
# UPLOAD IMAGE (Single)
# ---------------------------
@upload_bp.route("/image", methods=["POST"])
@jwt_required()
def upload_image():
    try:
        user_id = get_jwt_identity()
        
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
            return jsonify({
                "error": f"Invalid file type. Allowed types: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
            }), 400
        
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_IMAGE_SIZE:
            return jsonify({"error": "File too large. Maximum size is 5MB"}), 400
        
        images_folder = os.path.join(UPLOAD_FOLDER, 'images')
        os.makedirs(images_folder, exist_ok=True)
        
        unique_filename = generate_unique_filename(file.filename)
        file_path = os.path.join(images_folder, unique_filename)
        file.save(file_path)
        
        file_url = f"/uploads/images/{unique_filename}"
        
        return jsonify({
            "message": "Image uploaded successfully",
            "url": file_url,
            "filename": unique_filename
        }), 201
        
    except Exception as e:
        return jsonify({"error": f"Failed to upload image: {str(e)}"}), 500

# Other routes remain the same...
# (Keep your video upload and delete routes as they are)