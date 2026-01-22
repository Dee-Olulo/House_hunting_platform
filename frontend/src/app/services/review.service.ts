// src/app/services/review.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment.development';

export interface Review {
  _id: string;
  tenant_id: string;
  tenant_name?:string;
  landlord_id: string;
  landlord_email: string;
  property_id: string;
  property_title: string;
  rating: number;
  title: string;
  comment: string;
  categories: {
    communication: number;
    responsiveness: number;
    property_accuracy: number;
    cleanliness: number;
    value_for_money: number;
  };
  is_verified: boolean;
  helpful_count: number;
  created_at: string;
  updated_at: string;
}

export interface ReviewStats {
  average_rating: number;
  total_reviews: number;
  rating_distribution: {
     [key: number]: number;
  };
  category_ratings: {
    communication: number;
    responsiveness: number;
    property_accuracy: number;
    cleanliness: number;
    value_for_money: number;
  };
}

@Injectable({
  providedIn: 'root'
})
export class ReviewService {
  private API_URL = `${environment.apiUrl}/reviews`;

  constructor(private http: HttpClient) {}

  createReview(review: {
    landlord_id: string;
    property_id: string;
    rating: number;
    title: string;
    comment: string;
    categories: any;
  }): Observable<any> {
    return this.http.post(`${this.API_URL}/create`, review);
  }

  getLandlordReviews(landlordId: string, params?: any): Observable<any> {
    return this.http.get(`${this.API_URL}/landlord/${landlordId}`, { params });
  }

  getMyReviews(): Observable<{ reviews: Review[] }> {
    return this.http.get<{ reviews: Review[] }>(`${this.API_URL}/my-reviews`);
  }

  getReviewsAboutMe(params?: any): Observable<any> {
    return this.http.get(`${this.API_URL}/about-me`, { params });
  }

  updateReview(reviewId: string, data: any): Observable<any> {
    return this.http.put(`${this.API_URL}/${reviewId}`, data);
  }

  deleteReview(reviewId: string): Observable<any> {
    return this.http.delete(`${this.API_URL}/${reviewId}`);
  }

  markHelpful(reviewId: string): Observable<any> {
    return this.http.post(`${this.API_URL}/${reviewId}/helpful`, {});
  }

  reportReview(reviewId: string, reason: string): Observable<any> {
    return this.http.post(`${this.API_URL}/${reviewId}/report`, { reason });
  }

  getStarArray(rating: number): number[] {
    return Array(5).fill(0).map((_, i) => i < Math.round(rating) ? 1 : 0);
  }

  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  }

  getRelativeTime(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) {
      return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
    } else if (diffHours < 24) {
      return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    } else if (diffDays < 30) {
      return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    } else {
      return this.formatDate(dateString);
    }
  }
}

