// src/app/landlord/location-picker/location-picker.component.ts

import { Component, Input, Output, EventEmitter, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MapComponent } from '../../shared/components/map/map.component';
import { LocationService } from '../../shared/services/location.service';

export interface LocationData {
  latitude: number | null;
  longitude: number | null;
  address: string;
  city: string;
  state: string;
  country: string;
  zip_code?: string;
}

@Component({
  selector: 'app-location-picker',
  standalone: true,
  imports: [CommonModule, FormsModule, MapComponent],
  template: `
    <div class="location-picker">
      <h3>Property Location</h3>
      
      <!-- Address Input -->
      <div class="address-section">
        <div class="form-row">
          <div class="form-group">
            <label>Street Address *</label>
            <input
              type="text"
              [(ngModel)]="locationData.address"
              placeholder="123 Main Street"
              class="form-control"
              (blur)="onAddressChange()"
            />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>City *</label>
            <input
              type="text"
              [(ngModel)]="locationData.city"
              placeholder="New York"
              class="form-control"
              (blur)="onAddressChange()"
            />
          </div>
          <div class="form-group">
            <label>State/Province *</label>
            <input
              type="text"
              [(ngModel)]="locationData.state"
              placeholder="NY"
              class="form-control"
              (blur)="onAddressChange()"
            />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>ZIP/Postal Code</label>
            <input
              type="text"
              [(ngModel)]="locationData.zip_code"
              placeholder="10001"
              class="form-control"
            />
          </div>
          <div class="form-group">
            <label>Country *</label>
            <input
              type="text"
              [(ngModel)]="locationData.country"
              placeholder="USA"
              class="form-control"
              (blur)="onAddressChange()"
            />
          </div>
        </div>

        <button 
          class="geocode-btn"
          (click)="geocodeAddress()"
          [disabled]="isGeocoding || !canGeocode()"
        >
          <i class="fas" [ngClass]="isGeocoding ? 'fa-spinner fa-spin' : 'fa-map-marker-alt'"></i>
          {{ isGeocoding ? 'Finding location...' : 'Find on Map' }}
        </button>
      </div>

      <!-- Coordinates Display -->
      <div class="coordinates-section" *ngIf="locationData.latitude && locationData.longitude">
        <div class="coordinates-display">
          <span class="label">Coordinates:</span>
          <span class="value">
            {{ locationData.latitude.toFixed(6) }}, {{ locationData.longitude.toFixed(6) }}
          </span>
          <button class="clear-btn" (click)="clearLocation()" title="Clear location">
            <i class="fas fa-times"></i>
          </button>
        </div>
      </div>

      <!-- Error Message -->
      <div class="error-message" *ngIf="errorMessage">
        <i class="fas fa-exclamation-circle"></i>
        {{ errorMessage }}
      </div>

      <!-- Success Message -->
      <div class="success-message" *ngIf="successMessage">
        <i class="fas fa-check-circle"></i>
        {{ successMessage }}
      </div>

      <!-- Map -->
      <div class="map-section">
        <div class="map-instructions">
          <i class="fas fa-info-circle"></i>
          <span>Click on the map to set property location, or enter address above to find it automatically</span>
        </div>
        
        <app-map
          #mapComponent
          [height]="'500px'"
          [centerLat]="mapCenter.lat"
          [centerLng]="mapCenter.lng"
          [zoom]="13"
          [clickable]="true"
          (mapClick)="onMapClick($event)"
        ></app-map>
      </div>
    </div>
  `,
  styles: [`
    .location-picker {
      background: white;
      border-radius: 12px;
      padding: 24px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }

    h3 {
      margin: 0 0 20px 0;
      color: #2c3e50;
      font-size: 1.3rem;
    }

    .address-section {
      margin-bottom: 20px;
    }

    .form-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 15px;
      margin-bottom: 15px;
    }

    .form-row:first-child {
      grid-template-columns: 1fr;
    }

    .form-group {
      display: flex;
      flex-direction: column;
    }

    .form-group label {
      margin-bottom: 6px;
      color: #34495e;
      font-weight: 600;
      font-size: 0.9rem;
    }

    .form-control {
      padding: 10px 12px;
      border: 2px solid #e0e0e0;
      border-radius: 6px;
      font-size: 1rem;
      transition: border-color 0.3s;
    }

    .form-control:focus {
      outline: none;
      border-color: #3498db;
    }

    .geocode-btn {
      padding: 12px 24px;
      background: #3498db;
      color: white;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      font-weight: 600;
      font-size: 1rem;
      transition: background 0.3s;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .geocode-btn:hover:not(:disabled) {
      background: #2980b9;
    }

    .geocode-btn:disabled {
      background: #95a5a6;
      cursor: not-allowed;
    }

    .geocode-btn i {
      font-size: 1rem;
    }

    .coordinates-section {
      margin: 15px 0;
    }

    .coordinates-display {
      background: #ecf0f1;
      padding: 12px 16px;
      border-radius: 6px;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .coordinates-display .label {
      font-weight: 600;
      color: #34495e;
    }

    .coordinates-display .value {
      color: #2c3e50;
      font-family: monospace;
      flex: 1;
    }

    .clear-btn {
      background: #e74c3c;
      color: white;
      border: none;
      border-radius: 4px;
      padding: 6px 10px;
      cursor: pointer;
      transition: background 0.3s;
    }

    .clear-btn:hover {
      background: #c0392b;
    }

    .error-message, .success-message {
      padding: 12px 16px;
      border-radius: 6px;
      margin: 15px 0;
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 0.95rem;
    }

    .error-message {
      background: #fee;
      color: #c0392b;
      border: 1px solid #f5c6cb;
    }

    .success-message {
      background: #d4edda;
      color: #155724;
      border: 1px solid #c3e6cb;
    }

    .map-section {
      margin-top: 20px;
    }

    .map-instructions {
      background: #e8f4f8;
      padding: 12px 16px;
      border-radius: 6px;
      margin-bottom: 15px;
      display: flex;
      align-items: center;
      gap: 10px;
      color: #2c3e50;
      font-size: 0.9rem;
    }

    .map-instructions i {
      color: #3498db;
      font-size: 1.1rem;
    }

    @media (max-width: 768px) {
      .form-row {
        grid-template-columns: 1fr;
      }

      .location-picker {
        padding: 16px;
      }
    }
  `]
})
export class LocationPickerComponent {
  @Input() locationData: LocationData = {
    latitude: null,
    longitude: null,
    address: '',
    city: '',
    state: '',
    country: ''
  };

