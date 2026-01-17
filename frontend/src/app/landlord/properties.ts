// // import { Component, OnInit } from '@angular/core';
// // import { CommonModule } from '@angular/common';
// // import { Router, RouterLink } from '@angular/router';
// // import { PropertyService, Property } from '../services/property.service';

// // @Component({
// //   selector: 'app-properties',
// //   standalone: true,
// //   imports: [CommonModule, RouterLink],
// //   templateUrl: './properties.html',
// //   styleUrls: ['./properties.css']
// // })
// // export class PropertiesComponent implements OnInit {
// //   properties: Property[] = [];
// //   isLoading = false;
// //   errorMessage = '';
// //   successMessage = '';

// //   constructor(
// //     private propertyService: PropertyService,
// //     private router: Router
// //   ) {}

// //   ngOnInit(): void {
// //     this.loadProperties();
// //   }

// //   loadProperties(): void {
// //     this.isLoading = true;
// //     this.errorMessage = '';

// //     this.propertyService.getMyProperties().subscribe({
// //       next: (response) => {
// //         this.properties = response.properties;
// //         this.isLoading = false;
// //       },
// //       error: (error) => {
// //         console.error('Error loading properties:', error);
// //         this.errorMessage = error.error?.error || 'Failed to load properties';
// //         this.isLoading = false;
// //       }
// //     });
// //   }

// //   getImageUrl(imagePath: string): string {
// //     return this.propertyService.getImageUrl(imagePath);
// //   }

// //   editProperty(propertyId: string): void {
// //     this.router.navigate(['/landlord/properties/edit', propertyId]);
    
// //   }

// //   deleteProperty(propertyId: string, title: string): void {
// //     if (confirm(`Are you sure you want to delete "${title}"?`)) {
// //       this.propertyService.deleteProperty(propertyId).subscribe({
// //         next: (response) => {
// //           this.successMessage = response.message;
// //           this.loadProperties(); // Reload list
// //           setTimeout(() => this.successMessage = '', 3000);
// //         },
// //         error: (error) => {
// //           console.error('Error deleting property:', error);
// //           this.errorMessage = error.error?.error || 'Failed to delete property';
// //           setTimeout(() => this.errorMessage = '', 3000);
// //         }
// //       });
// //     }
// //   }

// //   confirmProperty(propertyId: string): void {
// //     this.propertyService.confirmProperty(propertyId).subscribe({
// //       next: (response) => {
// //         this.successMessage = response.message;
// //         this.loadProperties(); // Reload list
// //         setTimeout(() => this.successMessage = '', 3000);
// //       },
// //       error: (error) => {
// //         console.error('Error confirming property:', error);
// //         this.errorMessage = error.error?.error || 'Failed to confirm property';
// //         setTimeout(() => this.errorMessage = '', 3000);
// //       }
// //     });
// //   }

// //   viewProperty(propertyId: string): void {
// //     this.router.navigate(['/properties', propertyId]);
// //   }

// //   getStatusClass(status: string): string {
// //     const statusClasses: { [key: string]: string } = {
// //       'active': 'status-active',
// //       'inactive': 'status-inactive',
// //       'pending': 'status-pending',
// //       'expired': 'status-expired'
// //     };
// //     return statusClasses[status] || 'status-default';
// //   }
// // }

// import { Component, OnInit } from '@angular/core';
// import { CommonModule } from '@angular/common';
// import { Router, RouterLink } from '@angular/router';
// import { PropertyService, Property } from '../services/property.service';

// @Component({
//   selector: 'app-properties',
//   standalone: true,
//   imports: [CommonModule, RouterLink],
//   templateUrl: './properties.html',
//   styleUrls: ['./properties.css']
// })
// export class PropertiesComponent implements OnInit {
//   properties: Property[] = [];
//   isLoading = false;
//   errorMessage = '';
//   successMessage = '';

//   constructor(
//     private propertyService: PropertyService,
//     private router: Router
//   ) {}

//   ngOnInit(): void {
//     this.loadProperties();
//   }

//   loadProperties(): void {
//     this.isLoading = true;
//     this.errorMessage = '';

