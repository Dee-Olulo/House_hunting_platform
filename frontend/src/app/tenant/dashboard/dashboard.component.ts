// // src/app/tenant/dashboard/dashboard.component.ts (UPDATED WITH FAVOURITES)

// import { Component, OnInit } from '@angular/core';
// import { PropertySearchService } from '../services/property-search.service';
// import { FavouriteService } from '../../services/favourite.service';
// import {
//   Property,
//   PropertySearchParams,
//   FilterOptions
// } from '../models/property.interface';
// import { CommonModule } from '@angular/common';
// import { FormsModule } from '@angular/forms';
// import { RouterModule } from '@angular/router';

// @Component({
//   selector: 'app-dashboard',
//   standalone: true,
//   imports: [CommonModule, FormsModule, RouterModule],
//   templateUrl: './dashboard.component.html',
//   styleUrls: ['./dashboard.component.css']
// })
// export class DashboardComponent implements OnInit {
//   // Properties data
//   properties: Property[] = [];
//   totalProperties: number = 0;
//   currentPage: number = 1;
//   perPage: number = 12;
//   totalPages: number = 0;

//   // Loading states
//   isLoading: boolean = false;
//   isLoadingFilters: boolean = false;

//   // Filter options from backend
//   filterOptions: FilterOptions | null = null;

//   // Search filters
//   searchFilters: PropertySearchParams = {
//     status: 'active',
//     sort_by: 'newest',
//     page: 1,
//     per_page: 12
//   };

//   // UI state
//   showFilters: boolean = false;
//   viewMode: 'grid' | 'list' = 'grid';

//   // ✨ FAVOURITE STATES
//   favouritePropertyIds: Set<string> = new Set();
//   savingFavourite: Set<string> = new Set(); // Track which properties are being saved/unsaved

//   // Sort options
//   sortOptions = [
//     { value: 'newest', label: 'Newest First' },
//     { value: 'price_low', label: 'Price: Low to High' },
//     { value: 'price_high', label: 'Price: High to Low' },
//     { value: 'bedrooms', label: 'Most Bedrooms' }
//   ];

//   constructor(
//     private propertySearchService: PropertySearchService,
//     private favouriteService: FavouriteService // ✨ INJECT FAVOURITE SERVICE
//   ) {}

//   ngOnInit(): void {
//     this.loadFilterOptions();
//     this.searchProperties();
//     this.loadFavouriteIds(); // ✨ LOAD FAVOURITES
//   }

//   /**
//    * ✨ Load favourite property IDs
//    */
//   loadFavouriteIds(): void {
//     this.favouriteService.favouriteIds$.subscribe({
//       next: (ids) => {
//         this.favouritePropertyIds = ids;
//       }
//     });
//   }

//   /**
//    * ✨ Check if property is favourite
//    */
//   isFavourite(propertyId: string): boolean {
//     return this.favouritePropertyIds.has(propertyId);
//   }

//   /**
//    * ✨ Toggle favourite status
//    */
//   toggleFavourite(property: Property, event: Event): void {
//     event.stopPropagation(); // Prevent card click
//     event.preventDefault();
    
//     console.log('🔘 Save button clicked!');
//     console.log('📍 Property ID:', property._id);
//     console.log('📍 Property Title:', property.title);
    
//     if (!property._id) {
//       console.error('❌ No property ID found!');
//       alert('Error: Property ID is missing');
//       return;
//     }
    
//     const propertyId = property._id;
//     const isFav = this.isFavourite(propertyId);
    
//     console.log(`${isFav ? '➖' : '➕'} ${isFav ? 'Removing from' : 'Adding to'} favourites...`);
    
//     // Mark as saving
//     this.savingFavourite.add(propertyId);
    
//     this.favouriteService.toggleFavourite(propertyId).subscribe({
//       next: (response) => {
//         console.log('✅ Favourite toggled successfully:', response);
//         this.savingFavourite.delete(propertyId);
        
//         // Show success message
//         const message = isFav ? 'Removed from favourites' : 'Added to favourites';
//         this.showToast(message, 'success');
//       },
//       error: (error) => {
//         console.error('❌ Error toggling favourite:', error);
//         console.error('❌ Error details:', error.error);
//         console.error('❌ Error status:', error.status);
        
//         this.savingFavourite.delete(propertyId);
        
//         // Show error message
//         let errorMessage = 'Failed to update favourites';
//         if (error.status === 401) {
//           errorMessage = 'Please login to save properties';
//         } else if (error.status === 403) {
//           errorMessage = 'Only tenants can save properties';
//         } else if (error.error?.error) {
//           errorMessage = error.error.error;
//         }
        
//         this.showToast(errorMessage, 'error');
//       }
//     });
//   }

//   /**
//    * ✨ Show toast notification
//    */
//   showToast(message: string, type: 'success' | 'error'): void {
//     // Simple alert for now, can be replaced with a toast library
//     alert(message);
//   }

//   /**
//    * ✨ Check if property is being saved/unsaved
//    */
//   isSavingFavourite(propertyId: string): boolean {
//     return this.savingFavourite.has(propertyId);
//   }

