
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import uuid
from datetime import datetime

from utils.cloudinary_helper import (
    upload_image_to_cloudinary,
    upload_video_to_cloudinary,
    upload_multiple_images as cloudinary_upload_multiple_images,
    upload_multiple_videos as cloudinary_upload_multiple_videos,
    delete_from_cloudinary
)

upload_bp = Blueprint("upload", __name__)

# =========================
# CONFIGURATION
# =========================
UPLOAD_FOLDER = "uploads"

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "avi", "mov", "wmv", "webm"}

MAX_IMAGE_SIZE = 5 * 1024 * 1024      # 5MB
MAX_VIDEO_SIZE = 50 * 1024 * 1024     # 50MB


# =========================
# HELPERS
# =========================
def allowed_file(filename, allowed_extensions):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def generate_unique_filename(filename):
    ext = filename.rsplit(".", 1)[1].lower()
    return f"{uuid.uuid4().hex}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{ext}"


# =========================
# DEBUG ENDPOINT
# =========================
@upload_bp.route("/debug", methods=["POST"])
@jwt_required()
def debug_upload():
    print("\n=== DEBUG UPLOAD ===")
    print("Content-Type:", request.content_type)
    print("Files:", request.files)
    print("Keys:", list(request.files.keys()))

    return jsonify({
        "content_type": request.content_type,
        "files_keys": list(request.files.keys()),
        "has_files": bool(request.files)
    }), 200


# =========================
# IMAGES (MULTIPLE - LOCAL)
# =========================
@upload_bp.route("/images/multiple", methods=["POST", "OPTIONS"])
@jwt_required()
def upload_multiple_images():
    if request.method == "OPTIONS":
        return jsonify({"message": "OK"}), 200

    print("\n=== UPLOAD MULTIPLE IMAGES ===")
    print(f"Content-Type: {request.content_type}")
    print(f"Request.files: {request.files}")
    print(f"Request.files.keys(): {list(request.files.keys())}")

    files = request.files.getlist("files")
    print(f"Files count: {len(files)}")

    if not files:
        return jsonify({"error": "No images provided"}), 400

    if len(files) > 20:
        return jsonify({"error": "Maximum 20 images allowed"}), 400

    images_dir = os.path.join(UPLOAD_FOLDER, "images")
    os.makedirs(images_dir, exist_ok=True)

    uploaded_files = []
    errors = []

    for file in files:
        print(f"Processing file: {file.filename}")
        
        if file.filename == "":
            continue

        if not allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
            errors.append(f"{file.filename}: Invalid image type")
            continue

        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        print(f"File size: {size} bytes")

        if size > MAX_IMAGE_SIZE:
            errors.append(f"{file.filename}: Image too large")
            continue

        filename = generate_unique_filename(file.filename)
        path = os.path.join(images_dir, filename)
        file.save(path)
        print(f"Saved file: {path}")

        uploaded_files.append({
            "original_name": file.filename,
            "filename": filename,
            "url": f"/uploads/images/{filename}",
            "size": size,
            "mimetype": file.content_type
        })

    print(f"Successfully uploaded {len(uploaded_files)} files")
    
    return jsonify({
        "message": f"Uploaded {len(uploaded_files)} images",
        "files": uploaded_files,
        "errors": errors or None
    }), 201


# =========================
# IMAGE (SINGLE)
# =========================
@upload_bp.route("/image", methods=["POST"])
@jwt_required()
def upload_single_image():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
        return jsonify({"error": "Invalid image type"}), 400

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)

    if size > MAX_IMAGE_SIZE:
        return jsonify({"error": "Image too large"}), 400

    result = upload_image_to_cloudinary(file)

    return jsonify({
        "message": "Image uploaded successfully",
        **result
    }), 201


# =========================
# VIDEOS (MULTIPLE - CLOUDINARY)
# =========================
@upload_bp.route("/videos/multiple", methods=["POST", "OPTIONS"])
@jwt_required()
def upload_multiple_videos():
    if request.method == "OPTIONS":
        return jsonify({"message": "OK"}), 200

    print("\n=== UPLOAD MULTIPLE VIDEOS ===")
    print(f"Content-Type: {request.content_type}")
    print(f"Request.files: {request.files}")
    print(f"Request.files.keys(): {list(request.files.keys())}")

    # Get files from request
    files = request.files.getlist("files")
    print(f"Files count: {len(files)}")
    
    # Log each file received
    for i, file in enumerate(files):
        print(f"File {i+1}: name={file.filename}, content_type={file.content_type}")

    if not files:
        print("❌ No files provided in request")
        return jsonify({"error": "No videos provided"}), 400

    if len(files) > 5:
        print(f"❌ Too many files: {len(files)}")
        return jsonify({"error": "Maximum 5 videos allowed"}), 400

    # Validate each file
    for file in files:
        print(f"Validating file: {file.filename}")
        
        if not allowed_file(file.filename, ALLOWED_VIDEO_EXTENSIONS):
            print(f"❌ Invalid video type: {file.filename}")
            return jsonify({"error": f"Invalid video type: {file.filename}"}), 400

        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        print(f"File size: {size} bytes ({size / 1024 / 1024:.2f} MB)")
        
        if size > MAX_VIDEO_SIZE:
            print(f"❌ File too large: {file.filename}")
            return jsonify({"error": f"{file.filename} too large (max 50MB)"}), 400

    # Upload to Cloudinary
    print("✅ All validations passed. Uploading to Cloudinary...")
    uploaded_files, errors = cloudinary_upload_multiple_videos(files)

    if errors:
        print(f"❌ Cloudinary upload errors: {errors}")
        return jsonify({
            "error": "Video upload failed",
            "details": errors
        }), 400

    print(f"✅ Successfully uploaded {len(uploaded_files)} videos")
    return jsonify({
        "message": "Videos uploaded successfully",
        "files": uploaded_files
    }), 201


# =========================
# VIDEO (SINGLE)
# =========================
@upload_bp.route("/video", methods=["POST"])
@jwt_required()
def upload_single_video():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)

    if size > MAX_VIDEO_SIZE:
        return jsonify({"error": "Video too large"}), 400

    result = upload_video_to_cloudinary(file)

    return jsonify({
        "message": "Video uploaded successfully",
        **result
    }), 201


# =========================
# DELETE (IMAGE / VIDEO)
# =========================
@upload_bp.route("/delete", methods=["DELETE"])
@jwt_required()
def delete_file():
    data = request.get_json()

    url = data.get("url")
    resource_type = data.get("resource_type", "image")

    if not url:
        return jsonify({"error": "url is required"}), 400

    success = delete_from_cloudinary(url, resource_type)

    if success:
        return jsonify({"message": "File deleted successfully"}), 200

    return jsonify({"error": "Delete failed"}), 500