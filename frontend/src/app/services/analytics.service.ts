// src/app/services/analytics.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment.development';

export interface AnalyticsSummary {
  overview: {
    total_users: number;
    total_properties: number;
    total_bookings: number;
  };
  period_stats: {
    new_users: number;
    new_properties: number;
    new_bookings: number;
    period_days: number;
  };
  growth: {
    user_growth: number;
    property_growth: number;
    booking_growth: number;
  };
}

export interface UserEngagement {
  total_users: number;
  new_users: number;
  active_users: number;
  retention_rate: number;
  users_by_role: Array<{_id: string; count: number}>;
  daily_trend: Array<{date: string; count: number}>;
  period_days: number;
}

export interface PropertyPerformance {
  total_properties: number;
  active_properties: number;
  new_properties: number;
  conversion_rate: number;
  avg_price: number;
  properties_by_status: Array<{_id: string; count: number}>;
  most_booked: Array<{
    property_id: string;
    title: string;
    city: string;
    price: number;
    booking_count: number;
  }>;
  daily_trend: Array<{date: string; count: number}>;
  period_days: number;
}

export interface GeographicDistribution {
  properties_by_city: Array<{
    city: string;
    property_count: number;
    avg_price: number;
  }>;
  properties_by_type: Array<{_id: string; count: number}>;
  popular_cities: Array<{
    city: string;
    booking_count: number;
  }>;
}

export interface BookingTrends {
  total_bookings: number;
  period_bookings: number;
  confirmed_bookings: number;
  conversion_rate: number;
  bookings_by_status: Array<{_id: string; count: number}>;
  daily_trend: Array<{date: string; count: number}>;
  period_days: number;
}

@Injectable({
  providedIn: 'root'
})
export class AnalyticsService {
  private API_URL = `${environment.apiUrl}/analytics`;

  constructor(private http: HttpClient) {}

  getSummary(days: number = 30): Observable<AnalyticsSummary> {
    return this.http.get<AnalyticsSummary>(`${this.API_URL}/summary`, {
      params: { days: days.toString() }
    });
  }

  getUserEngagement(days: number = 30): Observable<UserEngagement> {
    return this.http.get<UserEngagement>(`${this.API_URL}/users/engagement`, {
      params: { days: days.toString() }
    });
  }

  getPropertyPerformance(days: number = 30): Observable<PropertyPerformance> {
    return this.http.get<PropertyPerformance>(`${this.API_URL}/properties/performance`, {
      params: { days: days.toString() }
    });
  }

  getGeographicDistribution(): Observable<GeographicDistribution> {
    return this.http.get<GeographicDistribution>(`${this.API_URL}/geography/distribution`);
  }

  getBookingTrends(days: number = 30): Observable<BookingTrends> {
    return this.http.get<BookingTrends>(`${this.API_URL}/bookings/trends`, {
      params: { days: days.toString() }
    });
  }

  // Export functionality
  exportToPDF(): void {
    // This will trigger browser print dialog
    window.print();
  }

  exportToExcel(data: any, filename: string): void {
    // Convert data to CSV
    const csv = this.convertToCSV(data);
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${filename}_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    window.URL.revokeObjectURL(url);
  }

  private convertToCSV(data: any): string {
    if (!data || data.length === 0) return '';
    
    const headers = Object.keys(data[0]);
    const csvRows = [headers.join(',')];
    
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