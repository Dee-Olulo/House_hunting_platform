# models/property.py
# Defines the structure of a Property document stored in MongoDB's 'properties' collection.
# This is a plain Python class with three responsibilities:
#   1. __init__    -> defines all fields and their default values
#   2. to_dict()   -> serializes the object for inserting/updating in MongoDB
#   3. from_dict() -> deserializes a MongoDB document back into a Property object
#
# Property lifecycle (via status field):
#   pending -> approved -> active -> inactive
#
# Moderation lifecycle (via moderation_status field):
#   pending -> pending_review -> approved | rejected

from datetime import datetime
from bson import ObjectId


class Property:
    def __init__(
        self,
        landlord_id,        # ObjectId ref to the user who owns this listing
        title,              # Short display name of the property
        description,        # Full text description shown to tenants
        property_type,      # e.g. apartment, house, studio, commercial
        # Location fields — used for display and map rendering
        address,
        city,
        state,
        zip_code,
        country,
        latitude,           # Used for map pin placement
        longitude,
        # Listing details
        price,              # Monthly rent amount
        bedrooms,
        bathrooms,
        area_sqft,
        # Media — stored as lists of file paths or URLs
        images=[],
        videos=[],
        amenities=[],       # e.g. ["parking", "wifi", "gym"]
        # Listing visibility status (controlled by landlord/admin)
        status="pending",   # pending | approved | active | inactive
        is_featured=False,  # Featured listings appear at the top of search results
        views=0,            # Incremented each time a tenant views the listing

        # ----------------------------------------------------------
        # Moderation fields (set by the automated moderation service
        # or manually by an admin during review)
        # ----------------------------------------------------------
        moderation_status="pending",    # pending | pending_review | approved | rejected
        moderation_score=0,             # Automated quality/compliance score (0-100)
        moderation_issues=[],           # List of flagged issues found during moderation
        moderation_notes="",            # Admin notes explaining a rejection or review decision
        moderated_at=None,              # Timestamp of the last moderation action
        moderated_by=None,              # ObjectId of the admin who manually reviewed it

        # Timestamps
        created_at=None,
        updated_at=None,
        last_confirmed_at=None,         # Tracks when landlord last confirmed listing is still active
        _id=None
    ):
        # Generate a new ObjectId if one is not provided (new listing)
        # Reuse the existing one if loading from the database (from_dict)
        self._id = _id or ObjectId()

        self.landlord_id = landlord_id
        self.title = title
        self.description = description
        self.property_type = property_type
        self.address = address
        self.city = city
        self.state = state
        self.zip_code = zip_code
        self.country = country
        self.latitude = latitude
        self.longitude = longitude
        self.price = price
        self.bedrooms = bedrooms
        self.bathrooms = bathrooms
        self.area_sqft = area_sqft
        self.images = images
        self.videos = videos
        self.amenities = amenities
        self.status = status
        self.is_featured = is_featured
        self.views = views

        # Moderation fields
        self.moderation_status = moderation_status
        self.moderation_score = moderation_score
        self.moderation_issues = moderation_issues
        self.moderation_notes = moderation_notes
        self.moderated_at = moderated_at
        self.moderated_by = moderated_by

        # Default timestamps to now if not provided (i.e. new document)
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.last_confirmed_at = last_confirmed_at or datetime.utcnow()

    def to_dict(self):
        """
        Converts the Property object into a plain dictionary for MongoDB operations.
        Used by routes/services when calling:
            mongo.db.properties.insert_one(property.to_dict())
            mongo.db.properties.update_one(..., {"$set": property.to_dict()})
        """
        return {
            "_id": self._id,
            "landlord_id": self.landlord_id,
            "title": self.title,
            "description": self.description,
            "property_type": self.property_type,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "country": self.country,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "price": self.price,
            "bedrooms": self.bedrooms,
            "bathrooms": self.bathrooms,
            "area_sqft": self.area_sqft,
            "images": self.images,
            "videos": self.videos,
            "amenities": self.amenities,
            "status": self.status,
            "is_featured": self.is_featured,
            "views": self.views,
            # Moderation fields
            "moderation_status": self.moderation_status,
            "moderation_score": self.moderation_score,
            "moderation_issues": self.moderation_issues,
            "moderation_notes": self.moderation_notes,
            "moderated_at": self.moderated_at,
            "moderated_by": self.moderated_by,
            # Timestamps
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_confirmed_at": self.last_confirmed_at
        }

    @staticmethod
    def from_dict(data):
        """
        Reconstructs a Property object from a raw MongoDB document (dict).
        Used when fetching a property from the database and needing to work
        with it as a Python object rather than a raw dictionary.

        Example:
            raw = mongo.db.properties.find_one({"_id": ObjectId(id)})
            property = Property.from_dict(raw)
        """
        return Property(
            landlord_id=data.get("landlord_id"),
            title=data.get("title"),
            description=data.get("description"),
            property_type=data.get("property_type"),
            address=data.get("address"),
            city=data.get("city"),
            state=data.get("state"),
            zip_code=data.get("zip_code"),
            country=data.get("country"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            price=data.get("price"),
            bedrooms=data.get("bedrooms"),
            bathrooms=data.get("bathrooms"),
            area_sqft=data.get("area_sqft"),
            images=data.get("images", []),
            videos=data.get("videos", []),
            amenities=data.get("amenities", []),
            status=data.get("status", "pending"),
            is_featured=data.get("is_featured", False),
            views=data.get("views", 0),
            # Moderation fields — default to safe values if missing in older documents
            moderation_status=data.get("moderation_status", "pending"),
            moderation_score=data.get("moderation_score", 0),
            moderation_issues=data.get("moderation_issues", []),
            moderation_notes=data.get("moderation_notes", ""),
            moderated_at=data.get("moderated_at"),
            moderated_by=data.get("moderated_by"),
            # Preserve original timestamps from the database document
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            last_confirmed_at=data.get("last_confirmed_at"),
            _id=data.get("_id")
        )