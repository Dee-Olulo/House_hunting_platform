// src/app/shared/components/map/map.component.ts

import { Component, Input, Output, EventEmitter, OnInit, OnDestroy, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import * as L from 'leaflet';

export interface MapClickEvent {
  latitude: number;
  longitude: number;
}

export interface MarkerData {
  id: string;
  latitude: number;
  longitude: number;
  title: string;
  price?: number;
  popup?: string;
}

@Component({
  selector: 'app-map',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div [id]="mapId" class="map-container" [style.height]="height"></div>
  `,
  styles: [`
    .map-container {
      width: 100%;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }

    :host ::ng-deep .leaflet-popup-content-wrapper {
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }

    :host ::ng-deep .leaflet-popup-content {
      margin: 12px;
      font-family: inherit;
    }

    :host ::ng-deep .property-popup {
      min-width: 200px;
    }

    :host ::ng-deep .property-popup h3 {
      margin: 0 0 8px 0;
      font-size: 1rem;
      color: #2c3e50;
    }

    :host ::ng-deep .property-popup p {
      margin: 4px 0;
      font-size: 0.9rem;
      color: #7f8c8d;
    }

    :host ::ng-deep .property-popup .price {
      color: #27ae60;
      font-weight: 600;
      font-size: 1.1rem;
    }
  `]
})
export class MapComponent implements OnInit, AfterViewInit, OnDestroy {
  @Input() mapId: string = 'map-' + Math.random().toString(36).substr(2, 9);
  @Input() height: string = '400px';
  @Input() centerLat: number = 40.7128; // Default: New York
  @Input() centerLng: number = -74.0060;
  @Input() zoom: number = 13;
  @Input() clickable: boolean = false; // Allow clicking to set location
  @Input() markers: MarkerData[] = []; // Multiple markers
  @Input() showUserLocation: boolean = false;
  
  @Output() mapClick = new EventEmitter<MapClickEvent>();
  @Output() markerClick = new EventEmitter<string>(); // Emits marker ID

  private map: L.Map | null = null;
  private markersLayer: L.LayerGroup | null = null;
  private clickMarker: L.Marker | null = null;
  private userLocationMarker: L.Marker | null = null;

  ngOnInit(): void {
    // Fix for default marker icons in Leaflet
    this.fixLeafletIcons();
  }

  ngAfterViewInit(): void {
    setTimeout(() => {
      this.initializeMap();
    }, 100);
  }

  ngOnDestroy(): void {
    if (this.map) {
      this.map.remove();
      this.map = null;
    }
  }

  private initializeMap(): void {
    // Initialize map
    this.map = L.map(this.mapId).setView([this.centerLat, this.centerLng], this.zoom);

    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© OpenStreetMap contributors'
    }).addTo(this.map);

    // Initialize markers layer
    this.markersLayer = L.layerGroup().addTo(this.map);

    // Add click handler if clickable
    if (this.clickable) {
      this.map.on('click', (e: L.LeafletMouseEvent) => {
        this.onMapClick(e.latlng.lat, e.latlng.lng);
      });
    }

    // Add markers if provided
    if (this.markers && this.markers.length > 0) {
      this.addMarkers(this.markers);
    }

    // Show user location if requested
    if (this.showUserLocation) {
      this.showCurrentLocation();
    }
  }

  /**
   * Add multiple markers to map
   */
  addMarkers(markers: MarkerData[]): void {
    if (!this.map || !this.markersLayer) return;

    // Clear existing markers
    this.markersLayer.clearLayers();

    markers.forEach(marker => {
      const leafletMarker = L.marker([marker.latitude, marker.longitude], {
        icon: this.createPropertyIcon()
      });

      // Add popup if provided
      if (marker.popup) {
        leafletMarker.bindPopup(marker.popup);
      } else {
        // Create default popup
        const popupContent = `
          <div class="property-popup">
            <h3>${marker.title}</h3>
            ${marker.price ? `<p class="price">$${marker.price.toLocaleString()}/month</p>` : ''}
          </div>
        `;
        leafletMarker.bindPopup(popupContent);
      }

      // Add click handler
      leafletMarker.on('click', () => {
        this.markerClick.emit(marker.id);
      });

      leafletMarker.addTo(this.markersLayer!);
    });

    // Fit bounds to show all markers
    if (markers.length > 1) {
      const bounds = L.latLngBounds(markers.map(m => [m.latitude, m.longitude]));
      this.map!.fitBounds(bounds, { padding: [50, 50] });
    }
  }

  /**
   * Add a single marker (for location picker)
   */
  addSingleMarker(lat: number, lng: number, draggable: boolean = false): void {
    if (!this.map) return;

    // Remove previous marker
    if (this.clickMarker) {
      this.clickMarker.remove();
    }

    // Add new marker
    this.clickMarker = L.marker([lat, lng], {
      draggable: draggable,
      icon: this.createSelectedIcon()
    }).addTo(this.map);

    // Handle drag end
    if (draggable) {
      this.clickMarker.on('dragend', (e: L.DragEndEvent) => {
        const position = e.target.getLatLng();
        this.mapClick.emit({
          latitude: position.lat,
          longitude: position.lng
        });
      });
    }

    // Center map on marker
    this.map.setView([lat, lng], this.zoom);
  }

  /**
   * Show user's current location on map
   */
  private showCurrentLocation(): void {
    if (!this.map) return;

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;

        // Add user location marker
        this.userLocationMarker = L.marker([lat, lng], {
          icon: this.createUserIcon()
        })
          .bindPopup('You are here')
          .addTo(this.map!);
      },
      (error) => {
        console.error('Error getting location:', error);
      }
    );
  }

  /**
   * Handle map click
   */
  private onMapClick(lat: number, lng: number): void {
    this.addSingleMarker(lat, lng, true);
    this.mapClick.emit({ latitude: lat, longitude: lng });
  }

  /**
   * Update map center
   */
  setCenter(lat: number, lng: number, zoom?: number): void {
    if (this.map) {
      this.map.setView([lat, lng], zoom || this.zoom);
    }
  }

  /**
   * Create custom property marker icon
   */
  private createPropertyIcon(): L.Icon {
    return L.icon({
      iconUrl: 'data:image/svg+xml;base64,' + btoa(`
        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="42" viewBox="0 0 32 42">
          <path fill="#3498db" stroke="#2c3e50" stroke-width="2" d="M16 0C7.163 0 0 7.163 0 16c0 12 16 26 16 26s16-14 16-26C32 7.163 24.837 0 16 0z"/>
          <circle cx="16" cy="16" r="6" fill="white"/>
        </svg>
      `),
      iconSize: [32, 42],
      iconAnchor: [16, 42],
      popupAnchor: [0, -42]
    });
  }

  /**
   * Create custom selected location icon
   */
  private createSelectedIcon(): L.Icon {
    return L.icon({
      iconUrl: 'data:image/svg+xml;base64,' + btoa(`
        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="42" viewBox="0 0 32 42">
          <path fill="#e74c3c" stroke="#c0392b" stroke-width="2" d="M16 0C7.163 0 0 7.163 0 16c0 12 16 26 16 26s16-14 16-26C32 7.163 24.837 0 16 0z"/>
          <circle cx="16" cy="16" r="6" fill="white"/>
        </svg>
      `),
      iconSize: [32, 42],
      iconAnchor: [16, 42],
      popupAnchor: [0, -42]
    });
  }

  /**
   * Create user location icon
   */
  private createUserIcon(): L.Icon {
    return L.icon({
      iconUrl: 'data:image/svg+xml;base64,' + btoa(`
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20">
          <circle cx="10" cy="10" r="8" fill="#3498db" stroke="white" stroke-width="3"/>
          <circle cx="10" cy="10" r="4" fill="white"/>
        </svg>
      `),
      iconSize: [20, 20],
      iconAnchor: [10, 10]
    });
  }

  /**
   * Fix Leaflet default icon issue
   */
  private fixLeafletIcons(): void {
    const iconRetinaUrl = 'assets/marker-icon-2x.png';
    const iconUrl = 'assets/marker-icon.png';
    const shadowUrl = 'assets/marker-shadow.png';
    const iconDefault = L.icon({
      iconRetinaUrl,
      iconUrl,
      shadowUrl,
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
      tooltipAnchor: [16, -28],
      shadowSize: [41, 41]
    });
    L.Marker.prototype.options.icon = iconDefault;
  }
}