//     this.propertyService.getMyProperties().subscribe({
//       next: (response) => {
//         this.properties = response.properties;
//         this.isLoading = false;
//       },
//       error: (error) => {
//         console.error('Error loading properties:', error);
//         this.errorMessage = error.error?.error || 'Failed to load properties';
//         this.isLoading = false;
//       }
//     });
//   }

//   getImageUrl(imagePath: string): string {
//     return this.propertyService.getImageUrl(imagePath);
//   }

//   /**
//    * FIXED: Edit property with proper event handling
//    */
//   editProperty(propertyId: string, event?: MouseEvent): void {
//     // Prevent event propagation and default behavior
//     if (event) {
//       event.preventDefault();
//       event.stopPropagation();
//       event.stopImmediatePropagation();
//     }

//     console.log('🔵 Edit button clicked for property:', propertyId);

//     // Navigate immediately
//     this.router.navigate(['/landlord/properties/edit', propertyId]).then(success => {
//       if (success) {
//         console.log('✅ Navigation successful');
//       } else {
//         console.log('❌ Navigation failed');
//       }
//     });
//   }

//   /**
//    * FIXED: View property with proper event handling
//    */
//   viewProperty(propertyId: string, event?: MouseEvent): void {
//     if (event) {
//       event.preventDefault();
//       event.stopPropagation();
//       event.stopImmediatePropagation();
//     }

//     console.log('🔵 View button clicked for property:', propertyId);
    
//     this.router.navigate(['/properties', propertyId]).then(success => {
//       if (success) {
//         console.log('✅ Navigation successful');
//       } else {
//         console.log('❌ Navigation failed');
//       }
//     });
//   }

//   /**
//    * FIXED: Delete property with proper event handling
//    */
//   deleteProperty(propertyId: string, title: string, event?: MouseEvent): void {
//     if (event) {
//       event.preventDefault();
//       event.stopPropagation();
//       event.stopImmediatePropagation();
//     }

//     if (confirm(`Are you sure you want to delete "${title}"?`)) {
//       this.propertyService.deleteProperty(propertyId).subscribe({
//         next: (response) => {
//           this.successMessage = response.message;
//           this.loadProperties();
//           setTimeout(() => this.successMessage = '', 3000);
//         },
//         error: (error) => {
//           console.error('Error deleting property:', error);
//           this.errorMessage = error.error?.error || 'Failed to delete property';
//           setTimeout(() => this.errorMessage = '', 3000);
//         }
//       });
//     }
//   }

//   /**
//    * FIXED: Confirm property with proper event handling
//    */
//   confirmProperty(propertyId: string, event?: MouseEvent): void {
//     if (event) {
//       event.preventDefault();
//       event.stopPropagation();
//       event.stopImmediatePropagation();
//     }

//     this.propertyService.confirmProperty(propertyId).subscribe({
//       next: (response) => {
//         this.successMessage = response.message;
//         this.loadProperties();
//         setTimeout(() => this.successMessage = '', 3000);
//       },
//       error: (error) => {
//         console.error('Error confirming property:', error);
//         this.errorMessage = error.error?.error || 'Failed to confirm property';
//         setTimeout(() => this.errorMessage = '', 3000);
//       }
//     });
//   }

//   getStatusClass(status: string): string {
//     const statusClasses: { [key: string]: string } = {
//       'active': 'status-active',
//       'inactive': 'status-inactive',
//       'pending': 'status-pending',
//       'expired': 'status-expired'
//     };
//     return statusClasses[status] || 'status-default';
//   }
// }

