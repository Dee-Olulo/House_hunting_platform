# app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from pymongo import MongoClient
from config import MONGO_URI, DATABASE_NAME

app = Flask(__name__)
CORS(app)
jwt = JWTManager()

# MongoDB connection
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
users_collection = db["users"]


@app.route("/")
def home():
    return "Server is running!"

# Run the app only if this file is executed directly
if __name__ == "__main__":
    app.run(debug=True)




from flask import Flask
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from config import Config

# Initialize extensions here (without app)
mongo = PyMongo()
jwt = JWTManager()

def create_app():
    # Create Flask app
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions with app
    mongo.init_app(app)
    jwt.init_app(app)

    # Import and register blueprints here to avoid circular imports
    from auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    @app.route("/")
    def home():
        return "Server is running!"


    return app

# Run app
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
