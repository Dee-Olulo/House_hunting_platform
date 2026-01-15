# utils/create_indexes.py
from extensions import mongo

def create_favourites_indexes():
    """Create indexes for favourites collection"""
    # Compound index for efficient querying
    mongo.db.favourites.create_index([("user_id", 1), ("property_id", 1)], unique=True)
    # Index for querying by user
    mongo.db.favourites.create_index([("user_id", 1)])
    print("✅ Favourites indexes created")