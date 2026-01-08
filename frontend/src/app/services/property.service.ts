import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment.development';

export interface Property {
  _id?: string;
  landlord_id?: string;
  title: string;
  description: string;
  property_type: string;
  address: string;
  city: string;
  state: string;
  zip_code: string;
  country: string;
  latitude?: number;
  longitude?: number;
  price: number;
  bedrooms: number;
  bathrooms: number;
  area_sqft: number;
  images?: string[];
  videos?: string[];
  amenities?: string[];
  status?: string;
  is_featured?: boolean;
  views?: number;
  created_at?: string;
  updated_at?: string;
  last_confirmed_at?: string;
}

export interface PropertyResponse {
  properties: Property[];
  count: number;
}

export interface CreatePropertyResponse {
  message: string;
  property_id: string;
}

export interface PropertyFilters {
  city?: string;
  min_price?: number;
  max_price?: number;
  bedrooms?: number;
  property_type?: string;
  status?: string;
}

@Injectable({
  providedIn: 'root'
})
export class PropertyService {
  private API_URL = `${environment.apiUrl}/properties`;

  constructor(private http: HttpClient) {}

  // Create property
  createProperty(property: Property): Observable<CreatePropertyResponse> {
    return this.http.post<CreatePropertyResponse>(`${this.API_URL}/`, property);
  }

  // Get all properties with optional filters
  getAllProperties(filters?: PropertyFilters): Observable<PropertyResponse> {
    let params = new HttpParams();
    
    if (filters) {
      if (filters.city) params = params.set('city', filters.city);
      if (filters.min_price) params = params.set('min_price', filters.min_price.toString());
      if (filters.max_price) params = params.set('max_price', filters.max_price.toString());
      if (filters.bedrooms) params = params.set('bedrooms', filters.bedrooms.toString());
      if (filters.property_type) params = params.set('property_type', filters.property_type);
      if (filters.status) params = params.set('status', filters.status);
    }

    return this.http.get<PropertyResponse>(`${this.API_URL}/`, { params });
  }

  // Get single property
  getProperty(propertyId: string): Observable<Property> {
    return this.http.get<Property>(`${this.API_URL}/${propertyId}`);
  }

  // Get landlord's properties
  getMyProperties(): Observable<PropertyResponse> {
    return this.http.get<PropertyResponse>(`${this.API_URL}/landlord/my-properties`);
  }

  // Update property
  updateProperty(propertyId: string, updates: Partial<Property>): Observable<{message: string}> {
    return this.http.put<{message: string}>(`${this.API_URL}/${propertyId}`, updates);
  }

  // Delete property
  deleteProperty(propertyId: string): Observable<{message: string}> {
    return this.http.delete<{message: string}>(`${this.API_URL}/${propertyId}`);
  }

  // Confirm property listing
  confirmProperty(propertyId: string): Observable<{message: string}> {
    return this.http.post<{message: string}>(`${this.API_URL}/${propertyId}/confirm`, {});
  }

  // Get image URL
  getImageUrl(imagePath: string): string {
    if (!imagePath) return '';
    return imagePath.startsWith('http') ? imagePath : `${environment.apiUrl}${imagePath}`;
  }

  // Get video URL
  getVideoUrl(videoPath: string): string {
    if (!videoPath) return '';
    return videoPath.startsWith('http') ? videoPath : `${environment.apiUrl}${videoPath}`;
  }
}