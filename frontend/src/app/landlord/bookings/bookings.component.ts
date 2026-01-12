import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { BookingService } from '../../services/booking.service';
import { Booking, BookingFilters } from '../../services/booking.interface';

@Component({
  selector: 'app-landlord-bookings',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './bookings.component.html',
  styleUrls: ['./bookings.component.css']
})
export class LandlordBookingsComponent implements OnInit {
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
  showRejectModal = false;
  showCompleteModal = false;
  showNotesModal = false;
  rejectionReason = '';
  completionNotes = '';
  internalNotes = '';

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

    this.bookingService.getLandlordBookings(filters).subscribe({
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
    this.bookingService.getLandlordStatistics().subscribe({
      next: (stats) => {
        this.statistics = stats;
      },
      error: (error) => {
        console.error('Error loading statistics:', error);
      }
    });
  }

  loadUpcomingBookings(): void {
    this.bookingService.getLandlordUpcomingBookings().subscribe({
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

  confirmBooking(booking: Booking): void {
    if (confirm(`Confirm booking for ${booking.tenant_name}?`)) {
      this.bookingService.confirmBooking(booking._id!).subscribe({
        next: (response) => {
          this.successMessage = response.message;
          this.loadBookings();
          this.loadUpcomingBookings();
          setTimeout(() => this.successMessage = '', 3000);
        },
        error: (error) => {
          this.errorMessage = error.error?.error || 'Failed to confirm booking';
          setTimeout(() => this.errorMessage = '', 3000);
        }
      });
    }
  }

  openRejectModal(booking: Booking): void {
    this.selectedBooking = booking;
    this.rejectionReason = '';
    this.showRejectModal = true;
  }

  rejectBooking(): void {
    if (!this.rejectionReason.trim()) {
      alert('Please provide a rejection reason');
      return;
    }

    this.bookingService.rejectBooking(this.selectedBooking!._id!, this.rejectionReason).subscribe({
      next: (response) => {
        this.successMessage = response.message;
        this.closeModals();
        this.loadBookings();
        setTimeout(() => this.successMessage = '', 3000);
      },
      error: (error) => {
        this.errorMessage = error.error?.error || 'Failed to reject booking';
        setTimeout(() => this.errorMessage = '', 3000);
      }
    });
  }

  openCompleteModal(booking: Booking): void {
    this.selectedBooking = booking;
    this.completionNotes = '';
    this.showCompleteModal = true;
  }

  completeBooking(): void {
    this.bookingService.completeBooking(this.selectedBooking!._id!, this.completionNotes).subscribe({
      next: (response) => {
        this.successMessage = response.message;
        this.closeModals();
        this.loadBookings();
        setTimeout(() => this.successMessage = '', 3000);
      },
      error: (error) => {
        this.errorMessage = error.error?.error || 'Failed to complete booking';
        setTimeout(() => this.errorMessage = '', 3000);
      }
    });
  }

  openNotesModal(booking: Booking): void {
    this.selectedBooking = booking;
    this.internalNotes = booking.notes || '';
    this.showNotesModal = true;
  }

  saveNotes(): void {
    this.bookingService.updateBookingNotes(this.selectedBooking!._id!, this.internalNotes).subscribe({
      next: (response) => {
        this.successMessage = 'Notes updated successfully';
        this.closeModals();
        this.loadBookings();
        setTimeout(() => this.successMessage = '', 3000);
      },
      error: (error) => {
        this.errorMessage = error.error?.error || 'Failed to update notes';
        setTimeout(() => this.errorMessage = '', 3000);
      }
    });
  }

  closeModals(): void {
    this.showRejectModal = false;
    this.showCompleteModal = false;
    this.showNotesModal = false;
    this.selectedBooking = null;
    this.rejectionReason = '';
    this.completionNotes = '';
    this.internalNotes = '';
  }

  viewBookingDetails(bookingId: string): void {
    this.router.navigate(['/landlord/bookings', bookingId]);
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
}