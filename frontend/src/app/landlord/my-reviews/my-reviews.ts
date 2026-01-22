// src/app/landlord/my-reviews/my-reviews.component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ReviewService, Review, ReviewStats } from '../../services/review.service';

@Component({
  selector: 'app-my-reviews',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './my-reviews.html',
  styleUrls: ['./my-reviews.css']
})
export class MyReviewsComponent implements OnInit {
  reviews: Review[] = [];
  stats: ReviewStats | null = null;
  isLoading = true;
  errorMessage = '';
  successMessage = '';

  // Filters
  selectedRating: string = '';
  selectedProperty: string = '';
  sortBy: 'newest' | 'oldest' | 'highest' | 'lowest' = 'newest';

  // Pagination
  currentPage = 1;
  totalPages = 1;
  perPage = 10;

  // Response modal
  showResponseModal = false;
  selectedReview: Review | null = null;
  responseText = '';
  isSubmittingResponse = false;

  // Properties list for filter dropdown
  properties: Array<{ id: string; title: string }> = [];

  constructor(public reviewService: ReviewService) {}

  ngOnInit(): void {
    this.loadReviews();
    
  }

  /**
   * Load landlord's reviews
   */
  loadReviews(): void {
    this.isLoading = true;
    this.errorMessage = '';

    const params: any = {
      page: this.currentPage,
      per_page: this.perPage,
      sort_by: this.sortBy
    };

    if (this.selectedRating) {
      params.rating = parseInt(this.selectedRating);
    }

    if (this.selectedProperty) {
      params.property_id = this.selectedProperty;
    }

    this.reviewService.getMyReviews().subscribe({
      next: (response) => {
        this.reviews = response.reviews;
        this.isLoading = false;

        // Extract unique properties for filter
        this.extractProperties();
      },
      error: (error) => {
        console.error('Error loading reviews:', error);
        this.errorMessage = error.error?.error || 'Failed to load reviews';
        this.isLoading = false;
      }
    });
  }



  /**
   * Extract unique properties from reviews for filter dropdown
   */
  extractProperties(): void {
    const propertyMap = new Map<string, string>();
    
    this.reviews.forEach(review => {
      if (review.property_id && review.property_title) {
        propertyMap.set(review.property_id, review.property_title);
      }
    });

    this.properties = Array.from(propertyMap.entries()).map(([id, title]) => ({
      id,
      title
    }));
  }

  /**
   * Apply filters and reload reviews
   */
  applyFilters(): void {
    this.currentPage = 1;
    this.loadReviews();
  }

  /**
   * Clear all filters
   */
  clearFilters(): void {
    this.selectedRating = '';
    this.selectedProperty = '';
    this.sortBy = 'newest';
    this.currentPage = 1;
    this.loadReviews();
  }

  /**
   * Open response modal
   */
  openResponseModal(review: Review): void {
    this.selectedReview = review;
    this.showResponseModal = true;
  }

  /**
   * Close response modal
   */
  closeResponseModal(): void {
    this.showResponseModal = false;
    this.selectedReview = null;
    this.responseText = '';
    this.isSubmittingResponse = false;
  }

 
  /**
   * Pagination methods
   */
  goToPage(page: number): void {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.loadReviews();
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
   * Get star array for rating display
   */
  getStarArray(rating: number): boolean[] {
    return this.reviewService.getStarArray(rating).map(val => val === 1);
  }

  /**
   * Get initials from name
   */
  getInitials(name?: string): string {
    if (!name) return '?';
    return name.split(' ')
      .map(n => n.charAt(0))
      .slice(0, 2)
      .join('')
      .toUpperCase();
  }

  /**
   * Get distribution percentage
   */
  getDistributionPercentage(stars: number): number {
    if (!this.stats || this.stats.total_reviews === 0) return 0;
    const count = this.stats.rating_distribution[stars as keyof typeof this.stats.rating_distribution] || 0;
    return (count / this.stats.total_reviews) * 100;
  }

  /**
   * Get distribution count
   */
  getDistributionCount(stars: number): number {
    if (!this.stats) return 0;
    return this.stats.rating_distribution[stars as keyof typeof this.stats.rating_distribution] || 0;
  }

  /**
   * Get CSS class for rating badge
   */
  getRatingClass(rating: number): string {
    if (rating >= 4.5) return 'rating-excellent';
    if (rating >= 4.0) return 'rating-good';
    if (rating >= 3.0) return 'rating-average';
    return 'rating-poor';
  }

 
  /**
   * Format relative time
   */
  formatRelativeTime(dateString: string): string {
    return this.reviewService.getRelativeTime(dateString);
  }
}