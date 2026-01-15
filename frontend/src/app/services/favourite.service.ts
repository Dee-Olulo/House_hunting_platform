// src/app/services/favourite.service.ts

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject, tap } from 'rxjs';
import { environment } from '../../environments/environment.development';
import { Property } from './property.service';

export interface Favourite {
  favourite_id: string;
  added_at: string;
  property: Property;
}

export interface FavouritesResponse {
  favourites: Favourite[];
  count: number;
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface FavouriteCheckResponse {
  is_favourite: boolean;
  favourite_id: string | null;
}

@Injectable({
  providedIn: 'root'
})
export class FavouriteService {
  private API_URL = `${environment.apiUrl}/favourites`;
  
  // Track favourite IDs in memory for quick access
  private favouriteIds = new BehaviorSubject<Set<string>>(new Set());
  public favouriteIds$ = this.favouriteIds.asObservable();
  
  // Track total count
  private favouritesCount = new BehaviorSubject<number>(0);
  public favouritesCount$ = this.favouritesCount.asObservable();

  constructor(private http: HttpClient) {
    // Load initial favourites on service creation
    this.loadFavouriteIds();
  }

  /**
   * Load all favourite property IDs into memory
   */
  private loadFavouriteIds(): void {
    this.getFavourites().subscribe({
      next: (response) => {
        const ids = new Set(response.favourites.map(f => f.property._id || ''));
        this.favouriteIds.next(ids);
        this.favouritesCount.next(response.total);
      },
      error: (error) => {
        console.error('Error loading favourite IDs:', error);
      }
    });
  }

  /**
   * Add property to favourites
   */
  addToFavourites(propertyId: string): Observable<{message: string; favourite_id: string}> {
    return this.http.post<{message: string; favourite_id: string}>(
      `${this.API_URL}/`,
      { property_id: propertyId }
    ).pipe(
      tap(() => {
        // Update local state
        const currentIds = this.favouriteIds.value;
        currentIds.add(propertyId);
        this.favouriteIds.next(currentIds);
        this.favouritesCount.next(this.favouritesCount.value + 1);
      })
    );
  }

  /**
   * Remove property from favourites
   */
  removeFromFavourites(propertyId: string): Observable<{message: string}> {
    return this.http.delete<{message: string}>(`${this.API_URL}/${propertyId}`).pipe(
      tap(() => {
        // Update local state
        const currentIds = this.favouriteIds.value;
        currentIds.delete(propertyId);
        this.favouriteIds.next(currentIds);
        this.favouritesCount.next(Math.max(0, this.favouritesCount.value - 1));
      })
    );
  }

  /**
   * Toggle favourite status
   */
  toggleFavourite(propertyId: string): Observable<any> {
    const isFavourite = this.favouriteIds.value.has(propertyId);
    
    if (isFavourite) {
      return this.removeFromFavourites(propertyId);
    } else {
      return this.addToFavourites(propertyId);
    }
  }

  /**
   * Get all favourites with pagination
   */
  getFavourites(page: number = 1, perPage: number = 20): Observable<FavouritesResponse> {
    return this.http.get<FavouritesResponse>(`${this.API_URL}/`, {
      params: { page: page.toString(), per_page: perPage.toString() }
    });
  }

  /**
   * Check if property is in favourites
   */
  checkFavourite(propertyId: string): Observable<FavouriteCheckResponse> {
    return this.http.get<FavouriteCheckResponse>(`${this.API_URL}/check/${propertyId}`);
  }

  /**
   * Get favourites count
   */
  getFavouritesCount(): Observable<{count: number}> {
    return this.http.get<{count: number}>(`${this.API_URL}/count`).pipe(
      tap(response => {
        this.favouritesCount.next(response.count);
      })
    );
  }

  /**
   * Clear all favourites
   */
  clearAllFavourites(): Observable<{message: string; deleted_count: number}> {
    return this.http.delete<{message: string; deleted_count: number}>(`${this.API_URL}/clear`).pipe(
      tap(() => {
        this.favouriteIds.next(new Set());
        this.favouritesCount.next(0);
      })
    );
  }

  /**
   * Check if property is favourite (from local state)
   */
  isFavourite(propertyId: string): boolean {
    return this.favouriteIds.value.has(propertyId);
  }

  /**
   * Refresh favourites list
   */
  refreshFavourites(): void {
    this.loadFavouriteIds();
  }
}