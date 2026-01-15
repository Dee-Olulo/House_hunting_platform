// import { Component, OnInit, ViewChild } from '@angular/core';
// import { CommonModule } from '@angular/common';
// import { ActivatedRoute, Router, RouterModule } from '@angular/router';
// import { HttpErrorResponse } from '@angular/common/http';
// import { PropertyService, Property } from '../services/property.service';
// import { AuthService } from '../services/auth';
// import { LocationService } from '../shared/services/location.service';
// import { MapComponent } from '../shared/components/map/map.component';

// @Component({
//   selector: 'app-property-details',
//   standalone: true,
//   imports: [CommonModule, RouterModule, MapComponent],
//   templateUrl: './property-details.html',
//   styleUrls: ['./property-details.css']
// })
// export class PropertyDetailsComponent implements OnInit {
//   @ViewChild(MapComponent) mapComponent!: MapComponent;
  
//   property: Property | null = null;
//   propertyId: string = '';
//   currentImageIndex = 0;
//   currentVideoIndex = 0;
//   isLoading = true;
//   errorMessage = '';
//   isLoggedIn = false;
//   userRole: string | null = null;

//   // User location for distance calculation
//   userLocation: { latitude: number; longitude: number } | null = null;
//   distanceToProperty: number | null = null;

//   constructor(
//     private route: ActivatedRoute,
//     private router: Router,
//     private propertyService: PropertyService,
//     private authService: AuthService,
//     private locationService: LocationService
//   ) {}

//   ngOnInit(): void {
//     this.propertyId = this.route.snapshot.params['id'];
//     this.isLoggedIn = this.authService.isLoggedIn();
//     this.userRole = this.authService.getUserRole();
    
//     console.log('PropertyDetailsComponent initialized');
//     console.log('Loading property:', this.propertyId);
//     console.log('User logged in:', this.isLoggedIn);
//     console.log('User role:', this.userRole);
    
//     this.loadProperty();
//     this.getUserLocation();
//   }

//   loadProperty(): void {
//     this.isLoading = true;
//     this.errorMessage = '';
    
//     console.log('Fetching property from API...');
    
//     this.propertyService.getProperty(this.propertyId).subscribe({
//       next: (property: Property) => {
//         console.log('✅ Property loaded:', property);
//         this.property = property;
//         this.isLoading = false;

//         // Initialize map with property location after property is loaded
//         if (this.property.latitude && this.property.longitude) {
//           console.log('Property has coordinates, initializing map...');
//           setTimeout(() => {
//             this.initializeMap();
//           }, 100);
//         } else {
//           console.log('Property has no coordinates for map');
//         }

//         // Calculate distance if we have user location
//         if (this.userLocation) {
//           this.calculateDistance();
//         }
//       },
//       error: (error: HttpErrorResponse) => {
//         console.error('❌ Error loading property:', error);
//         console.error('Error status:', error.status);
//         console.error('Error message:', error.error);
        
//         if (error.status === 404) {
//           this.errorMessage = 'Property not found';
//         } else if (error.status === 401) {
//           this.errorMessage = 'Please log in to view this property';
//           setTimeout(() => this.router.navigate(['/login']), 2000);
//         } else {
//           this.errorMessage = error.error?.message || 'Failed to load property. Please try again.';
//         }
        
//         this.isLoading = false;
//       }
//     });
//   }

//   /**
//    * Initialize map with property location
//    */
//   initializeMap(): void {
//     if (!this.mapComponent) {
//       console.warn('Map component not yet available');
//       return;
//     }

//     if (!this.property?.latitude || !this.property?.longitude) {
//       console.warn('Property coordinates not available');
//       return;
//     }

//     console.log('Initializing map with property location');

//     const marker = {
//       id: this.property._id || '',
//       latitude: this.property.latitude,
//       longitude: this.property.longitude,
//       title: this.property.title,
//       price: this.property.price,
//       popup: `
//         <div style="text-align: center;">
//           <h3 style="margin: 0 0 8px 0;">${this.property.title}</h3>
//           <p style="margin: 4px 0; color: #27ae60; font-weight: 600;">
//             KES ${this.property.price.toLocaleString()}/month
//           </p>
//           <p style="margin: 4px 0;">${this.property.address}</p>
//         </div>
//       `
//     };
    
