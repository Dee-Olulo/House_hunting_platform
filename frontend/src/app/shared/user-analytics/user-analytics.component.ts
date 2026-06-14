// src/app/shared/user-analytics/user-analytics.component.ts
 
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { environment } from '../../../environments/environment';
 
// ── Interfaces ──────────────────────────────────────────────────────────────
 
export interface LandlordDashboard {
  total_properties: number;
  active_properties: number;
  new_properties: number;
  total_bookings: number;
  period_bookings: number;
  confirmed_bookings: number;
  pending_bookings: number;
  conversion_rate: number;
  booking_growth: number;
  bookings_by_status: StatusCount[];
  most_booked_properties: MostBookedProperty[];
  daily_trend: DailyPoint[];
  period_days: number;
}
 
export interface TenantDashboard {
  total_bookings: number;
  period_bookings: number;
  confirmed_bookings: number;
  pending_bookings: number;
  booking_growth: number;
  favourites_count: number;
  bookings_by_status: StatusCount[];
  daily_trend: DailyPoint[];
  recent_bookings: RecentBooking[];
  period_days: number;
}
 
interface StatusCount {
  _id: string;
  count: number;
}
 
interface MostBookedProperty {
  property_id: string;
  title: string;
  city: string;
  price: number;
  booking_count: number;
}
 
interface RecentBooking {
  booking_id: string;
  status: string;
  created_at: string;
  property_title: string;
  property_city: string;
  property_price: number;
  property_id: string;
}
 
interface DailyPoint {
  date: string;
  count: number;
}
 
// ── Component ────────────────────────────────────────────────────────────────
 
@Component({
  selector: 'app-user-analytics',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './user-analytics.component.html',
  styleUrls: ['./user-analytics.component.css']
})
export class UserAnalyticsComponent implements OnInit {
  isLoading = true;
  errorMessage = '';
  selectedPeriod = 30;
  userRole = '';
 
  landlordData: LandlordDashboard | null = null;
  tenantData: TenantDashboard | null = null;
 
  // Adjust this if your API URL is stored in environment.ts
  private readonly apiUrl = 'http://localhost:5000/api/analytics';
 
  constructor(
    private http: HttpClient,
    public router: Router
  ) {}
 
  ngOnInit(): void {
    this.resolveRole();
    this.loadDashboard();
  }
 
  // ── Helpers ────────────────────────────────────────────────────────────────
 
  private resolveRole(): void {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      this.userRole = payload.role ?? '';
    } catch {
      this.userRole = '';
    }
  }
 
  private getHeaders(): HttpHeaders {
    const token = localStorage.getItem('access_token') ?? '';
    return new HttpHeaders({ Authorization: `Bearer ${token}` });
  }
 
  // ── Data loading ───────────────────────────────────────────────────────────
 
  loadDashboard(): void {
    this.isLoading = true;
    this.errorMessage = '';
 
    const headers = this.getHeaders();
    const qs = `?days=${this.selectedPeriod}`;
 
    if (this.userRole === 'landlord') {
      this.http
        .get<LandlordDashboard>(`${this.apiUrl}/landlord/dashboard${qs}`, { headers })
        .subscribe({
          next: (data) => {
            this.landlordData = data;
            this.isLoading = false;
          },
          error: () => {
            this.errorMessage = 'Failed to load analytics. Please try again.';
            this.isLoading = false;
          }
        });
    } else if (this.userRole === 'tenant') {
      this.http
        .get<TenantDashboard>(`${this.apiUrl}/tenant/dashboard${qs}`, { headers })
        .subscribe({
          next: (data) => {
            this.tenantData = data;
            this.isLoading = false;
          },
          error: () => {
            this.errorMessage = 'Failed to load analytics. Please try again.';
            this.isLoading = false;
          }
        });
    } else {
      this.errorMessage = 'Analytics not available for your account type.';
      this.isLoading = false;
    }
  }
 
  onPeriodChange(): void {
    this.loadDashboard();
  }
 
  // ── Display utilities ──────────────────────────────────────────────────────
 
  getGrowthClass(growth: number): string {
    if (growth > 0) return 'positive';
    if (growth < 0) return 'negative';
    return 'neutral';
  }
 
  getGrowthIcon(growth: number): string {
    if (growth > 0) return '↑';
    if (growth < 0) return '↓';
    return '→';
  }
 
  getStatusCount(arr: StatusCount[], status: string): number {
    return arr.find(s => s._id === status)?.count ?? 0;
  }
 
  getMaxCount(data: Array<{ count: number }>): number {
    return Math.max(...data.map(d => d.count), 1);
  }
 
  getBarWidth(count: number, max: number): number {
    return Math.round((count / max) * 100);
  }
 
  getStatusBadgeClass(status: string): string {
    switch (status?.toLowerCase()) {
      case 'confirmed':  return 'badge-confirmed';
      case 'pending':    return 'badge-pending';
      case 'cancelled':  return 'badge-cancelled';
      case 'completed':  return 'badge-completed';
      case 'rejected':   return 'badge-cancelled';
      default:           return 'badge-default';
    }
  }
 
  getDotClass(status: string): string {
    return `dot-${status?.toLowerCase() ?? 'default'}`;
  }
 
  navigateBack(): void {
    if (this.userRole === 'landlord') {
      this.router.navigate(['/landlord/properties']);
    } else {
      this.router.navigate(['/tenant/dashboard']);
    }
  }
}