import os
from flask import Flask,  send_from_directory
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from config import Config
from extensions import mongo, bcrypt, jwt
from flask_cors import CORS
from routes.auth_routes import auth_bp
from routes.property_routes import property_bp
from routes.upload_routes import upload_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

     # CRITICAL: Set max content length for file uploads
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

    # Initialize extensions
    mongo.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    
    # Configure CORS for Angular frontend
    CORS(app, resources={
        r"/*": {
            "origins": ["http://localhost:4200"],  # Angular default dev server
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
            "max_age": 3600
        }
    })

    # Register blueprints

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(property_bp, url_prefix="/properties")
    app.register_blueprint(upload_bp, url_prefix="/upload")

    # Health check endpoint
    @app.route("/health", methods=["GET"])
    def health_check():
        return {"status": "healthy", "message": "Flask backend is running"}, 200
    
    # Serve uploaded files
    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        uploads_dir = os.path.join(app.root_path, 'uploads')
        return send_from_directory(uploads_dir, filename)

    return app

if __name__ == "__main__":
    app = create_app()

    # Create uploads directory if it doesn't exist
    os.makedirs('uploads/images', exist_ok=True)
    os.makedirs('uploads/videos', exist_ok=True)
    
    print("\n" + "="*50)
    print("Flask server starting...")
    print("API URL: http://localhost:5000")
    print("Uploads folder: ./uploads")
    print("="*50 + "\n")
   
    app.run(debug=True, host="0.0.0.0", port=5000)