// src/app/tenant/tenant-bookings/tenant-bookings.component.ts
import { Component, OnInit } from '@angular/core';
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
  styleUrls: ['./bookings.component.css']
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

  constructor(
    private bookingService: BookingService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadBookings();
    this.loadStatistics();
    this.loadUpcomingBookings();
  }

  loadBookings(): void {
    this.isLoading = true;
    this.errorMessage = '';

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
      },
      error: (error) => {
        console.error('Error loading bookings:', error);
        this.errorMessage = error.error?.error || 'Failed to load bookings';
        this.isLoading = false;
      }
    });
  }

  loadStatistics(): void {
    this.bookingService.getTenantStatistics().subscribe({
      next: (stats) => {
        this.statistics = stats;
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
        setTimeout(() => this.successMessage = '', 3000);
      },
      error: (error) => {
        this.errorMessage = error.error?.error || 'Failed to cancel booking';
        setTimeout(() => this.errorMessage = '', 3000);
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
        setTimeout(() => this.successMessage = '', 3000);
      },
      error: (error) => {
        this.errorMessage = error.error?.error || 'Failed to update booking';
        setTimeout(() => this.errorMessage = '', 3000);
      }
    });
  }

  closeModals(): void {
    this.showCancelModal = false;
    this.showUpdateModal = false;
    this.selectedBooking = null;
    this.cancellationReason = '';
  }

  viewBookingDetails(bookingId: string): void {
    this.router.navigate(['/tenant/bookings', bookingId]);
  }

  viewProperty(propertyId: string): void {
    this.router.navigate(['/properties', propertyId]);
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

  getImageUrl(images?: string[]): string {
    return images && images.length > 0 ? images[0] : '/assets/placeholder.jpg';
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