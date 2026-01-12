// src/app/shared/services/location.service.ts

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, from } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface Coordinates {
  latitude: number;
  longitude: number;
}

export interface GeocodeResult {
  success: boolean;
  data?: {
    latitude: number;
    longitude: number;
    formatted_address: string;
  };
  error?: string;
}

export interface ReverseGeocodeResult {
  success: boolean;
  data?: {
    address: string;
    city: string;
    state: string;
    country: string;
    zip_code: string;
    formatted_address: string;
  };
  error?: string;
}

export interface NearbySearchParams {
  latitude: number;
  longitude: number;
  radius_km?: number;
  property_type?: string;
  min_price?: number;
  max_price?: number;
  bedrooms?: number;
  page?: number;
  per_page?: number;
}

export interface PropertyWithDistance {
  _id: string;
  title: string;
  price: number;
  bedrooms: number;
  bathrooms: number;
  latitude: number;
  longitude: number;
  distance_km: number;
  city: string;
  state: string;
  // ... other property fields
}

export interface NearbySearchResponse {
  properties: PropertyWithDistance[];
  count: number;
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  search_center: {
    latitude: number;
    longitude: number;
    radius_km: number;
  };
}

@Injectable({
  providedIn: 'root'
})
export class LocationService {
  private apiUrl = `${environment.apiUrl}/properties`;

  constructor(private http: HttpClient) {}

  /**
   * Geocode an address to get coordinates
   */
  geocodeAddress(
    address: string,
    city?: string,
    state?: string,
    country?: string
  ): Observable<GeocodeResult> {
    return this.http.post<GeocodeResult>(`${this.apiUrl}/geocode`, {
      address,
      city,
      state,
      country
    });
  }

  /**
   * Reverse geocode coordinates to get address
   */
  reverseGeocode(latitude: number, longitude: number): Observable<ReverseGeocodeResult> {
    return this.http.post<ReverseGeocodeResult>(`${this.apiUrl}/reverse-geocode`, {
      latitude,
      longitude
    });
  }

  /**
   * Search properties near a location
   */
  searchNearby(params: NearbySearchParams): Observable<NearbySearchResponse> {
    return this.http.post<NearbySearchResponse>(`${this.apiUrl}/nearby`, params);
  }

  /**
   * Get distance from user to a specific property
   */
  getDistanceToProperty(propertyId: string, userLat: number, userLon: number): Observable<any> {
    return this.http.post(`${this.apiUrl}/${propertyId}/distance`, {
      latitude: userLat,
      longitude: userLon
    });
  }

  /**
   * Get user's current location using browser Geolocation API
   */
  getCurrentLocation(): Observable<Coordinates> {
    return from(
      new Promise<Coordinates>((resolve, reject) => {
        if (!navigator.geolocation) {
          reject(new Error('Geolocation is not supported by your browser'));
          return;
        }

        navigator.geolocation.getCurrentPosition(
          (position) => {
            resolve({
              latitude: position.coords.latitude,
              longitude: position.coords.longitude
            });
          },
          (error) => {
            reject(new Error(this.getGeolocationErrorMessage(error)));
          },
          {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 0
          }
        );
      })
    );
  }

  /**
   * Open navigation to property in native maps app
   */
  openInMaps(latitude: number, longitude: number, label?: string): void {
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    const isAndroid = /android/i.test(navigator.userAgent);

    let url: string;

    if (isIOS) {
      // Apple Maps
      url = `maps://maps.apple.com/?q=${latitude},${longitude}`;
      if (label) {
        url += `&label=${encodeURIComponent(label)}`;
      }
    } else if (isAndroid) {
      // Google Maps
      url = `geo:${latitude},${longitude}?q=${latitude},${longitude}`;
      if (label) {
        url += `(${encodeURIComponent(label)})`;
      }
    } else {
      // Desktop - Google Maps web
      url = `https://www.google.com/maps/search/?api=1&query=${latitude},${longitude}`;
    }

    window.open(url, '_blank');
  }

  /**
   * Calculate distance between two coordinates (Haversine formula)
   * Returns distance in kilometers
   */
  calculateDistance(
    lat1: number,
    lon1: number,
    lat2: number,
    lon2: number
  ): number {
    const R = 6371; // Radius of Earth in kilometers
    const dLat = this.toRad(lat2 - lat1);
    const dLon = this.toRad(lon2 - lon1);
    
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(this.toRad(lat1)) *
        Math.cos(this.toRad(lat2)) *
        Math.sin(dLon / 2) *
        Math.sin(dLon / 2);
    
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    const distance = R * c;
    
    return Math.round(distance * 100) / 100; // Round to 2 decimal places
  }

  /**
   * Format distance for display
   */
  formatDistance(distanceKm: number): string {
    if (distanceKm < 1) {
      return `${Math.round(distanceKm * 1000)} m`;
    } else {
      return `${distanceKm.toFixed(1)} km`;
    }
  }

  /**
   * Validate coordinates
   */
  validateCoordinates(latitude: number, longitude: number): { valid: boolean; error?: string } {
    if (latitude < -90 || latitude > 90) {
      return { valid: false, error: 'Latitude must be between -90 and 90' };
    }
    if (longitude < -180 || longitude > 180) {
      return { valid: false, error: 'Longitude must be between -180 and 180' };
    }
    return { valid: true };
  }

  private toRad(degrees: number): number {
    return degrees * (Math.PI / 180);
  }

  private getGeolocationErrorMessage(error: GeolocationPositionError): string {
    switch (error.code) {
      case error.PERMISSION_DENIED:
        return 'Location access denied. Please enable location permissions in your browser.';
      case error.POSITION_UNAVAILABLE:
        return 'Location information unavailable.';
      case error.TIMEOUT:
        return 'Location request timed out.';
      default:
        return 'An unknown error occurred while getting location.';
    }
  }
}