  @Output() locationChange = new EventEmitter<LocationData>();
  @ViewChild('mapComponent') mapComponent!: MapComponent;

  mapCenter = { lat: 40.7128, lng: -74.0060 }; // Default: New York
  isGeocoding = false;
  errorMessage = '';
  successMessage = '';

  constructor(private locationService: LocationService) {}

  /**
   * Check if we can geocode (have enough address info)
   */
  canGeocode(): boolean {
    return !!(
      this.locationData.address &&
      this.locationData.city &&
      this.locationData.country
    );
  }

  /**
   * Geocode address when user enters it
   */
  geocodeAddress(): void {
    if (!this.canGeocode()) {
      this.errorMessage = 'Please enter at least address, city, and country';
      return;
    }

    this.isGeocoding = true;
    this.errorMessage = '';
    this.successMessage = '';

    this.locationService.geocodeAddress(
      this.locationData.address,
      this.locationData.city,
      this.locationData.state,
      this.locationData.country
    ).subscribe({
      next: (result) => {
        this.isGeocoding = false;
        
        if (result.success && result.data) {
          this.locationData.latitude = result.data.latitude;
          this.locationData.longitude = result.data.longitude;
          
          // Update map
          this.mapCenter = {
            lat: result.data.latitude,
            lng: result.data.longitude
          };
          
          // Add marker to map
          if (this.mapComponent) {
            this.mapComponent.addSingleMarker(
              result.data.latitude,
              result.data.longitude,
              true
            );
          }
          
          this.successMessage = 'Location found successfully!';
          this.locationChange.emit(this.locationData);
          
          // Clear success message after 3 seconds
          setTimeout(() => {
            this.successMessage = '';
          }, 3000);
        } else {
          this.errorMessage = result.error || 'Could not find location. Please check the address.';
        }
      },
      error: (error) => {
        this.isGeocoding = false;
        this.errorMessage = 'Failed to geocode address. Please try again.';
        console.error('Geocoding error:', error);
      }
    });
  }

  /**
   * Auto-geocode when address changes (with debounce)
   */
  private geocodeTimeout: any;
  onAddressChange(): void {
    clearTimeout(this.geocodeTimeout);
    
    if (this.canGeocode()) {
      this.geocodeTimeout = setTimeout(() => {
        this.geocodeAddress();
      }, 1000); // Wait 1 second after user stops typing
    }
  }

  /**
   * Handle map click
   */
  onMapClick(event: { latitude: number; longitude: number }): void {
    this.locationData.latitude = event.latitude;
    this.locationData.longitude = event.longitude;
    
    // Reverse geocode to get address
    this.errorMessage = '';
    this.successMessage = 'Location selected! Getting address...';
    
    this.locationService.reverseGeocode(event.latitude, event.longitude).subscribe({
      next: (result) => {
        if (result.success && result.data) {
          // Update address fields
          this.locationData.address = result.data.address;
          this.locationData.city = result.data.city;
          this.locationData.state = result.data.state;
          this.locationData.country = result.data.country;
          this.locationData.zip_code = result.data.zip_code;
          
          this.successMessage = 'Location and address updated!';
          this.locationChange.emit(this.locationData);
          
          setTimeout(() => {
            this.successMessage = '';
          }, 3000);
        }
      },
      error: (error) => {
        console.error('Reverse geocoding error:', error);
        // Still emit location even if reverse geocode fails
        this.successMessage = 'Location selected!';
        this.locationChange.emit(this.locationData);
      }
    });
  }

  /**
   * Clear location data
   */
  clearLocation(): void {
    this.locationData.latitude = null;
    this.locationData.longitude = null;
    this.errorMessage = '';
    this.successMessage = '';
    this.locationChange.emit(this.locationData);
  }
}