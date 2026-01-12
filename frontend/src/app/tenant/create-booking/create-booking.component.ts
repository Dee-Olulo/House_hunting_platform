// src/app/tenant/create-booking/create-booking.component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { BookingService } from '../../services/booking.service';
import { PropertyService, Property } from '../../services/property.service';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-create-booking',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './create-booking.component.html',
  styleUrls: ['./create-booking.component.css']
})
export class CreateBookingComponent implements OnInit {
  bookingForm!: FormGroup;
  property: Property | null = null;
  propertyId: string = '';
  isLoading = false;
  isLoadingProperty = true;
  errorMessage = '';
  successMessage = '';
  currentUser: any = null;

  // Minimum date (today)
  minDate: string = '';
  // Maximum date (6 months from now)
  maxDate: string = '';

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private router: Router,
    private bookingService: BookingService,
    private propertyService: PropertyService,
    private authService: AuthService
  ) {
    this.initializeDates();
  }

  ngOnInit(): void {
    // Get property ID from route
    this.propertyId = this.route.snapshot.params['id'];
    
    // Get current user
    this.currentUser = this.authService.getCurrentUser();
    
    // Initialize form
    this.initializeForm();
    
    // Load property details
    this.loadProperty();
  }

  initializeDates(): void {
    const today = new Date();
    this.minDate = today.toISOString().split('T')[0];
    
    const maxDate = new Date();
    maxDate.setMonth(maxDate.getMonth() + 6);
    this.maxDate = maxDate.toISOString().split('T')[0];
  }

  initializeForm(): void {
    this.bookingForm = this.fb.group({
      booking_type: ['viewing', Validators.required],
      booking_date: ['', [Validators.required]],
      booking_time: ['', [Validators.required]],
      tenant_name: [this.currentUser?.name || '', [Validators.required, Validators.minLength(2)]],
      tenant_email: [this.currentUser?.email || '', [Validators.required, Validators.email]],
      tenant_phone: ['', [Validators.pattern(/^\+?[0-9]{10,15}$/)]],
      message: ['', [Validators.maxLength(1000)]]
    });
  }

  loadProperty(): void {
    this.isLoadingProperty = true;
    this.propertyService.getProperty(this.propertyId).subscribe({
      next: (property) => {
        this.property = property;
        this.isLoadingProperty = false;
      },
      error: (error) => {
        console.error('Error loading property:', error);
        this.errorMessage = 'Property not found';
        this.isLoadingProperty = false;
      }
    });
  }

  onSubmit(): void {
    if (this.bookingForm.invalid) {
      this.markFormGroupTouched(this.bookingForm);
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';
    this.successMessage = '';

    const bookingData = {
      property_id: this.propertyId,
      ...this.bookingForm.value
    };

    this.bookingService.createBooking(bookingData).subscribe({
      next: (response) => {
        this.successMessage = response.message;
        this.isLoading = false;
        
        // Redirect to tenant bookings after 2 seconds
        setTimeout(() => {
          this.router.navigate(['/tenant/bookings']);
        }, 2000);
      },
      error: (error) => {
        console.error('Error creating booking:', error);
        this.errorMessage = error.error?.error || 'Failed to create booking';
        if (error.error?.details) {
          this.errorMessage += ': ' + error.error.details.join(', ');
        }
        this.isLoading = false;
      }
    });
  }

  markFormGroupTouched(formGroup: FormGroup): void {
    Object.keys(formGroup.controls).forEach(key => {
      const control = formGroup.get(key);
      control?.markAsTouched();
    });
  }

  isFieldInvalid(fieldName: string): boolean {
    const field = this.bookingForm.get(fieldName);
    return !!(field && field.invalid && field.touched);
  }

  getFieldError(fieldName: string): string {
    const field = this.bookingForm.get(fieldName);
    if (field?.hasError('required')) return `${fieldName} is required`;
    if (field?.hasError('email')) return 'Invalid email format';
    if (field?.hasError('minlength')) return `${fieldName} is too short`;
    if (field?.hasError('maxlength')) return `${fieldName} is too long`;
    if (field?.hasError('pattern')) return 'Invalid format';
    return '';
  }

  goBack(): void {
    window.history.back();
  }

  getImageUrl(imagePath: string): string {
    return this.propertyService.getImageUrl(imagePath);
  }

  getPropertyImage(): string {
    if (this.property?.images && this.property.images.length > 0) {
      return this.getImageUrl(this.property.images[0]);
    }
    return '/assets/placeholder.jpg';
  }
}