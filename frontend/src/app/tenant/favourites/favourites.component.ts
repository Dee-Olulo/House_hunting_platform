// src/app/tenant/favourites/favourites.component.ts (FIXED)

import { Component, OnInit, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { FavouriteService, Favourite } from '../../services/favourite.service';

@Component({
  selector: 'app-favourites',
  standalone: true,
  imports: [CommonModule, RouterModule],
  changeDetection: ChangeDetectionStrategy.OnPush, // Added OnPush strategy
  template: `
    <div class="favourites-container">
      <div class="favourites-header">
        <div>
          <h1>My Saved Properties</h1>
          <p class="subtitle">{{ totalFavourites }} properties saved</p>
        </div>
        <button 
          *ngIf="favourites.length > 0"
          (click)="clearAll()" 
          class="clear-all-btn"
          type="button">
          <i class="fas fa-trash"></i> Clear All
        </button>
      </div>

      <!-- Loading State -->
      <div *ngIf="isLoading" class="loading-container">
        <div class="spinner"></div>
        <p>Loading favourites...</p>
      </div>

      <!-- Empty State -->
      <div *ngIf="!isLoading && favourites.length === 0" class="empty-state">
        <i class="far fa-heart"></i>
        <h3>No Saved Properties</h3>
        <p>Properties you save will appear here</p>
        <button 
          (click)="navigateToDashboard($event)" 
          class="browse-btn"
          type="button">
          <i class="fas fa-search"></i> Browse Properties
        </button>
      </div>

      <!-- Favourites Grid -->
      <div *ngIf="!isLoading && favourites.length > 0" class="favourites-grid">
        <div *ngFor="let favourite of favourites" class="favourite-card">
          <div class="property-image">
            <img
              [src]="favourite.property.images?.[0] || 'assets/images/placeholder.jpg'"
              [alt]="favourite.property.title"
            />
            <button 
              class="remove-btn" 
              (click)="removeFavourite(favourite.property._id || '', $event)"
              [disabled]="removing.has(favourite.property._id || '')"
              type="button">
              <i *ngIf="!removing.has(favourite.property._id || '')" class="fas fa-times"></i>
              <i *ngIf="removing.has(favourite.property._id || '')" class="fas fa-spinner fa-spin"></i>
            </button>
          </div>

          <div class="property-info">
            <div class="property-type">{{ favourite.property.property_type }}</div>
            <h3>{{ favourite.property.title }}</h3>
            <p class="location">
              <i class="fas fa-map-marker-alt"></i>
              {{ favourite.property.city }}, {{ favourite.property.state }}
            </p>

            <div class="property-features">
              <span><i class="fas fa-bed"></i> {{ favourite.property.bedrooms }} Beds</span>
              <span><i class="fas fa-bath"></i> {{ favourite.property.bathrooms }} Baths</span>
              <span><i class="fas fa-ruler-combined"></i> {{ favourite.property.area_sqft }} sqft</span>
            </div>

            <div class="added-date">
              <i class="far fa-clock"></i> Saved {{ getRelativeTime(favourite.added_at) }}
            </div>

            <div class="card-footer">
              <div class="price">{{ formatPrice(favourite.property.price) }}<span>/month</span></div>
              <button 
                class="view-btn" 
                (click)="viewPropertyDetails(favourite.property._id, $event)"
                type="button">
                View Details
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div *ngIf="!isLoading && favourites.length > 0 && totalPages > 1" class="pagination">
        <button
          [disabled]="currentPage === 1"
          (click)="previousPage()"
          type="button">
          <i class="fas fa-chevron-left"></i> Previous
        </button>

        <div class="page-numbers">
          <button
            *ngFor="let page of getPageNumbers()"
            [class.active]="page === currentPage"
            (click)="goToPage(page)"
            type="button">
            {{ page }}
          </button>
        </div>

        <button
          [disabled]="currentPage === totalPages"
          (click)="nextPage()"
          type="button">
          Next <i class="fas fa-chevron-right"></i>
        </button>
      </div>
    </div>
  `,
  styles: [`
    .favourites-container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 20px;
    }

    .favourites-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 30px;
    }

    .favourites-header h1 {
      margin: 0;
      color: #2c3e50;
    }

    .subtitle {
      color: #7f8c8d;
      margin: 5px 0 0;
    }

    .clear-all-btn {
      padding: 10px 20px;
      background: #e74c3c;
      color: white;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: all 0.3s ease;
    }

    .clear-all-btn:hover:not(:disabled) {
      background: #c0392b;
    }

    .clear-all-btn:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    .loading-container, .empty-state {
      text-align: center;
      padding: 60px 20px;
    }

    .spinner {
      border: 4px solid #f3f3f3;
      border-top: 4px solid #6c5ce7;
      border-radius: 50%;
      width: 40px;
      height: 40px;
      animation: spin 1s linear infinite;
      margin: 0 auto 20px;
    }

    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }

    .empty-state i {
      font-size: 80px;
      color: #ddd;
      margin-bottom: 20px;
    }

    .empty-state h3 {
      color: #2c3e50;
      margin-bottom: 10px;
    }

    .empty-state p {
      color: #7f8c8d;
      margin-bottom: 20px;
    }

    .browse-btn {
      padding: 12px 24px;
      background: #6c5ce7;
      color: white;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      transition: all 0.3s ease;
    }

    .browse-btn:hover {
      background: #5f4fd1;
    }

    .favourites-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 24px;
    }

    .favourite-card {
      background: white;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    .favourite-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
    }

    .property-image {
      position: relative;
      height: 200px;
      overflow: hidden;
    }

    .property-image img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .remove-btn {
      position: absolute;
      top: 10px;
      right: 10px;
      background: rgba(231, 76, 60, 0.9);
      color: white;
      border: none;
      border-radius: 50%;
      width: 36px;
      height: 36px;
      cursor: pointer;
      transition: all 0.3s ease;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .remove-btn:hover:not(:disabled) {
      background: #c0392b;
      transform: scale(1.1);
    }

    .remove-btn:disabled {
      opacity: 0.7;
      cursor: not-allowed;
    }

    .property-info {
      padding: 16px;
    }

    .property-type {
      display: inline-block;
      padding: 4px 12px;
      background: #ecf0f1;
      border-radius: 4px;
      font-size: 12px;
      text-transform: uppercase;
      margin-bottom: 8px;
    }

    .property-info h3 {
      margin: 8px 0;
      font-size: 18px;
      color: #2c3e50;
    }

    .location {
      color: #7f8c8d;
      font-size: 14px;
      margin-bottom: 12px;
    }

    .property-features {
      display: flex;
      gap: 16px;
      margin-bottom: 12px;
      font-size: 14px;
      color: #7f8c8d;
    }

    .added-date {
      font-size: 12px;
      color: #95a5a6;
      margin-bottom: 12px;
    }

    .card-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-top: 12px;
      border-top: 1px solid #ecf0f1;
    }

    .price {
      font-size: 24px;
      font-weight: 600;
      color: #27ae60;
    }

    .price span {
      font-size: 14px;
      color: #7f8c8d;
    }

    .view-btn {
      padding: 8px 16px;
      background: #6c5ce7;
      color: white;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.3s ease;
    }

    .view-btn:hover {
      background: #5f4fd1;
    }

    .pagination {
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 12px;
      margin-top: 40px;
    }

    .pagination button {
      padding: 8px 16px;
      border: 1px solid #ddd;
      background: white;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.3s ease;
    }

    .pagination button:hover:not(:disabled) {
      background: #f8f9fa;
      border-color: #bbb;
    }

    .pagination button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .page-numbers button.active {
      background: #6c5ce7;
      color: white;
      border-color: #6c5ce7;
    }
  `]
})
export class FavouritesComponent implements OnInit {
  favourites: Favourite[] = [];
  totalFavourites: number = 0;
  currentPage: number = 1;
  perPage: number = 12;
  totalPages: number = 0;
  isLoading: boolean = false;
  removing: Set<string> = new Set();
  
  // Prevent double navigation
  private isNavigating = false;

  constructor(
    private favouriteService: FavouriteService,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.loadFavourites();
  }

  loadFavourites(): void {
    this.isLoading = true;
    this.cdr.markForCheck();

    this.favouriteService.getFavourites(this.currentPage, this.perPage).subscribe({
      next: (response) => {
        this.favourites = response.favourites;
        this.totalFavourites = response.total;
        this.totalPages = response.total_pages;
        this.isLoading = false;
        this.cdr.markForCheck();
      },
      error: (error) => {
        console.error('Error loading favourites:', error);
        this.isLoading = false;
        this.cdr.markForCheck();
      }
    });
  }

  removeFavourite(propertyId: string, event: Event): void {
    event.stopPropagation();
    event.preventDefault();
    
    if (confirm('Remove this property from your favourites?')) {
      this.removing.add(propertyId);
      this.cdr.markForCheck();
      
      this.favouriteService.removeFromFavourites(propertyId).subscribe({
        next: () => {
          this.removing.delete(propertyId);
          this.loadFavourites(); // Reload list
          this.cdr.markForCheck();
        },
        error: (error) => {
          console.error('Error removing favourite:', error);
          this.removing.delete(propertyId);
          this.cdr.markForCheck();
          alert('Failed to remove favourite');
        }
      });
    }
  }

  clearAll(): void {
    if (confirm('Are you sure you want to clear all saved properties?')) {
      this.isLoading = true;
      this.cdr.markForCheck();
      
      this.favouriteService.clearAllFavourites().subscribe({
        next: () => {
          this.loadFavourites();
        },
        error: (error) => {
          console.error('Error clearing favourites:', error);
          this.isLoading = false;
          this.cdr.markForCheck();
          alert('Failed to clear favourites');
        }
      });
    }
  }

  /**
   * Navigate to property details with double-click prevention
   */
  viewPropertyDetails(propertyId: string | undefined, event?: MouseEvent): void {
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }

    if (!propertyId) {
      console.error('No property ID provided');
      return;
    }

    if (this.isNavigating) {
      console.log('⚠️ Navigation already in progress');
      return;
    }

    console.log('🔵 Viewing property:', propertyId);
    this.isNavigating = true;

    this.router.navigate(['/tenant/property', propertyId]).then(success => {
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
   * Navigate to dashboard with double-click prevention
   */
  navigateToDashboard(event?: MouseEvent): void {
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }

    if (this.isNavigating) return;

    this.isNavigating = true;
    this.router.navigate(['/tenant/dashboard']).finally(() => {
      setTimeout(() => {
        this.isNavigating = false;
      }, 500);
    });
  }

  goToPage(page: number): void {
    this.currentPage = page;
    this.loadFavourites();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  previousPage(): void {
    if (this.currentPage > 1) {
      this.goToPage(this.currentPage - 1);
    }
  }

  nextPage(): void {
    if (this.currentPage < this.totalPages) {
      this.goToPage(this.currentPage + 1);
    }
  }

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

  formatPrice(price: number): string {
    return new Intl.NumberFormat('en-KE', {
      style: 'currency',
      currency: 'KES',
      minimumFractionDigits: 0
    }).format(price);
  }

  getRelativeTime(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'today';
    if (diffDays === 1) return 'yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    return `${Math.floor(diffDays / 30)} months ago`;
  }
}