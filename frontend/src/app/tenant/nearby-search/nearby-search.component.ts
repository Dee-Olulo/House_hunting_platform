// src/app/tenant/nearby-search/nearby-search.component.ts

import { Component, ViewChild, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { MapComponent, MarkerData } from '../../shared/components/map/map.component';
import { LocationService, PropertyWithDistance } from '../../shared/services/location.service';

@Component({
  selector: 'app-nearby-search',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, MapComponent],
  templateUrl: './nearby-search.component.html',
  styleUrls: ['./nearby-search.component.css']
})
export class NearbySearchComponent implements OnInit {
  @ViewChild('mapComponent') mapComponent!: MapComponent;

  // Search parameters
  userLocation: { latitude: number; longitude: number } | null = null;
  radiusKm: number = 5;
  propertyType: string = '';
  minPrice: number | null = null;
  maxPrice: number | null = null;
  bedrooms: number | null = null;

  // Results
  properties: PropertyWithDistance[] = [];
  markers: MarkerData[] = [];
  totalResults: number = 0;
  
  // UI state
  isLoadingLocation: boolean = false;
  isSearching: boolean = false;
  errorMessage: string = '';
  viewMode: 'list' | 'map' = 'list';
  showFilters: boolean = false;

  // Property type options
  propertyTypes = ['apartment', 'house', 'studio', 'condo', 'townhouse', 'villa'];

  constructor(private locationService: LocationService) {}

  ngOnInit(): void {
    // Optionally get user location on component load
  }

  /**
   * Get user's current location
   */
  getUserLocation(): void {
    this.isLoadingLocation = true;
    this.errorMessage = '';

    this.locationService.getCurrentLocation().subscribe({
      next: (location) => {
        this.userLocation = location;
        this.isLoadingLocation = false;
        
        // Automatically search nearby properties
        this.searchNearby();
      },
      error: (error) => {
        this.isLoadingLocation = false;
        this.errorMessage = error.message;
        console.error('Location error:', error);
      }
    });
  }

  /**
   * Search for nearby properties
   */
  searchNearby(): void {
    if (!this.userLocation) {
      this.errorMessage = 'Please allow location access first';
      return;
    }

    this.isSearching = true;
    this.errorMessage = '';

    const searchParams = {
      latitude: this.userLocation.latitude,
      longitude: this.userLocation.longitude,
      radius_km: this.radiusKm,
      property_type: this.propertyType || undefined,
      min_price: this.minPrice || undefined,
      max_price: this.maxPrice || undefined,
      bedrooms: this.bedrooms || undefined
    };

    this.locationService.searchNearby(searchParams).subscribe({
      next: (response) => {
        this.properties = response.properties;
        this.totalResults = response.total;
        this.isSearching = false;

        // Convert properties to markers
        this.markers = this.properties.map(prop => ({
          id: prop._id,
          latitude: prop.latitude,
          longitude: prop.longitude,
          title: prop.title,
          price: prop.price,
          popup: this.createPopupContent(prop)
        }));

        // Update map with markers
        if (this.mapComponent && this.markers.length > 0) {
          this.mapComponent.addMarkers(this.markers);
        }
      },
      error: (error) => {
        this.isSearching = false;
        this.errorMessage = 'Failed to search properties. Please try again.';
        console.error('Search error:', error);
      }
    });
  }

  /**
   * Create popup content for map markers
   */
  private createPopupContent(property: PropertyWithDistance): string {
    return `
      <div class="property-popup">
        <h3>${property.title}</h3>
        <p class="price">$${property.price.toLocaleString()}/month</p>
        <p>${property.bedrooms} bed • ${property.bathrooms} bath</p>
        <p class="distance">
          <i class="fas fa-location-arrow"></i> 
          ${this.locationService.formatDistance(property.distance_km)} away
        </p>
      </div>
    `;
  }

  /**
   * Navigate to property in maps app
   */
  navigateToProperty(property: PropertyWithDistance): void {
    this.locationService.openInMaps(
      property.latitude,
      property.longitude,
      property.title
    );
  }

  /**
   * Toggle view mode
   */
  toggleViewMode(): void {
    this.viewMode = this.viewMode === 'list' ? 'map' : 'list';
  }

  /**
   * Toggle filters
   */
  toggleFilters(): void {
    this.showFilters = !this.showFilters;
  }

  /**
   * Reset filters
   */
  resetFilters(): void {
    this.radiusKm = 5;
    this.propertyType = '';
    this.minPrice = null;
    this.maxPrice = null;
    this.bedrooms = null;
    
    if (this.userLocation) {
      this.searchNearby();
    }
  }

  /**
   * Format price
   */
  formatPrice(price: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(price);
  }

  /**
   * Format distance
   */
  formatDistance(distanceKm: number): string {
    return this.locationService.formatDistance(distanceKm);
  }
}