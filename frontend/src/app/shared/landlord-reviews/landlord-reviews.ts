// src/app/shared/landlord-reviews/landlord-reviews.component.ts
import { Component, Input, OnInit, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReviewService, Review, ReviewStats } from '../../services/review.service';

@Component({
  selector: 'app-landlord-reviews',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './landlord-reviews.html',
  styleUrls: ['./landlord-reviews.css']
})
export class LandlordReviewsComponent implements OnInit, OnChanges {
  @Input() landlordId: string = '';

  reviews: Review[] = [];
  stats: ReviewStats | null = null;
  isLoading = true;
  errorMessage = '';

  // Pagination
  currentPage = 1;
  totalPages = 1;
  perPage = 5;

  constructor(private reviewService: ReviewService) {}

  ngOnInit(): void {
    if (this.landlordId) {
      this.loadReviews();
    }
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['landlordId'] && !changes['landlordId'].firstChange) {
      this.loadReviews();
    }
  }

  loadReviews(): void {
    if (!this.landlordId) {
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';

    const params = {
      page: this.currentPage,
      per_page: this.perPage,
      sort_by: 'newest'
    };

    this.reviewService.getLandlordReviews(this.landlordId, params).subscribe({
      next: (response) => {
        console.log('✅ Reviews loaded:', response);
        this.reviews = response.reviews || [];
        this.stats = response.statistics || null;
        this.totalPages = response.total_pages || 1;
        this.isLoading = false;
      },
      error: (error) => {
        console.error('❌ Error loading reviews:', error);
        this.errorMessage = 'Failed to load reviews';
        this.isLoading = false;
      }
    });
  }

  goToPage(page: number): void {
    if (page >= 1 && page <= this.totalPages && page !== this.currentPage) {
      this.currentPage = page;
      this.loadReviews();
      this.scrollToTop();
    }
  }

  previousPage(): void {
    this.goToPage(this.currentPage - 1);
  }

  nextPage(): void {
    this.goToPage(this.currentPage + 1);
  }

  scrollToTop(): void {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  getStarArray(rating: number): boolean[] {
    return this.reviewService.getStarArray(rating).map(val => val === 1);
  }

  getRelativeTime(dateString: string): string {
    return this.reviewService.getRelativeTime(dateString);
  }

  getDistributionPercentage(stars: number): number {
    if (!this.stats || this.stats.total_reviews === 0) return 0;
    const count = this.stats.rating_distribution[stars] || 0;
    return (count / this.stats.total_reviews) * 100;
  }

  getDistributionCount(stars: number): number {
    if (!this.stats) return 0;
    return this.stats.rating_distribution[stars] || 0;
  }

  getRatingClass(rating: number): string {
    if (rating >= 4.5) return 'rating-excellent';
    if (rating >= 4.0) return 'rating-good';
    if (rating >= 3.0) return 'rating-average';
    return 'rating-poor';
  }
}