// src/app/tenant/tenant-bookings/tenant-bookings.component.ts (FIXED)
import { Component, OnInit, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { BookingService } from '../../services/booking.service';
import { Booking, BookingFilters } from '../../services/booking.interface';

@Component({
  selector: 'app-tenant-bookings',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './bookings.component.html',
  styleUrls: ['./bookings.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush // Added OnPush strategy
})
export class TenantBookingsComponent implements OnInit {
  bookings: Booking[] = [];
  filteredBookings: Booking[] = [];
  isLoading = false;
  errorMessage = '';
  successMessage = '';

  // Filters
  filterStatus: string = '';
  filterType: string = '';
  filterFromDate: string = '';
  filterToDate: string = '';

  // Pagination
  currentPage = 1;
  totalPages = 1;
  perPage = 20;
  totalBookings = 0;

  // Statistics
  statistics: any = null;
  upcomingBookings: Booking[] = [];

  // Modal state
  selectedBooking: Booking | null = null;
  showCancelModal = false;
  showUpdateModal = false;
  cancellationReason = '';
  
  // Update form data
  updateForm = {
    booking_date: '',
    booking_time: '',
    message: ''
  };

  // Prevent double navigation
  private isNavigating = false;

  constructor(
    private bookingService: BookingService,
    private router: Router,
    private cdr: ChangeDetectorRef // Added ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.loadBookings();
    this.loadStatistics();
    this.loadUpcomingBookings();
  }

  loadBookings(): void {
    this.isLoading = true;
    this.errorMessage = '';
    this.cdr.markForCheck();

    const filters: BookingFilters = {
      page: this.currentPage,
      per_page: this.perPage
    };

    if (this.filterStatus) filters.status = this.filterStatus;
    if (this.filterType) filters.booking_type = this.filterType;
    if (this.filterFromDate) filters.from_date = this.filterFromDate;
    if (this.filterToDate) filters.to_date = this.filterToDate;

    this.bookingService.getTenantBookings(filters).subscribe({
      next: (response) => {
        this.bookings = response.bookings;
        this.filteredBookings = response.bookings;
        this.totalBookings = response.total;
        this.totalPages = response.total_pages;
        this.isLoading = false;
        this.cdr.markForCheck();
      },
      error: (error) => {
        console.error('Error loading bookings:', error);
        this.errorMessage = error.error?.error || 'Failed to load bookings';
        this.isLoading = false;
        this.cdr.markForCheck();
      }
    });
  }

  loadStatistics(): void {
    this.bookingService.getTenantStatistics().subscribe({
      next: (stats) => {
        this.statistics = stats;
        this.cdr.markForCheck();
      },
      error: (error) => {
        console.error('Error loading statistics:', error);
      }
    });
  }

  loadUpcomingBookings(): void {
    this.bookingService.getTenantUpcomingBookings().subscribe({
      next: (response) => {
        this.upcomingBookings = response.bookings;
        this.cdr.markForCheck();
      },
      error: (error) => {
        console.error('Error loading upcoming bookings:', error);
      }
    });
  }

  applyFilters(): void {
    this.currentPage = 1;
    this.loadBookings();
  }

  clearFilters(): void {
    this.filterStatus = '';
    this.filterType = '';
    this.filterFromDate = '';
    this.filterToDate = '';
    this.currentPage = 1;
    this.loadBookings();
  }

  openCancelModal(booking: Booking): void {
    this.selectedBooking = booking;
    this.cancellationReason = '';
    this.showCancelModal = true;
    this.cdr.markForCheck();
  }

  cancelBooking(): void {
    if (!this.cancellationReason.trim()) {
      alert('Please provide a cancellation reason');
      return;
    }

    this.bookingService.cancelBooking(this.selectedBooking!._id!, this.cancellationReason).subscribe({
      next: (response) => {
        this.successMessage = response.message;
        this.closeModals();
        this.loadBookings();
        this.loadUpcomingBookings();
        this.cdr.markForCheck();
        setTimeout(() => {
          this.successMessage = '';
          this.cdr.markForCheck();
        }, 3000);
      },
      error: (error) => {
        this.errorMessage = error.error?.error || 'Failed to cancel booking';
        this.cdr.markForCheck();
        setTimeout(() => {
          this.errorMessage = '';
          this.cdr.markForCheck();
        }, 3000);
      }
    });
  }

  openUpdateModal(booking: Booking): void {
    this.selectedBooking = booking;
    this.updateForm = {
      booking_date: booking.booking_date,
      booking_time: booking.booking_time,
      message: booking.message || ''
    };
    this.showUpdateModal = true;
    this.cdr.markForCheck();
  }

  updateBooking(): void {
    const updates: any = {};
    
    if (this.updateForm.booking_date !== this.selectedBooking!.booking_date) {
      updates.booking_date = this.updateForm.booking_date;
    }
    if (this.updateForm.booking_time !== this.selectedBooking!.booking_time) {
      updates.booking_time = this.updateForm.booking_time;
    }
    if (this.updateForm.message) {
      updates.message = this.updateForm.message;
    }

    if (Object.keys(updates).length === 0) {
      alert('No changes made');
      return;
    }

    this.bookingService.updateTenantBooking(this.selectedBooking!._id!, updates).subscribe({
      next: (response) => {
        this.successMessage = 'Booking updated successfully';
        this.closeModals();
        this.loadBookings();
        this.cdr.markForCheck();
        setTimeout(() => {
          this.successMessage = '';
          this.cdr.markForCheck();
        }, 3000);
      },
      error: (error) => {
        this.errorMessage = error.error?.error || 'Failed to update booking';
        this.cdr.markForCheck();
        setTimeout(() => {
          this.errorMessage = '';
          this.cdr.markForCheck();
        }, 3000);
      }
    });
  }

  closeModals(): void {
    this.showCancelModal = false;
    this.showUpdateModal = false;
    this.selectedBooking = null;
    this.cancellationReason = '';
    this.cdr.markForCheck();
  }

  /**
   * View booking details with navigation guard
   */
  viewBookingDetails(bookingId: string, event?: MouseEvent): void {
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }

    if (this.isNavigating) {
      console.log('⚠️ Navigation already in progress');
      return;
    }

    console.log('🔵 Viewing booking:', bookingId);
    this.isNavigating = true;

    this.router.navigate(['/tenant/bookings', bookingId]).then(success => {
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
   * View property with navigation guard
   */
  viewProperty(propertyId: string, event?: MouseEvent): void {
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

  goToPage(page: number): void {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.loadBookings();
    }
  }

  previousPage(): void {
    this.goToPage(this.currentPage - 1);
  }

  nextPage(): void {
    this.goToPage(this.currentPage + 1);
  }

  getStatusClass(status: string): string {
    return this.bookingService.getStatusClass(status);
  }

  getStatusText(status: string): string {
    return this.bookingService.getStatusText(status);
  }

  getBookingTypeText(type: string): string {
    return this.bookingService.getBookingTypeText(type);
  }

  formatDate(dateString: string): string {
    return this.bookingService.formatDate(dateString);
  }

  formatTime(timeString: string): string {
    return this.bookingService.formatTime(timeString);
  }

  /**
   * Get image URL with proper backend path
   */
  getImageUrl(booking: Booking): string {
    // Check if property_details exists and has images
    if (booking.property_details?.images && booking.property_details.images.length > 0) {
      const imagePath = booking.property_details.images[0];
      return this.constructImageUrl(imagePath);
    }
    
    return '/assets/placeholder.jpg';
  }

  private constructImageUrl(imagePath: string): string {
    if (!imagePath) {
      return '/assets/placeholder.jpg';
    }

    // If it's already a full URL, return as is
    if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
      return imagePath;
    }
    
    // CHANGE THIS TO YOUR ACTUAL BACKEND URL
    const backendUrl = 'http://localhost:3000'; // Adjust to your backend port
    
    // If it's a relative path starting with 'uploads/', prepend backend URL
    if (imagePath.startsWith('uploads/')) {
      return `${backendUrl}/${imagePath}`;
    }
    
    // If it starts with /, it's an absolute path
    if (imagePath.startsWith('/')) {
      return `${backendUrl}${imagePath}`;
    }
    
    // Otherwise, assume it's in uploads/images/
    return `${backendUrl}/uploads/images/${imagePath}`;
  }

  /**
   * Handle image error
   */
  handleImageError(event: any): void {
    event.target.src = '/assets/placeholder.jpg';
  }

  canUpdate(booking: Booking): boolean {
    return booking.status === 'pending';
  }

  canCancel(booking: Booking): boolean {
    return booking.status === 'pending' || booking.status === 'confirmed';
  }

  getStatusCount(status: string): number {
    if (!this.statistics?.status_breakdown) return 0;
    const stat = this.statistics.status_breakdown.find((s: any) => s._id === status);
    return stat ? stat.count : 0;
  }
}