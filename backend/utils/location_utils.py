# utils/location_utils.py

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from geopy.distance import geodesic
import time

# Initialize geocoder with a user agent (required by Nominatim)
geolocator = Nominatim(user_agent="house_hunting_app")

def geocode_address(address, city=None, state=None, country=None):
    """
    Convert address to latitude/longitude coordinates
    
    Args:
        address: Street address
        city: City name (optional)
        state: State/Province (optional)
        country: Country (optional)
    
    Returns:
        dict: {"latitude": float, "longitude": float, "formatted_address": str}
        or None if geocoding fails
    """
    try:
        # Build full address string
        address_parts = [address]
        if city:
            address_parts.append(city)
        if state:
            address_parts.append(state)
        if country:
            address_parts.append(country)
        
        full_address = ", ".join(address_parts)
        
        # Geocode the address with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                location = geolocator.geocode(full_address, timeout=10)
                
                if location:
                    return {
                        "latitude": location.latitude,
                        "longitude": location.longitude,
                        "formatted_address": location.address
                    }
                else:
                    return None
                    
            except GeocoderTimedOut:
                if attempt < max_retries - 1:
                    time.sleep(1)  # Wait before retry
                    continue
                else:
                    print(f"Geocoding timed out after {max_retries} attempts")
                    return None
                    
    except GeocoderServiceError as e:
        print(f"Geocoding service error: {str(e)}")
        return None
    except Exception as e:
        print(f"Unexpected geocoding error: {str(e)}")
        return None


def reverse_geocode(latitude, longitude):
    """
    Convert latitude/longitude to address
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
    
    Returns:
        dict: {"address": str, "city": str, "state": str, "country": str}
        or None if reverse geocoding fails
    """
    try:
        # Reverse geocode with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                location = geolocator.reverse(
                    f"{latitude}, {longitude}", 
                    timeout=10,
                    language="en"
                )
                
                if location:
                    address_data = location.raw.get('address', {})
                    
                    # Extract address components
                    road = address_data.get('road', '')
                    house_number = address_data.get('house_number', '')
                    suburb = address_data.get('suburb', '')
                    
                    # Build street address
                    street_parts = [house_number, road]
                    street_address = " ".join([p for p in street_parts if p])
                    
                    return {
                        "address": street_address or location.address.split(',')[0],
                        "city": address_data.get('city') or address_data.get('town') or address_data.get('village', ''),
                        "state": address_data.get('state', ''),
                        "country": address_data.get('country', ''),
                        "formatted_address": location.address,
                        "zip_code": address_data.get('postcode', '')
                    }
                else:
                    return None
                    
            except GeocoderTimedOut:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                else:
                    print(f"Reverse geocoding timed out after {max_retries} attempts")
                    return None
                    
    except GeocoderServiceError as e:
        print(f"Reverse geocoding service error: {str(e)}")
        return None
    except Exception as e:
        print(f"Unexpected reverse geocoding error: {str(e)}")
        return None


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two coordinates in kilometers
    
    Args:
        lat1, lon1: First coordinate
        lat2, lon2: Second coordinate
    
    Returns:
        float: Distance in kilometers
    """
    try:
        point1 = (lat1, lon1)
        point2 = (lat2, lon2)
        distance = geodesic(point1, point2).kilometers
        return round(distance, 2)
    except Exception as e:
        print(f"Error calculating distance: {str(e)}")
        return None


def find_properties_nearby(properties, center_lat, center_lon, radius_km=10):
    """
    Filter properties within a radius from a center point
    
    Args:
        properties: List of property documents
        center_lat: Center latitude
        center_lon: Center longitude
        radius_km: Search radius in kilometers (default 10km)
    
    Returns:
        list: Properties within radius with distance added
    """
    nearby_properties = []
    
    for property_doc in properties:
        if property_doc.get('latitude') and property_doc.get('longitude'):
            distance = calculate_distance(
                center_lat, center_lon,
                property_doc['latitude'], property_doc['longitude']
            )
            
            if distance and distance <= radius_km:
                property_doc['distance_km'] = distance
                nearby_properties.append(property_doc)
    
    # Sort by distance
    nearby_properties.sort(key=lambda x: x.get('distance_km', float('inf')))
    
    return nearby_properties


def validate_coordinates(latitude, longitude):
    """
    Validate latitude and longitude values
    
    Args:
        latitude: Latitude value
        longitude: Longitude value
    
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    try:
        lat = float(latitude)
        lon = float(longitude)
        
        if lat < -90 or lat > 90:
            return False, "Latitude must be between -90 and 90"
        
        if lon < -180 or lon > 180:
            return False, "Longitude must be between -180 and 180"
        
        return True, None
        
    except (ValueError, TypeError):
        return False, "Invalid coordinate format"


def get_bounding_box(center_lat, center_lon, radius_km):
    """
    Calculate bounding box for a circle defined by center and radius
    Useful for database queries to filter properties before distance calculation
    
    Args:
        center_lat: Center latitude
        center_lon: Center longitude
        radius_km: Radius in kilometers
    
    Returns:
        dict: {"min_lat", "max_lat", "min_lon", "max_lon"}
    """
    # Approximate degrees per kilometer
    # At equator: 1 degree latitude ≈ 111 km
    # Longitude varies by latitude
    lat_degree_km = 111.0
    lon_degree_km = 111.0 * abs(geodesic((center_lat, 0), (center_lat, 1)).kilometers / 
                                  geodesic((0, 0), (0, 1)).kilometers)
    
    lat_offset = radius_km / lat_degree_km
    lon_offset = radius_km / lon_degree_km
    
    return {
        "min_lat": center_lat - lat_offset,
        "max_lat": center_lat + lat_offset,
        "min_lon": center_lon - lon_offset,
        "max_lon": center_lon + lon_offset
    }