//     this.mapComponent.addMarkers([marker]);
//     console.log('Map marker added');
//   }

//   /**
//    * Get user's current location
//    */
//   getUserLocation(): void {
//     console.log('Getting user location...');
    
//     this.locationService.getCurrentLocation().subscribe({
//       next: (location) => {
//         console.log('✅ User location obtained:', location);
//         this.userLocation = location;
//         this.calculateDistance();
//       },
//       error: (error: HttpErrorResponse) => {
//         console.log('Could not get user location:', error.message || error);
//         // It's okay if we can't get location
//       }
//     });
//   }

//   /**
//    * Calculate distance from user to property
//    */
//   calculateDistance(): void {
//     if (this.userLocation && this.property?.latitude && this.property?.longitude) {
//       this.distanceToProperty = this.locationService.calculateDistance(
//         this.userLocation.latitude,
//         this.userLocation.longitude,
//         this.property.latitude,
//         this.property.longitude
//       );
//       console.log('Distance to property:', this.distanceToProperty, 'km');
//     }
//   }

//   /**
//    * Open navigation to property
//    */
//   getDirections(): void {
//     if (!this.property?.latitude || !this.property?.longitude) {
//       alert('Property location not available');
//       return;
//     }

//     console.log('Opening directions to property');
//     this.locationService.openInMaps(
//       this.property.latitude,
//       this.property.longitude,
//       this.property.title
//     );
//   }

//   /**
//    * Format distance for display
//    */
//   formatDistance(distanceKm: number): string {
//     return this.locationService.formatDistance(distanceKm);
//   }

//   // ==========================================
//   // IMAGE GALLERY METHODS
//   // ==========================================

//   getImageUrl(imagePath: string): string {
//     if (!imagePath) {
//       return 'https://placehold.co/800x600?text=No+Image';
//     }
//     return this.propertyService.getImageUrl(imagePath);
//   }

//   hasImages(): boolean {
//     return !!(this.property?.images && this.property.images.length > 0);
//   }

//   nextImage(): void {
//     if (this.property && this.property.images && this.property.images.length > 0) {
//       this.currentImageIndex = (this.currentImageIndex + 1) % this.property.images.length;
//       console.log('Next image:', this.currentImageIndex);
//     }
//   }

//   previousImage(): void {
//     if (this.property && this.property.images && this.property.images.length > 0) {
//       this.currentImageIndex = this.currentImageIndex === 0 
//         ? this.property.images.length - 1 
//         : this.currentImageIndex - 1;
//       console.log('Previous image:', this.currentImageIndex);
//     }
//   }

//   selectImage(index: number): void {
//     if (index >= 0 && this.property?.images && index < this.property.images.length) {
//       this.currentImageIndex = index;
//       console.log('Selected image:', this.currentImageIndex);
//     }
//   }
   

//   /**
//    * Open image in modal (new tab for now)
//    */
//   openImageModal(index: number): void {
//     if (this.property?.images && this.property.images[index]) {
//       window.open(this.getImageUrl(this.property.images[index]), '_blank');
//     }
//   }
//   // ==========================================
//   // VIDEO GALLERY METHODS
//   // ==========================================
//   hasVideos(): boolean {
//     return !!(this.property?.videos && this.property.videos.length > 0);
//   }

//   /**
//    * Get video URL (Cloudinary URLs are already complete)
//    */
//   getVideoUrl(videoPath: string): string {
//     if (!videoPath) return '';
//     // Cloudinary URLs are already complete, just return them
//     return videoPath;
//   }

//   /**
//    * Get poster image for video
//    * Uses first property image as fallback
//    */
//   getVideoPoster(videoUrl: string): string {
//     if (this.property?.images && this.property.images.length > 0) {
//       return this.getImageUrl(this.property.images[0]);
//     }
//     return '';
//   }

