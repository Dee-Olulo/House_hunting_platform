// src/app/services/analytics.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment.development';

/**
 * High-level analytics summary: current totals, activity within the
 * selected period, and growth rates. Returned by GET /analytics/summary.
 */
export interface AnalyticsSummary {
  overview: {
    total_users: number;        // All-time user count
    total_properties: number;   // All-time property count
    total_bookings: number;     // All-time booking count
  };
  period_stats: {
    new_users: number;          // Users created within the period
    new_properties: number;     // Properties created within the period
    new_bookings: number;       // Bookings created within the period
    period_days: number;        // Length of the period in days
  };
  growth: {
    user_growth: number;        // % change in users vs. previous period
    property_growth: number;    // % change in properties vs. previous period
    booking_growth: number;     // % change in bookings vs. previous period
  };
}

/**
 * User engagement metrics over a time window.
 * Returned by GET /analytics/users/engagement.
 */
export interface UserEngagement {
  total_users: number;
  new_users: number;                                  // New signups in the period
  active_users: number;                               // Users active in the period
  retention_rate: number;                             // % of users retained
  users_by_role: Array<{_id: string; count: number}>; // Counts grouped by role (_id = role name)
  daily_trend: Array<{date: string; count: number}>;  // Per-day signup counts
  period_days: number;
}

/**
 * Property performance metrics, including the best-performing listings.
 * Returned by GET /analytics/properties/performance.
 */
export interface PropertyPerformance {
  total_properties: number;
  active_properties: number;                              // Currently active listings
  new_properties: number;                                 // Listings created in the period
  conversion_rate: number;                                // % of listings that convert to bookings
  avg_price: number;                                      // Average listing price
  properties_by_status: Array<{_id: string; count: number}>; // Counts grouped by status
  most_booked: Array<{                                    // Top listings ranked by bookings
    property_id: string;
    title: string;
    city: string;
    price: number;
    booking_count: number;
  }>;
  daily_trend: Array<{date: string; count: number}>;      // Per-day new-listing counts
  period_days: number;
}

/**
 * Geographic breakdown of properties and booking activity by location.
 * Returned by GET /analytics/geography/distribution.
 */
export interface GeographicDistribution {
  properties_by_city: Array<{          // Listing spread across cities
    city: string;
    property_count: number;
    avg_price: number;                 // Average price within that city
  }>;
  properties_by_type: Array<{_id: string; count: number}>; // Counts grouped by property type
  popular_cities: Array<{              // Cities ranked by booking volume
    city: string;
    booking_count: number;
  }>;
}

/**
 * Booking trend metrics over a time window.
 * Returned by GET /analytics/bookings/trends.
 */
export interface BookingTrends {
  total_bookings: number;
  period_bookings: number;                               // Bookings made in the period
  confirmed_bookings: number;                            // Bookings that reached confirmed status
  conversion_rate: number;                               // % of bookings confirmed
  bookings_by_status: Array<{_id: string; count: number}>; // Counts grouped by status
  daily_trend: Array<{date: string; count: number}>;     // Per-day booking counts
  period_days: number;
}

/**
 * Service for fetching analytics data and exporting it.
 * Provided in root, so a single instance is shared across the app.
 */
@Injectable({
  providedIn: 'root'
})
export class AnalyticsService {
  // Base URL for all analytics endpoints, built from the environment config.
  private API_URL = `${environment.apiUrl}/analytics`;

  constructor(private http: HttpClient) {}

  /**
   * Fetch the high-level analytics summary.
   * @param days Look-back window in days (defaults to 30).
   */
  getSummary(days: number = 30): Observable<AnalyticsSummary> {
    return this.http.get<AnalyticsSummary>(`${this.API_URL}/summary`, {
      params: { days: days.toString() }
    });
  }

  /**
   * Fetch user engagement metrics.
   * @param days Look-back window in days (defaults to 30).
   */
  getUserEngagement(days: number = 30): Observable<UserEngagement> {
    return this.http.get<UserEngagement>(`${this.API_URL}/users/engagement`, {
      params: { days: days.toString() }
    });
  }

  /**
   * Fetch property performance metrics.
   * @param days Look-back window in days (defaults to 30).
   */
  getPropertyPerformance(days: number = 30): Observable<PropertyPerformance> {
    return this.http.get<PropertyPerformance>(`${this.API_URL}/properties/performance`, {
      params: { days: days.toString() }
    });
  }

  /** Fetch the geographic distribution of properties and bookings (no time window). */
  getGeographicDistribution(): Observable<GeographicDistribution> {
    return this.http.get<GeographicDistribution>(`${this.API_URL}/geography/distribution`);
  }

  /**
   * Fetch booking trend metrics.
   * @param days Look-back window in days (defaults to 30).
   */
  getBookingTrends(days: number = 30): Observable<BookingTrends> {
    return this.http.get<BookingTrends>(`${this.API_URL}/bookings/trends`, {
      params: { days: days.toString() }
    });
  }

  // Export functionality

  /** Export the current view to PDF by opening the browser's print dialog. */
  exportToPDF(): void {
    // Relies on the browser's "Save as PDF" option in the print dialog.
    window.print();
  }

  /**
   * Export an array of records to a downloadable CSV file.
   * (Despite the name, the output is CSV, which Excel opens natively.)
   * @param data     Array of row objects to export.
   * @param filename Base filename; the current date is appended automatically.
   */
  exportToExcel(data: any, filename: string): void {
    // Build the CSV text from the data.
    const csv = this.convertToCSV(data);
    // Wrap it in a Blob and create a temporary object URL to download from.
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    // Create a hidden anchor and trigger a click to start the download.
    const link = document.createElement('a');
    link.href = url;
    link.download = `${filename}_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    // Release the object URL to free memory.
    window.URL.revokeObjectURL(url);
  }

  /**
   * Convert an array of objects into a CSV string.
   * Column headers are derived from the keys of the first row.
   * @param data Array of uniform row objects.
   * @returns CSV text, or an empty string if there is no data.
   */
  private convertToCSV(data: any): string {
    if (!data || data.length === 0) return '';

    // Use the first row's keys as the header row.
    const headers = Object.keys(data[0]);
    const csvRows = [headers.join(',')];

    // Build one CSV line per row, quoting string values.
    for (const row of data) {
      const values = headers.map(header => {
        const value = row[header];
        return typeof value === 'string' ? `"${value}"` : value;
      });
      csvRows.push(values.join(','));
    }

    return csvRows.join('\n');
  }
}