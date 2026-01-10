// src/app/tenant/services/property-search.service.ts

import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  Property,
  PropertySearchParams,
  PropertySearchResponse,
  AdvancedSearchParams,
  FilterOptions
} from '../models/property.interface';

@Injectable({
  providedIn: 'root'
})
export class PropertySearchService {
  private apiUrl = `${environment.apiUrl}/properties`;

  constructor(private http: HttpClient) {}

  /**
   * Get all properties with optional filters (GET request)
   */
  searchProperties(params: PropertySearchParams): Observable<PropertySearchResponse> {
    let httpParams = new HttpParams();

    // Add all search parameters
    if (params.city) httpParams = httpParams.set('city', params.city);
    if (params.state) httpParams = httpParams.set('state', params.state);
    if (params.min_price !== undefined) httpParams = httpParams.set('min_price', params.min_price.toString());
    if (params.max_price !== undefined) httpParams = httpParams.set('max_price', params.max_price.toString());
    if (params.bedrooms !== undefined) httpParams = httpParams.set('bedrooms', params.bedrooms.toString());
    if (params.bathrooms !== undefined) httpParams = httpParams.set('bathrooms', params.bathrooms.toString());
    if (params.property_type) httpParams = httpParams.set('property_type', params.property_type);
    if (params.status) httpParams = httpParams.set('status', params.status);
    if (params.sort_by) httpParams = httpParams.set('sort_by', params.sort_by);
    if (params.page) httpParams = httpParams.set('page', params.page.toString());
    if (params.per_page) httpParams = httpParams.set('per_page', params.per_page.toString());
    if (params.search) httpParams = httpParams.set('search', params.search);

    return this.http.get<PropertySearchResponse>(this.apiUrl, { params: httpParams });
  }

  /**
   * Advanced search with POST request (supports complex filters)
   */
  advancedSearch(params: AdvancedSearchParams): Observable<PropertySearchResponse> {
    return this.http.post<PropertySearchResponse>(`${this.apiUrl}/search`, params);
  }

  /**
   * Get a single property by ID
   */
  getPropertyById(propertyId: string): Observable<Property> {
    return this.http.get<Property>(`${this.apiUrl}/${propertyId}`);
  }

  /**
   * Get filter options (cities, states, property types, etc.)
   */
  getFilterOptions(): Observable<FilterOptions> {
    return this.http.get<FilterOptions>(`${this.apiUrl}/filters/options`);
  }

  /**
   * Get property statistics
   */
  getPropertyStats(): Observable<any> {
    return this.http.get(`${this.apiUrl}/stats`);
  }
}