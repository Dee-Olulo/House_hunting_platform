import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment.development';
import { 
  Booking, 
  CreateBookingRequest, 
  BookingResponse, 
  BookingStatistics,
  BookingFilters 
} from './booking.interface';

@Injectable({
  providedIn: 'root'
})
export class BookingService {
  private API_URL = `${environment.apiUrl}/bookings`;

  constructor(private http: HttpClient) {}

  // ============================================
  // LANDLORD ENDPOINTS
  // ============================================

  /**
   * Get all bookings for landlord's properties with optional filters
   */
  getLandlordBookings(filters?: BookingFilters): Observable<BookingResponse> {
    let params = new HttpParams();
    
    if (filters) {
      if (filters.status) params = params.set('status', filters.status);
      if (filters.property_id) params = params.set('property_id', filters.property_id);
      if (filters.booking_type) params = params.set('booking_type', filters.booking_type);
      if (filters.from_date) params = params.set('from_date', filters.from_date);
      if (filters.to_date) params = params.set('to_date', filters.to_date);
      if (filters.page) params = params.set('page', filters.page.toString());
      if (filters.per_page) params = params.set('per_page', filters.per_page.toString());
    }

    return this.http.get<BookingResponse>(`${this.API_URL}/landlord/my-bookings`, { params });
  }

  /**
   * Get single booking details (landlord view)
   */
  getLandlordBookingDetails(bookingId: string): Observable<Booking> {
    return this.http.get<Booking>(`${this.API_URL}/landlord/${bookingId}`);
  }

  /**
   * Confirm a pending booking
   */
  confirmBooking(bookingId: string, notes?: string): Observable<{ message: string; booking_id: string; status: string }> {
    const body = notes ? { notes } : {};
    return this.http.put<{ message: string; booking_id: string; status: string }>(
      `${this.API_URL}/landlord/${bookingId}/confirm`,
      body
    );
  }

  /**
   * Reject a pending booking
   */
  rejectBooking(bookingId: string, rejection_reason: string): Observable<{ message: string; booking_id: string; status: string }> {
    return this.http.put<{ message: string; booking_id: string; status: string }>(
      `${this.API_URL}/landlord/${bookingId}/reject`,
      { rejection_reason }
    );
  }

  /**
   * Mark a confirmed booking as completed
   */
  completeBooking(bookingId: string, notes?: string): Observable<{ message: string; booking_id: string; status: string }> {
    const body = notes ? { notes } : {};
    return this.http.put<{ message: string; booking_id: string; status: string }>(
      `${this.API_URL}/landlord/${bookingId}/complete`,
      body
    );
  }

  /**
   * Add or update internal notes
   */
  updateBookingNotes(bookingId: string, notes: string): Observable<{ message: string; booking_id: string }> {
    return this.http.put<{ message: string; booking_id: string }>(
      `${this.API_URL}/landlord/${bookingId}/notes`,
      { notes }
    );
  }

  /**
   * Get landlord booking statistics
   */
  getLandlordStatistics(): Observable<BookingStatistics> {
    return this.http.get<BookingStatistics>(`${this.API_URL}/landlord/statistics`);
  }

  /**
   * Get upcoming confirmed bookings
   */
  getLandlordUpcomingBookings(): Observable<{ bookings: Booking[]; count: number }> {
    return this.http.get<{ bookings: Booking[]; count: number }>(`${this.API_URL}/landlord/upcoming`);
  }

  // ============================================
  // TENANT ENDPOINTS
  // ============================================

  /**
   * Create a new booking request
   */
  createBooking(bookingData: CreateBookingRequest): Observable<{
    message: string;
    booking_id: string;
    status: string;
    property_title: string;
    booking_date: string;
    booking_time: string;
  }> {
    return this.http.post<{
      message: string;
      booking_id: string;
      status: string;
      property_title: string;
      booking_date: string;
      booking_time: string;
    }>(`${this.API_URL}/tenant/create`, bookingData);
  }

  /**
   * Get all tenant's bookings with optional filters
   */
  getTenantBookings(filters?: BookingFilters): Observable<BookingResponse> {
    let params = new HttpParams();
    
    if (filters) {
      if (filters.status) params = params.set('status', filters.status);
      if (filters.booking_type) params = params.set('booking_type', filters.booking_type);
      if (filters.from_date) params = params.set('from_date', filters.from_date);
      if (filters.to_date) params = params.set('to_date', filters.to_date);
      if (filters.page) params = params.set('page', filters.page.toString());
      if (filters.per_page) params = params.set('per_page', filters.per_page.toString());
    }

    return this.http.get<BookingResponse>(`${this.API_URL}/tenant/my-bookings`, { params });
  }

  /**
   * Get single booking details (tenant view)
   */
  getTenantBookingDetails(bookingId: string): Observable<Booking> {
    return this.http.get<Booking>(`${this.API_URL}/tenant/${bookingId}`);
  }

  /**
   * Cancel a booking
   */
  cancelBooking(bookingId: string, cancellation_reason: string): Observable<{ message: string; booking_id: string; status: string }> {
    return this.http.put<{ message: string; booking_id: string; status: string }>(
      `${this.API_URL}/tenant/${bookingId}/cancel`,
      { cancellation_reason }
    );
  }

  /**
   * Update a pending booking
   */
  updateTenantBooking(bookingId: string, updates: Partial<CreateBookingRequest>): Observable<{ message: string; booking_id: string }> {
    return this.http.put<{ message: string; booking_id: string }>(
      `${this.API_URL}/tenant/${bookingId}/update`,
      updates
    );
  }

  /**
   * Get tenant booking statistics
   */
  getTenantStatistics(): Observable<BookingStatistics> {
    return this.http.get<BookingStatistics>(`${this.API_URL}/tenant/statistics`);
  }

  /**
   * Get upcoming confirmed bookings for tenant
   */
  getTenantUpcomingBookings(): Observable<{ bookings: Booking[]; count: number }> {
    return this.http.get<{ bookings: Booking[]; count: number }>(`${this.API_URL}/tenant/upcoming`);
  }

  // ============================================
  // HELPER METHODS
  // ============================================

  /**
   * Get status badge class for styling
   */
  getStatusClass(status: string): string {
    const statusClasses: { [key: string]: string } = {
      'pending': 'status-pending',
      'confirmed': 'status-confirmed',
      'rejected': 'status-rejected',
      'completed': 'status-completed',
      'cancelled': 'status-cancelled'
    };
    return statusClasses[status] || 'status-default';
  }

  /**
   * Get status display text
   */
  getStatusText(status: string): string {
    const statusTexts: { [key: string]: string } = {
      'pending': 'Pending',
      'confirmed': 'Confirmed',
      'rejected': 'Rejected',
      'completed': 'Completed',
      'cancelled': 'Cancelled'
    };
    return statusTexts[status] || status;
  }

  /**
   * Get booking type display text
   */
  getBookingTypeText(type: string): string {
    const typeTexts: { [key: string]: string } = {
      'viewing': 'Property Viewing',
      'rental_inquiry': 'Rental Inquiry'
    };
    return typeTexts[type] || type;
  }

  /**
   * Format date for display
   */
  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }

  /**
   * Format time for display
   */
  formatTime(timeString: string): string {
    const [hours, minutes] = timeString.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 || 12;
    return `${displayHour}:${minutes} ${ampm}`;
  }
}