from datetime import datetime
from bson import ObjectId

class Property:
    def __init__(
        self,
        landlord_id,
        title,
        description,
        property_type,
        address,
        city,
        state,
        zip_code,
        country,
        latitude,
        longitude,
        price,
        bedrooms,
        bathrooms,
        area_sqft,
        images=[],
        videos=[],
        amenities=[],
        status="active",
        is_featured=False,
        views=0,
        created_at=None,
        updated_at=None,
        last_confirmed_at=None,
        _id=None
    ):
        self._id = _id or ObjectId()
        self.landlord_id = landlord_id
        self.title = title
        self.description = description
        self.property_type = property_type  # apartment, house, studio, etc.
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
        self.images = images  # List of image URLs
        self.videos = videos  # List of video URLs
        self.amenities = amenities  # List of amenities
        self.status = status  # active, inactive, pending, expired
        self.is_featured = is_featured
        self.views = views
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.last_confirmed_at = last_confirmed_at or datetime.utcnow()

    def to_dict(self):
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
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_confirmed_at": self.last_confirmed_at
        }

    @staticmethod
    def from_dict(data):
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
            status=data.get("status", "active"),
            is_featured=data.get("is_featured", False),
            views=data.get("views", 0),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            last_confirmed_at=data.get("last_confirmed_at"),
            _id=data.get("_id")
        )