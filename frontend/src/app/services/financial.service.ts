// src/app/services/financial.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment.development';

export interface FinancialOverview {
  summary: {
    total_revenue: number;
    subscription_revenue: number;
    commission_revenue: number;
    mrr: number;
    period_days: number;
  };
  subscription_breakdown: Array<{
    _id: string;
    revenue: number;
    count: number;
  }>;
  commission_breakdown: Array<{
    tier: string;
    bookings: number;
    commission_rate: number;
    estimated_revenue: number;
  }>;
  active_subscriptions: {
    free: number;
    basic: number;
    premium: number;
  };
  daily_trend: Array<{
    date: string;
    revenue: number;
  }>;
}

export interface SubscriptionAnalytics {
  tier_distribution: Array<{ _id: string; count: number }>;
  new_subscriptions: Array<{
    _id: string;
    count: number;
    revenue: number;
  }>;
  churn_rate: number;
  expiring_soon: number;
  total_paid_subscribers: number;
}

export interface Transaction {
  _id: string;
  landlord_id: string;
  landlord_email: string;
  type: string;
  tier?: string;
  amount: number;
  currency: string;
  billing_cycle?: string;
  status: string;
  created_at: string;
  completed_at?: string;
}

export interface RevenueReport {
  period: {
    start: string;
    end: string;
  };
  summary: {
    total_revenue: number;
    transaction_count: number;
    average_transaction: number;
  };
  revenue_by_type: Array<{
    _id: string;
    revenue: number;
    count: number;
  }>;
  top_landlords: Array<{
    landlord_id: string;
    email: string;
    total_paid: number;
    transaction_count: number;
  }>;
}

@Injectable({
  providedIn: 'root'
})
export class FinancialService {
  private API_URL = `${environment.apiUrl}/financial`;

  constructor(private http: HttpClient) {}

  getFinancialOverview(days: number = 30): Observable<FinancialOverview> {
    return this.http.get<FinancialOverview>(`${this.API_URL}/overview`, {
      params: { days: days.toString() }
    });
  }

  getSubscriptionAnalytics(): Observable<SubscriptionAnalytics> {
    return this.http.get<SubscriptionAnalytics>(`${this.API_URL}/subscriptions/analytics`);
  }

  getAllTransactions(params?: any): Observable<any> {
    return this.http.get(`${this.API_URL}/transactions`, { params });
  }

  getRevenueReport(startDate?: string, endDate?: string): Observable<RevenueReport> {
    const params: any = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    return this.http.get<RevenueReport>(`${this.API_URL}/report`, { params });
  }

  exportToCSV(data: any[], filename: string): void {
    const csv = this.convertToCSV(data);
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${filename}_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    window.URL.revokeObjectURL(url);
  }

  private convertToCSV(data: any[]): string {
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