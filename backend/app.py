# app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from config import MONGO_URI, DATABASE_NAME

app = Flask(__name__)
CORS(app)  # allow Angular to talk to Flask

# MongoDB connection
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
users_collection = db["users"]

@app.route('/')
def home():
    return "Hello, House Hunting Platform!"

if __name__ == '__main__':
    app.run(debug=True)