import { Component, OnInit, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { PropertyService, Property } from '../services/property.service';

@Component({
  selector: 'app-properties',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './properties.html',
  styleUrls: ['./properties.css'],
  changeDetection: ChangeDetectionStrategy.OnPush // Added OnPush strategy
})
export class PropertiesComponent implements OnInit {
  properties: Property[] = [];
  isLoading = false;
  errorMessage = '';
  successMessage = '';

  // Prevent double navigation
  private isNavigating = false;

  constructor(
    private propertyService: PropertyService,
    private router: Router,
    private cdr: ChangeDetectorRef // Added ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.loadProperties();
  }

  loadProperties(): void {
    this.isLoading = true;
    this.errorMessage = '';
    this.cdr.markForCheck(); // Trigger change detection

    this.propertyService.getMyProperties().subscribe({
      next: (response) => {
        this.properties = response.properties;
        this.isLoading = false;
        this.cdr.markForCheck(); // Trigger change detection after data load
      },
      error: (error) => {
        console.error('Error loading properties:', error);
        this.errorMessage = error.error?.error || 'Failed to load properties';
        this.isLoading = false;
        this.cdr.markForCheck();
      }
    });
  }

  getImageUrl(imagePath: string): string {
    return this.propertyService.getImageUrl(imagePath);
  }

  /**
   * Edit property with proper event handling and navigation guard
   */
  editProperty(propertyId: string, event?: MouseEvent): void {
    // Prevent event propagation and default behavior
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }

    // Prevent double navigation
    if (this.isNavigating) {
      console.log('⚠️ Navigation already in progress, ignoring click');
      return;
    }

    console.log('🔵 Edit button clicked for property:', propertyId);
    this.isNavigating = true;

    // Navigate immediately
    this.router.navigate(['/landlord/properties/edit', propertyId]).then(success => {
      if (success) {
        console.log('✅ Navigation successful');
      } else {
        console.log('❌ Navigation failed');
      }
    }).finally(() => {
      // Reset navigation flag after a delay
      setTimeout(() => {
        this.isNavigating = false;
      }, 500);
    });
  }

  /**
   * View property with proper event handling and navigation guard
   */
  viewProperty(propertyId: string, event?: MouseEvent): void {
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }

    // Prevent double navigation
    if (this.isNavigating) {
      console.log('⚠️ Navigation already in progress, ignoring click');
      return;
    }

    console.log('🔵 View button clicked for property:', propertyId);
    this.isNavigating = true;
    
    this.router.navigate(['/properties', propertyId]).then(success => {
      if (success) {
        console.log('✅ Navigation successful');
      } else {
        console.log('❌ Navigation failed');
      }
    }).finally(() => {
      setTimeout(() => {
        this.isNavigating = false;
      }, 500);
    });
  }

  /**
   * Delete property with proper event handling
   */
  deleteProperty(propertyId: string, title: string, event?: MouseEvent): void {
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }

    if (confirm(`Are you sure you want to delete "${title}"?`)) {
      this.propertyService.deleteProperty(propertyId).subscribe({
        next: (response) => {
          this.successMessage = response.message;
          this.loadProperties();
          this.cdr.markForCheck();
          setTimeout(() => {
            this.successMessage = '';
            this.cdr.markForCheck();
          }, 3000);
        },
        error: (error) => {
          console.error('Error deleting property:', error);
          this.errorMessage = error.error?.error || 'Failed to delete property';
          this.cdr.markForCheck();
          setTimeout(() => {
            this.errorMessage = '';
            this.cdr.markForCheck();
          }, 3000);
        }
      });
    }
  }

  /**
   * Confirm property with proper event handling
   */
  confirmProperty(propertyId: string, event?: MouseEvent): void {
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }

    this.propertyService.confirmProperty(propertyId).subscribe({
      next: (response) => {
        this.successMessage = response.message;
        this.loadProperties();
        this.cdr.markForCheck();
        setTimeout(() => {
          this.successMessage = '';
          this.cdr.markForCheck();
        }, 3000);
      },
      error: (error) => {
        console.error('Error confirming property:', error);
        this.errorMessage = error.error?.error || 'Failed to confirm property';
        this.cdr.markForCheck();
        setTimeout(() => {
          this.errorMessage = '';
          this.cdr.markForCheck();
        }, 3000);
      }
    });
  }

  getStatusClass(status: string): string {
    const statusClasses: { [key: string]: string } = {
      'active': 'status-active',
      'inactive': 'status-inactive',
      'pending': 'status-pending',
      'expired': 'status-expired'
    };
    return statusClasses[status] || 'status-default';
  }
}