//   nextVideo(): void {
//     if (this.property && this.property.videos && this.property.videos.length > 0) {
//       this.currentVideoIndex = (this.currentVideoIndex + 1) % this.property.videos.length;
//       console.log('Next video:', this.currentVideoIndex);
//     }
//   }

//   previousVideo(): void {
//     if (this.property && this.property.videos && this.property.videos.length > 0) {
//       this.currentVideoIndex = this.currentVideoIndex === 0 
//         ? this.property.videos.length - 1 
//         : this.currentVideoIndex - 1;
//       console.log('Previous video:', this.currentVideoIndex);
//     }
//   }

//   selectVideo(index: number): void {
//     if (index >= 0 && this.property?.videos && index < this.property.videos.length) {
//       this.currentVideoIndex = index;
//       console.log('Selected video:', this.currentVideoIndex);
//     }
//   }


//   contactLandlord(): void {
//     console.log('Contact landlord clicked');
    
//     if (!this.isLoggedIn) {
//       alert('Please login to contact the landlord');
//       this.router.navigate(['/login'], { 
//         queryParams: { returnUrl: `/properties/${this.propertyId}` }
//       });
//       return;
//     }
    
//     // TODO: Implement contact/messaging functionality
//     alert('Contact functionality will be implemented in the messaging system.\n\nFor now, you can reach out to the property owner through the booking system.');
//   }

//   bookViewing(): void {
//   console.log('Book viewing clicked');
  
//   if (!this.isLoggedIn) {
//     alert('Please login to book a viewing');
//     this.router.navigate(['/login'], { 
//       queryParams: { returnUrl: `/properties/${this.propertyId}` }
//     });
//     return;
//   }
  
//   if (this.userRole !== 'tenant') {
//     alert('Only tenants can book property viewings');
//     return;
//   }
  
//   // Navigate to booking page with property ID
//   this.router.navigate(['/tenant/book-viewing', this.propertyId]);
// }

//   goBack(): void {
//     console.log('Going back');
//     window.history.back();
//   }

//   editProperty(): void {
//     if (!this.propertyId) {
//       console.error('Invalid property ID');
//       return;
//     }
    
//     console.log('Navigating to edit property:', this.propertyId);
//     this.router.navigate(['/landlord/properties/edit', this.propertyId]);
//   }

//   isOwner(): boolean {
//     // Check if current user is the landlord who owns this property
//     if (!this.isLoggedIn || !this.property) {
//       return false;
//     }
    
//     // Get current user ID
//     const currentUserId = localStorage.getItem('userId');
    
//     // Compare with property's landlord_id
//     const isPropertyOwner = this.property.landlord_id === currentUserId;
    
//     console.log('Ownership check:', {
//       currentUserId,
//       landlordId: this.property.landlord_id,
//       isOwner: isPropertyOwner
//     });
    
//     return isPropertyOwner && this.userRole === 'landlord';
//   }

//   // Helper method to get current image
//   getCurrentImage(): string {
//     if (this.hasImages() && this.property?.images) {
//       return this.getImageUrl(this.property.images[this.currentImageIndex]);
//     }
//     return 'https://placehold.co/800x600?text=No+Image';
//   }

//   // Helper method to check if property has amenity
//   hasAmenity(amenity: string): boolean {
//     return !!(this.property?.amenities?.includes(amenity));
//   }
// }

