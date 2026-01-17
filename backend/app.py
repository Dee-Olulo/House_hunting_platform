import os
from flask import Flask, app, send_from_directory, request, make_response
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from config import Config
from extensions import mongo, bcrypt, jwt
from flask_cors import CORS
from routes.auth_routes import auth_bp
from routes.property_routes import property_bp
from routes.upload_routes import upload_bp
from routes.booking_routes import booking_bp
from routes.notification_routes import notification_bp
from routes.payment_routes import payment_bp 
from routes.favourite_routes import favourite_bp
from routes.admin_routes import admin_bp

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

    # CRITICAL: Handle preflight OPTIONS requests BEFORE any other middleware
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = make_response()
            response.headers.add("Access-Control-Allow-Origin", "http://localhost:4200")
            response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
            response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
            response.headers.add("Access-Control-Allow-Credentials", "true")
            response.headers.add("Access-Control-Max-Age", "3600")
            return response, 200

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(property_bp, url_prefix="/properties")
    app.register_blueprint(upload_bp, url_prefix="/upload")
    app.register_blueprint(booking_bp, url_prefix="/bookings")  
    app.register_blueprint(notification_bp, url_prefix="/notifications") 
    app.register_blueprint(payment_bp, url_prefix="/payments")   
    app.register_blueprint(favourite_bp, url_prefix="/favourites")   
    app.register_blueprint(admin_bp, url_prefix="/admin") 
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