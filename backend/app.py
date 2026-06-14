# app.py
# The application factory for the Flask backend.
# Rather than creating the app at module level, create_app() builds and returns
# it on demand. This makes testing easier and avoids circular imports.

import os
from flask import Flask, send_from_directory, request, make_response
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from config import Config
from extensions import mongo, bcrypt, jwt  # Unbound instances created in extensions.py
from flask_cors import CORS

# Each blueprint groups a feature's routes into its own module
from routes.auth_routes import auth_bp
from routes.property_routes import property_bp
from routes.upload_routes import upload_bp
from routes.booking_routes import booking_bp
from routes.notification_routes import notification_bp
from routes.favourite_routes import favourite_bp
from routes.admin_routes import admin_bp
from routes.analytics_routes import analytics_bp
from routes.subscription_routes import subscription_bp
from routes.financial_routes import financial_bp
from routes.mpesa_routes import mpesa_bp
from routes.admin_notification_routes import admin_notification_bp
from routes.review_routes import review_bp
from routes.listing_confirmation_routes import listing_confirmation_bp

# APScheduler runs background jobs on a timer without needing Celery/Redis
from apscheduler.schedulers.background import BackgroundScheduler
from services.listing_scheduler import run_listing_confirmation_check


def create_app():
    # ------------------------------------------------------------------ #
    # 1. Create the Flask app and load config from config.py              #
    # ------------------------------------------------------------------ #
    app = Flask(__name__)
    app.config.from_object(Config)

    # Cap incoming request size at 50 MB to prevent large upload abuse
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

    # ------------------------------------------------------------------ #
    # 2. Bind extensions to this app instance                             #
    # ------------------------------------------------------------------ #
    # init_app() is the second half of the two-step extension setup.
    # mongo  -> database access
    # bcrypt -> password hashing
    # jwt    -> token authentication
    mongo.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # ------------------------------------------------------------------ #
    # 3. Configure CORS (Cross-Origin Resource Sharing)                   #
    # ------------------------------------------------------------------ #
    # The Angular dev server runs on port 4200. Without CORS headers the
    # browser blocks all requests from it to this Flask server on 5000.
    CORS(app, resources={
        r"/*": {
            "origins": ["http://localhost:4200"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,  # Required when sending cookies/auth headers
            "max_age": 3600                # Browser caches preflight result for 1 hour
        }
    })

    # ------------------------------------------------------------------ #
    # 4. Handle CORS preflight requests (OPTIONS)                         #
    # ------------------------------------------------------------------ #
    # Before sending a real request, the browser sends an OPTIONS preflight
    # to check if the server allows the operation. This hook intercepts those
    # and returns the required headers immediately, before any route logic runs.
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


    # 5. Register blueprints (feature-grouped route modules)           
    # Each blueprint handles one feature area.
    # url_prefix scopes all its routes under that path, e.g. /auth/login
    app.register_blueprint(auth_bp,                  url_prefix="/auth")
    app.register_blueprint(property_bp,              url_prefix="/properties")
    app.register_blueprint(upload_bp,                url_prefix="/upload")
    app.register_blueprint(booking_bp,               url_prefix="/bookings")
    app.register_blueprint(notification_bp,          url_prefix="/notifications")
    app.register_blueprint(mpesa_bp,                 url_prefix="/mpesa")
    app.register_blueprint(favourite_bp,             url_prefix="/favourites")
    app.register_blueprint(admin_bp,                 url_prefix="/admin")
    app.register_blueprint(analytics_bp,             url_prefix="/analytics")
    app.register_blueprint(subscription_bp,          url_prefix="/subscription")
    app.register_blueprint(financial_bp,             url_prefix="/financial")
    app.register_blueprint(admin_notification_bp,    url_prefix="/admin/notifications")
    app.register_blueprint(review_bp,                url_prefix="/reviews")
    app.register_blueprint(listing_confirmation_bp,  url_prefix="/listing-confirmation")

    # 6. Utility routes                                                   
    # Simple liveness check — useful for Docker health checks or uptime monitors
    @app.route("/health", methods=["GET"])
    def health_check():
        return {"status": "healthy", "message": "Flask backend is running"}, 200

    # Serves files stored in the local uploads/ folder (images, videos, etc.)
    # e.g. GET /uploads/images/house.jpg reads from ./uploads/images/house.jpg
    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        uploads_dir = os.path.join(app.root_path, 'uploads')
        return send_from_directory(uploads_dir, filename)

    # ------------------------------------------------------------------ #
    # 7. Background scheduler (APScheduler)                               #
    # ------------------------------------------------------------------ #
    # Runs run_listing_confirmation_check() on a timer (default every 24h).
    # The SCHEDULER_STARTED guard prevents a second scheduler from being
    # created when Flask restarts the server in debug/reload mode.
    if not app.config.get("SCHEDULER_STARTED"):
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            func=run_listing_confirmation_check,
            trigger="interval",
            hours=app.config.get("LISTING_CHECK_INTERVAL_HOURS", 24),
            id="listing_confirmation_check",
            name="Listing Confirmation Checker",
            replace_existing=True
        )

        # APScheduler runs jobs outside a request context, so mongo.db would
        # fail without this wrapper that manually pushes an app context.
        original_func = run_listing_confirmation_check

        def _job_wrapper():
            with app.app_context():
                original_func()

        scheduler.modify_job("listing_confirmation_check", func=_job_wrapper)
        scheduler.start()
        app.config["SCHEDULER_STARTED"] = True

        print(f"\n[ListingScheduler] Background scheduler started "
              f"(interval: {app.config.get('LISTING_CHECK_INTERVAL_HOURS', 24)}h)")

    return app  # Caller (create_admin.py, run.py, tests, etc.) receives the ready app


# 8. Direct execution entry point                                     
# Only runs when you do: python app.py
# Production deployments (gunicorn, etc.) call create_app() directly
# and never reach this block.
if __name__ == "__main__":
    app = create_app()

    # Ensure upload directories exist before the server starts accepting files
    os.makedirs('uploads/images', exist_ok=True)
    os.makedirs('uploads/videos', exist_ok=True)

    print("\n" + "="*50)
    print("Flask server starting...")
    print("API URL: http://localhost:5000")
    print("Uploads folder: ./uploads")
    print("="*50 + "\n")

    # host="0.0.0.0" makes the server reachable on the local network,
    # not just localhost. debug=True enables auto-reload on code changes.
    app.run(debug=True, host="0.0.0.0", port=5000)