import { Component, OnInit, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { PropertyService, Property } from '../services/property.service';
import { AuthService } from '../services/auth';
import { LocationService } from '../shared/services/location.service';
import { MapComponent } from '../shared/components/map/map.component';

@Component({
  selector: 'app-property-details',
  standalone: true,
  imports: [CommonModule, RouterModule, MapComponent],
  templateUrl: './property-details.html',
  styleUrls: ['./property-details.css']
})
export class PropertyDetailsComponent implements OnInit {
  @ViewChild(MapComponent) mapComponent!: MapComponent;
  
  property: Property | null = null;
  propertyId: string = '';
  currentImageIndex = 0;
  currentVideoIndex = 0;
  isLoading = true;
  errorMessage = '';
  isLoggedIn = false;
  userRole: string | null = null;

  // User location for distance calculation
  userLocation: { latitude: number; longitude: number } | null = null;
  distanceToProperty: number | null = null;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private propertyService: PropertyService,
    private authService: AuthService,
    private locationService: LocationService
  ) {}
  

  ngOnInit(): void {
    this.propertyId = this.route.snapshot.params['id'];
    this.isLoggedIn = this.authService.isLoggedIn();
    this.userRole = this.authService.getUserRole();
    
    console.log('PropertyDetailsComponent initialized');
    console.log('Loading property:', this.propertyId);
    console.log('User logged in:', this.isLoggedIn);
    console.log('User role:', this.userRole);
    
    this.loadProperty();
    this.getUserLocation();
  }

  loadProperty(): void {
    this.isLoading = true;
    this.errorMessage = '';
    
    console.log('Fetching property from API...');
    
    this.propertyService.getProperty(this.propertyId).subscribe({
      next: (property: Property) => {
        console.log('✅ Property loaded:', property);
        this.property = property;
        this.isLoading = false;

        // Initialize map with property location after property is loaded
        if (this.property.latitude && this.property.longitude) {
          console.log('Property has coordinates, initializing map...');
          setTimeout(() => {
            this.initializeMap();
          }, 100);
        } else {
          console.log('Property has no coordinates for map');
        }

        // Calculate distance if we have user location
        if (this.userLocation) {
          this.calculateDistance();
        }
      },
      error: (error: HttpErrorResponse) => {
        console.error('❌ Error loading property:', error);
        console.error('Error status:', error.status);
        console.error('Error message:', error.error);
        
        if (error.status === 404) {
          this.errorMessage = 'Property not found';
        } else if (error.status === 401) {
          this.errorMessage = 'Please log in to view this property';
          setTimeout(() => this.router.navigate(['/login']), 2000);
        } else {
          this.errorMessage = error.error?.message || 'Failed to load property. Please try again.';
        }
        
        this.isLoading = false;
      }
    });
  }

  /**
   * Initialize map with property location
   */
  initializeMap(): void {
    if (!this.mapComponent) {
      console.warn('Map component not yet available');
      return;
    }

    if (!this.property?.latitude || !this.property?.longitude) {
      console.warn('Property coordinates not available');
      return;
    }

    console.log('Initializing map with property location');

    const marker = {
      id: this.property._id || '',
      latitude: this.property.latitude,
      longitude: this.property.longitude,
      title: this.property.title,
      price: this.property.price,
      popup: `
        <div style="text-align: center;">
          <h3 style="margin: 0 0 8px 0;">${this.property.title}</h3>
          <p style="margin: 4px 0; color: #27ae60; font-weight: 600;">
            KES ${this.property.price.toLocaleString()}/month
          </p>
          <p style="margin: 4px 0;">${this.property.address}</p>
        </div>
      `
    };
    
    this.mapComponent.addMarkers([marker]);
    console.log('Map marker added');
  }

  /**
   * Get user's current location
   */
  getUserLocation(): void {
    console.log('Getting user location...');
    
    this.locationService.getCurrentLocation().subscribe({
      next: (location) => {
        console.log('✅ User location obtained:', location);
        this.userLocation = location;
        this.calculateDistance();
      },
      error: (error: HttpErrorResponse) => {
        console.log('Could not get user location:', error.message || error);
        // It's okay if we can't get location
      }
    });
  }

  /**
   * Calculate distance from user to property
   */
  calculateDistance(): void {
    if (this.userLocation && this.property?.latitude && this.property?.longitude) {
      this.distanceToProperty = this.locationService.calculateDistance(
        this.userLocation.latitude,
        this.userLocation.longitude,
        this.property.latitude,
        this.property.longitude
      );
      console.log('Distance to property:', this.distanceToProperty, 'km');
    }
  }

  /**
   * Open navigation to property
   */
  getDirections(): void {
    if (!this.property?.latitude || !this.property?.longitude) {
      alert('Property location not available');
      return;
    }

    console.log('Opening directions to property');
    this.locationService.openInMaps(
      this.property.latitude,
      this.property.longitude,
      this.property.title
    );
  }

  /**
   * Format distance for display
   */
  formatDistance(distanceKm: number): string {
    return this.locationService.formatDistance(distanceKm);
  }

  // ==========================================
  // IMAGE GALLERY METHODS
  // ==========================================

  getImageUrl(imagePath: string): string {
    if (!imagePath) {
      return 'https://placehold.co/800x600?text=No+Image';
    }
    return this.propertyService.getImageUrl(imagePath);
  }

  hasImages(): boolean {
    return !!(this.property?.images && this.property.images.length > 0);
  }

  nextImage(): void {
    if (this.property && this.property.images && this.property.images.length > 0) {
      this.currentImageIndex = (this.currentImageIndex + 1) % this.property.images.length;
      console.log('Next image:', this.currentImageIndex);
    }
  }

  previousImage(): void {
    if (this.property && this.property.images && this.property.images.length > 0) {
      this.currentImageIndex = this.currentImageIndex === 0 
        ? this.property.images.length - 1 
        : this.currentImageIndex - 1;
      console.log('Previous image:', this.currentImageIndex);
    }
  }

  selectImage(index: number): void {
    if (index >= 0 && this.property?.images && index < this.property.images.length) {
      this.currentImageIndex = index;
      console.log('Selected image:', this.currentImageIndex);
    }
  }
   
  /**
   * Open image in modal (new tab for now)
   */
  openImageModal(index: number): void {
    if (this.property?.images && this.property.images[index]) {
      window.open(this.getImageUrl(this.property.images[index]), '_blank');
    }
  }

  // ==========================================
  // VIDEO GALLERY METHODS
  // ==========================================
  hasVideos(): boolean {
    return !!(this.property?.videos && this.property.videos.length > 0);
  }

  /**
   * Get video URL (Cloudinary URLs are already complete)
   */
  getVideoUrl(videoPath: string): string {
    if (!videoPath) return '';
    // Cloudinary URLs are already complete, just return them
    return videoPath;
  }

  /**
   * Get poster image for video
   * Uses first property image as fallback
   */
  getVideoPoster(videoUrl: string): string {
    if (this.property?.images && this.property.images.length > 0) {
      return this.getImageUrl(this.property.images[0]);
    }
    return '';
  }

  nextVideo(): void {
    if (this.property && this.property.videos && this.property.videos.length > 0) {
      this.currentVideoIndex = (this.currentVideoIndex + 1) % this.property.videos.length;
      console.log('Next video:', this.currentVideoIndex);
    }
  }

  previousVideo(): void {
    if (this.property && this.property.videos && this.property.videos.length > 0) {
      this.currentVideoIndex = this.currentVideoIndex === 0 
        ? this.property.videos.length - 1 
        : this.currentVideoIndex - 1;
      console.log('Previous video:', this.currentVideoIndex);
    }
  }

  selectVideo(index: number): void {
    if (index >= 0 && this.property?.videos && index < this.property.videos.length) {
      this.currentVideoIndex = index;
      console.log('Selected video:', this.currentVideoIndex);
    }
  }

  // ==========================================
  // USER INTERACTION METHODS
  // ==========================================

  contactLandlord(): void {
    console.log('Contact landlord clicked');
    
    if (!this.isLoggedIn) {
      alert('Please login to contact the landlord');
      this.router.navigate(['/login'], { 
        queryParams: { returnUrl: `/properties/${this.propertyId}` }
      });
      return;
    }
    
    // TODO: Implement contact/messaging functionality
    alert('Contact functionality will be implemented in the messaging system.\n\nFor now, you can reach out to the property owner through the booking system.');
  }

  bookViewing(): void {
    console.log('Book viewing clicked');
    
    if (!this.isLoggedIn) {
      alert('Please login to book a viewing');
      this.router.navigate(['/login'], { 
        queryParams: { returnUrl: `/properties/${this.propertyId}` }
      });
      return;
    }
    
    if (this.userRole !== 'tenant') {
      alert('Only tenants can book property viewings');
      return;
    }
    
    // Navigate to booking page with property ID
    this.router.navigate(['/tenant/book-viewing', this.propertyId]);
  }

  /**
   * Navigate back - smart routing based on user role
   */
  goBack(): void {
    console.log('Going back - User role:', this.userRole);
    
    // Smart navigation based on user role
    if (this.userRole === 'landlord') {
      console.log('Navigating to landlord properties');
      this.router.navigate(['/landlord/properties']);
    } else if (this.userRole === 'tenant') {
      console.log('Navigating to tenant dashboard');
      this.router.navigate(['/tenant/dashboard']);
    } else if (this.isLoggedIn) {
      console.log('Navigating to general properties list');
      this.router.navigate(['/properties']);
    } else {
      // Fallback to browser history for non-authenticated users
      console.log('Using browser history back');
      window.history.back();
    }
  }

  editProperty(): void {
    if (!this.propertyId) {
      console.error('Invalid property ID');
      return;
    }
    
    console.log('Navigating to edit property:', this.propertyId);
    this.router.navigate(['/landlord/properties/edit', this.propertyId]);
  }

  isOwner(): boolean {
    // Check if current user is the landlord who owns this property
    if (!this.isLoggedIn || !this.property) {
      return false;
    }
    
    // Get current user ID
    const currentUserId = localStorage.getItem('userId');
    
    // Compare with property's landlord_id
    const isPropertyOwner = this.property.landlord_id === currentUserId;
    
    console.log('Ownership check:', {
      currentUserId,
      landlordId: this.property.landlord_id,
      isOwner: isPropertyOwner
    });
    
    return isPropertyOwner && this.userRole === 'landlord';
  }
  getModerationClass(status?: string): string {
  switch (status) {
    case 'approved':
      return 'moderation-approved';
    case 'pending_review':
      return 'moderation-pending';
    case 'rejected':
      return 'moderation-rejected';
    default:
      return 'moderation-unknown';
  }
}

/**
 * Get human-readable label for moderation status
 */
getModerationLabel(status?: string): string {
  switch (status) {
    case 'approved':
      return '✓ Approved';
    case 'pending_review':
      return '⏳ Under Review';
    case 'rejected':
      return '✗ Needs Improvement';
    default:
      return 'Unknown';
  }
}

/**
 * Get CSS class for quality score
 */
getScoreClass(score?: number): string {
  if (!score) return 'score-unknown';
  
  if (score >= 80) return 'score-high';
  if (score >= 50) return 'score-medium';
  return 'score-low';
}

/**
 * Request re-moderation after fixes
 */
requestRemoderation(): void {
  if (!this.propertyId) {
    console.error('No property ID available');
    return;
  }

  if (confirm('Request re-moderation? Make sure you\'ve fixed all issues first.')) {
    console.log('Requesting re-moderation for property:', this.propertyId);
    
    this.propertyService.remoderateProperty(this.propertyId).subscribe({
      next: (response) => {
        console.log('✅ Re-moderation complete:', response);
        alert(response.moderation.message);
        
        // Reload property to show updated status
        this.loadProperty();
      },
      error: (error) => {
        console.error('❌ Error re-moderating:', error);
        alert('Failed to remoderate property. Please try again.');
      }
    });
  }
}

  // ==========================================
  // HELPER METHODS
  // ==========================================

  /**
   * Get current image URL
   */
  getCurrentImage(): string {
    if (this.hasImages() && this.property?.images) {
      return this.getImageUrl(this.property.images[this.currentImageIndex]);
    }
    return 'https://placehold.co/800x600?text=No+Image';
  }

  /**
   * Check if property has specific amenity
   */
  hasAmenity(amenity: string): boolean {
    return !!(this.property?.amenities?.includes(amenity));
  } 
}