//   /**
//    * Load available filter options
//    */
//   loadFilterOptions(): void {
//     this.isLoadingFilters = true;
//     this.propertySearchService.getFilterOptions().subscribe({
//       next: (options) => {
//         this.filterOptions = options;
//         this.isLoadingFilters = false;
//       },
//       error: (error) => {
//         console.error('Error loading filter options:', error);
//         this.isLoadingFilters = false;
//       }
//     });
//   }

//   /**
//    * Search properties with current filters
//    */
//   searchProperties(): void {
//     this.isLoading = true;
//     this.searchFilters.page = this.currentPage;
//     this.searchFilters.per_page = this.perPage;

//     this.propertySearchService.searchProperties(this.searchFilters).subscribe({
//       next: (response) => {
//         this.properties = response.properties;
//         this.totalProperties = response.total;
//         this.totalPages = response.total_pages;
//         this.isLoading = false;
//       },
//       error: (error) => {
//         console.error('Error searching properties:', error);
//         this.isLoading = false;
//       }
//     });
//   }

//   /**
//    * Apply filters and search
//    */
//   applyFilters(): void {
//     this.currentPage = 1;
//     this.searchProperties();
//   }

//   /**
//    * Reset all filters
//    */
//   resetFilters(): void {
//     this.searchFilters = {
//       status: 'active',
//       sort_by: 'newest',
//       page: 1,
//       per_page: 12
//     };
//     this.currentPage = 1;
//     this.searchProperties();
//   }

//   /**
//    * Pagination
//    */
//   goToPage(page: number): void {
//     if (page >= 1 && page <= this.totalPages) {
//       this.currentPage = page;
//       this.searchProperties();
//       window.scrollTo({ top: 0, behavior: 'smooth' });
//     }
//   }

//   previousPage(): void {
//     this.goToPage(this.currentPage - 1);
//   }

//   nextPage(): void {
//     this.goToPage(this.currentPage + 1);
//   }

//   /**
//    * Toggle filter panel
//    */
//   toggleFilters(): void {
//     this.showFilters = !this.showFilters;
//   }

//   /**
//    * Get page numbers for pagination
//    */
//   getPageNumbers(): number[] {
//     const pages: number[] = [];
//     const maxVisible = 5;
//     let start = Math.max(1, this.currentPage - Math.floor(maxVisible / 2));
//     let end = Math.min(this.totalPages, start + maxVisible - 1);

//     if (end - start < maxVisible - 1) {
//       start = Math.max(1, end - maxVisible + 1);
//     }

//     for (let i = start; i <= end; i++) {
//       pages.push(i);
//     }

//     return pages;
//   }

//   /**
//    * Format price with currency
//    */
//   formatPrice(price: number): string {
//     return new Intl.NumberFormat('en-KE', {
//       style: 'currency',
//       currency: 'KES',
//       minimumFractionDigits: 0
//     }).format(price);
//   }
// }

// src/app/tenant/dashboard/dashboard.component.ts (FIXED WITH OnPush)

import { Component, OnInit, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { PropertySearchService } from '../services/property-search.service';
import { FavouriteService } from '../../services/favourite.service';
import {
  Property,
  PropertySearchParams,
  FilterOptions
} from '../models/property.interface';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Router } from '@angular/router';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush // Added OnPush strategy
})
export class DashboardComponent implements OnInit {
  // Properties data
  properties: Property[] = [];
  totalProperties: number = 0;
  currentPage: number = 1;
  perPage: number = 12;
  totalPages: number = 0;

  // Loading states
  isLoading: boolean = false;
  isLoadingFilters: boolean = false;

  // Filter options from backend
  filterOptions: FilterOptions | null = null;

  // Search filters
  searchFilters: PropertySearchParams = {
    status: 'active',
    sort_by: 'newest',
    page: 1,
    per_page: 12
  };

  // UI state
  showFilters: boolean = false;
  viewMode: 'grid' | 'list' = 'grid';

  // Favourite states
  favouritePropertyIds: Set<string> = new Set();
  savingFavourite: Set<string> = new Set();

  // Prevent double navigation
  private isNavigating = false;

  // Sort options
  sortOptions = [
    { value: 'newest', label: 'Newest First' },
    { value: 'price_low', label: 'Price: Low to High' },
    { value: 'price_high', label: 'Price: High to Low' },
    { value: 'bedrooms', label: 'Most Bedrooms' }
  ];

  constructor(
    private propertySearchService: PropertySearchService,
    private favouriteService: FavouriteService,
    private router: Router,
    private cdr: ChangeDetectorRef // Added ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.loadFilterOptions();
    this.searchProperties();
    this.loadFavouriteIds();
  }

  /**
   * Load favourite property IDs
   */
  loadFavouriteIds(): void {
    this.favouriteService.favouriteIds$.subscribe({
      next: (ids) => {
        this.favouritePropertyIds = ids;
        this.cdr.markForCheck(); // Trigger change detection
      }
    });
  }

