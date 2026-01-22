// src/app/tenant/create-review/create-review.component.ts
import { Component, Input, Output, EventEmitter, OnChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ReviewService } from '../../services/review.service';

@Component({
  selector: 'app-create-review',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './create-review.html',
  styleUrls: ['./create-review.css']
})
export class CreateReviewComponent implements OnChanges {
  @Input() isOpen = false;
  @Input() landlordId = '';
  @Input() propertyId = '';
  @Output() reviewCreated = new EventEmitter<void>();
  @Output() closed = new EventEmitter<void>();

  rating = 0;
  title = '';
  comment = '';
  isSubmitting = false;
  errorMessage = '';
  
  categories = [
    { key: 'communication', label: '💬 Communication', value: 0 },
    { key: 'responsiveness', label: '⚡ Responsiveness', value: 0 },
    { key: 'property_accuracy', label: '🎯 Property Accuracy', value: 0 },
    { key: 'cleanliness', label: '✨ Cleanliness', value: 0 },
    { key: 'value_for_money', label: '💰 Value for Money', value: 0 }
  ];

  constructor(private reviewService: ReviewService) {}

  ngOnChanges(): void {
    if (!this.isOpen) {
      this.resetForm();
    }
  }

  resetForm(): void {
    this.rating = 0;
    this.title = '';
    this.comment = '';
    this.categories.forEach(cat => cat.value = 0);
    this.errorMessage = '';
    this.isSubmitting = false;
  }

  submitReview(): void {
    if (!this.isValid()) {
      this.errorMessage = 'Please fill all required fields';
      return;
    }

    this.isSubmitting = true;
    this.errorMessage = '';

    const categoryRatings: any = {};
    this.categories.forEach(cat => {
      categoryRatings[cat.key] = cat.value;
    });

    const reviewData = {
      landlord_id: this.landlordId,
      property_id: this.propertyId,
      rating: this.rating,
      title: this.title.trim(),
      comment: this.comment.trim(),
      categories: categoryRatings
    };

    console.log('Submitting review:', reviewData);

    this.reviewService.createReview(reviewData).subscribe({
      next: (response) => {
        console.log('✅ Review created successfully:', response);
        this.reviewCreated.emit();
        this.close();
      },
      error: (error) => {
        console.error('❌ Error creating review:', error);
        this.errorMessage = error.error?.error || 'Failed to submit review. Please try again.';
        this.isSubmitting = false;
      }
    });
  }

  isValid(): boolean {
    return this.rating > 0 && 
           this.title.trim().length > 0 && 
           this.comment.trim().length >= 10 &&
           this.categories.every(cat => cat.value > 0);
  }

  setRating(stars: number): void {
    this.rating = stars;
  }

  setCategoryRating(categoryIndex: number, stars: number): void {
    this.categories[categoryIndex].value = stars;
  }

  close(): void {
    this.closed.emit();
  }

  getStarArray(): number[] {
    return [1, 2, 3, 4, 5];
  }
}