  /**
   * Check if property is favourite
   */
  isFavourite(propertyId: string): boolean {
    return this.favouritePropertyIds.has(propertyId);
  }

  /**
   * Toggle favourite status
   */
  toggleFavourite(property: Property, event: Event): void {
    event.stopPropagation();
    event.preventDefault();
    
    console.log('🔘 Save button clicked!');
    console.log('📍 Property ID:', property._id);
    
    if (!property._id) {
      console.error('❌ No property ID found!');
      this.showToast('Error: Property ID is missing', 'error');
      return;
    }
    
    const propertyId = property._id;
    const isFav = this.isFavourite(propertyId);
    
    console.log(`${isFav ? '➖' : '➕'} ${isFav ? 'Removing from' : 'Adding to'} favourites...`);
    
    // Mark as saving
    this.savingFavourite.add(propertyId);
    this.cdr.markForCheck();
    
    this.favouriteService.toggleFavourite(propertyId).subscribe({
      next: (response) => {
        console.log('✅ Favourite toggled successfully:', response);
        this.savingFavourite.delete(propertyId);
        this.cdr.markForCheck();
        
        const message = isFav ? 'Removed from favourites' : 'Added to favourites';
        this.showToast(message, 'success');
      },
      error: (error) => {
        console.error('❌ Error toggling favourite:', error);
        this.savingFavourite.delete(propertyId);
        this.cdr.markForCheck();
        
        let errorMessage = 'Failed to update favourites';
        if (error.status === 401) {
          errorMessage = 'Please login to save properties';
        } else if (error.status === 403) {
          errorMessage = 'Only tenants can save properties';
        } else if (error.error?.error) {
          errorMessage = error.error.error;
        }
        
        this.showToast(errorMessage, 'error');
      }
    });
  }

  /**
   * Show toast notification
   */
  showToast(message: string, type: 'success' | 'error'): void {
    // Simple alert for now, can be replaced with a toast library
    alert(message);
  }

  /**
   * Check if property is being saved/unsaved
   */
  isSavingFavourite(propertyId: string): boolean {
    return this.savingFavourite.has(propertyId);
  }

  /**
   * Navigate to property details (with double-click prevention)
   */
  viewPropertyDetails(propertyId: string, event?: MouseEvent): void {
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }

    if (this.isNavigating) {
      console.log('⚠️ Navigation already in progress');
      return;
    }

    console.log('🔵 Viewing property:', propertyId);
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
   * Load available filter options
   */
  loadFilterOptions(): void {
    this.isLoadingFilters = true;
    this.cdr.markForCheck();

    this.propertySearchService.getFilterOptions().subscribe({
      next: (options) => {
        this.filterOptions = options;
        this.isLoadingFilters = false;
        this.cdr.markForCheck();
      },
      error: (error) => {
        console.error('Error loading filter options:', error);
        this.isLoadingFilters = false;
        this.cdr.markForCheck();
      }
    });
  }

  /**
   * Search properties with current filters
   */
  searchProperties(): void {
    this.isLoading = true;
    this.searchFilters.page = this.currentPage;
    this.searchFilters.per_page = this.perPage;
    this.cdr.markForCheck();

    this.propertySearchService.searchProperties(this.searchFilters).subscribe({
      next: (response) => {
        this.properties = response.properties;
        this.totalProperties = response.total;
        this.totalPages = response.total_pages;
        this.isLoading = false;
        this.cdr.markForCheck();
      },
      error: (error) => {
        console.error('Error searching properties:', error);
        this.isLoading = false;
        this.cdr.markForCheck();
      }
    });
  }

  /**
   * Apply filters and search
   */
  applyFilters(): void {
    this.currentPage = 1;
    this.searchProperties();
  }

  /**
   * Reset all filters
   */
  resetFilters(): void {
    this.searchFilters = {
      status: 'active',
      sort_by: 'newest',
      page: 1,
      per_page: 12
    };
    this.currentPage = 1;
    this.searchProperties();
  }

  /**
   * Pagination
   */
  goToPage(page: number): void {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.searchProperties();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }

  previousPage(): void {
    this.goToPage(this.currentPage - 1);
  }

  nextPage(): void {
    this.goToPage(this.currentPage + 1);
  }

  /**
   * Toggle filter panel
   */
  toggleFilters(): void {
    this.showFilters = !this.showFilters;
    this.cdr.markForCheck();
  }

  /**
   * Get page numbers for pagination
   */
  getPageNumbers(): number[] {
    const pages: number[] = [];
    const maxVisible = 5;
    let start = Math.max(1, this.currentPage - Math.floor(maxVisible / 2));
    let end = Math.min(this.totalPages, start + maxVisible - 1);

    if (end - start < maxVisible - 1) {
      start = Math.max(1, end - maxVisible + 1);
    }

    for (let i = start; i <= end; i++) {
      pages.push(i);
    }

    return pages;
  }

  /**
   * Format price with currency
   */
  formatPrice(price: number): string {
    return new Intl.NumberFormat('en-KE', {
      style: 'currency',
      currency: 'KES',
      minimumFractionDigits: 0
    }).format(price);
  }
}