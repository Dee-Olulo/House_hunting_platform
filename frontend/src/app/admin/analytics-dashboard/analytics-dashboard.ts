// src/app/admin/analytics-dashboard/analytics-dashboard.ts

// Angular core imports
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';   // Needed for *ngIf, *ngFor, pipes like | number
import { FormsModule } from '@angular/forms';     // Needed for [(ngModel)] two-way binding on the period selector
import { Router } from '@angular/router';          // Enables programmatic navigation between pages

// AuthService lets us check who is logged in and what their role is
import { AuthService } from '../../services/auth';

// AnalyticsService handles all API calls to the backend analytics endpoints.
// Each interface describes the shape of the data returned by those endpoints.
import {
  AnalyticsService,
  AnalyticsSummary,          // Overview totals and growth percentages
  UserEngagement,            // User counts, roles, daily signup trend
  PropertyPerformance,       // Property counts, top booked, daily listing trend
  GeographicDistribution,    // Properties and bookings broken down by city and type
  BookingTrends              // Booking counts, statuses, daily booking trend
} from '../../services/analytics.service';

@Component({
  selector: 'app-analytics-dashboard',
  standalone: true,
  // Modules available to the template — CommonModule for directives/pipes, FormsModule for ngModel
  imports: [CommonModule, FormsModule],
  templateUrl: './analytics-dashboard.html',
  styleUrls: ['./analytics-dashboard.css']
})
export class AnalyticsDashboardComponent implements OnInit {

  // Controls the loading spinner — true while any API call is in flight
  isLoading = true;

  // Holds an error message to display in the template if an API call fails
  errorMessage = '';

  // The number of days to analyse — bound to the period dropdown in the template.
  // Defaults to 30 days; changes trigger a full data reload via onPeriodChange()
  selectedPeriod = 30;

  // ─── Data properties ───────────────────────────────────────────────────────
  // Each property is null until its API call resolves successfully.
  // The template uses *ngIf to avoid rendering sections before data arrives.

  summary: AnalyticsSummary | null = null;                  // Overview tab data
  userEngagement: UserEngagement | null = null;              // Users tab data
  propertyPerformance: PropertyPerformance | null = null;    // Properties tab data
  geographicData: GeographicDistribution | null = null;      // Geography tab data
  bookingTrends: BookingTrends | null = null;                // Bookings tab data

  // Tracks which tab is currently visible in the template.
  // The union type restricts it to only the five valid tab names.
  activeTab: 'overview' | 'users' | 'properties' | 'geography' | 'bookings' = 'overview';

  constructor(
    private analyticsService: AnalyticsService,  // Injected service for all analytics API calls
    private authService: AuthService,             // Injected service to read the current user's role
    public router: Router                         // public so the template can also call router directly if needed
  ) {}

  // ─── Smart back navigation ─────────────────────────────────────────────────
  // Instead of always going to /admin/dashboard, we check the user's role first
  // so non-admin users land on their own correct home screen.
  goBack(): void {
    const role = this.authService.getUserRole(); // Returns 'admin' | 'landlord' | 'tenant' | null

    switch (role) {
      case 'admin':
        this.router.navigate(['/admin/dashboard']);
        break;
      case 'landlord':
        this.router.navigate(['/landlord/properties']);
        break;
      case 'tenant':
        this.router.navigate(['/tenant/dashboard']);
        break;
      default:
        // Unauthenticated or unknown role — fall back to the previous browser history entry
        window.history.back();
    }
  }

  // ─── Lifecycle hook ────────────────────────────────────────────────────────
  // Called once by Angular after the component is created.
  // Kicks off the initial data load.
  ngOnInit(): void {
    this.loadAnalytics();
  }

  // ─── Data loading ──────────────────────────────────────────────────────────
  // Fires all five API calls in parallel (not sequentially), so all sections
  // load as fast as possible. isLoading is only set to false after the last
  // call (booking trends) completes, since it acts as a proxy for "all done".
  loadAnalytics(): void {
    this.isLoading = true;
    this.errorMessage = '';

    // 1. Overview cards — all-time totals and growth vs the previous period
    this.analyticsService.getSummary(this.selectedPeriod).subscribe({
      next: (data) => { this.summary = data; },
      error: (error) => {
        this.errorMessage = 'Failed to load analytics summary';
        console.error('Error:', error);
      }
    });

    // 2. Users tab — total, new, and active users; breakdown by role; daily trend
    this.analyticsService.getUserEngagement(this.selectedPeriod).subscribe({
      next: (data) => { this.userEngagement = data; },
      error: (error) => console.error('Error loading user engagement:', error)
    });

    // 3. Properties tab — totals, top 10 most booked, average price, daily trend
    this.analyticsService.getPropertyPerformance(this.selectedPeriod).subscribe({
      next: (data) => { this.propertyPerformance = data; },
      error: (error) => console.error('Error loading property performance:', error)
    });

    // 4. Geography tab — properties by city, popular cities by bookings, properties by type.
    //    No period parameter — geographic data is always shown in full.
    this.analyticsService.getGeographicDistribution().subscribe({
      next: (data) => { this.geographicData = data; },
      error: (error) => console.error('Error loading geographic data:', error)
    });

    // 5. Bookings tab — totals, status breakdown, daily trend.
    //    This is the last call so we toggle isLoading here regardless of outcome.
    this.analyticsService.getBookingTrends(this.selectedPeriod).subscribe({
      next: (data) => {
        this.bookingTrends = data;
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading booking trends:', error);
        this.isLoading = false;
      }
    });
  }

  // Triggered when the user changes the period dropdown.
  // Re-runs all API calls with the newly selected number of days.
  onPeriodChange(): void {
    this.loadAnalytics();
  }

  // Updates which tab content is shown in the template.
  setActiveTab(tab: typeof this.activeTab): void {
    this.activeTab = tab;
  }

  // ─── Export helpers ────────────────────────────────────────────────────────
  // Each method passes a specific data array to the service, which converts
  // it to CSV/Excel and triggers a browser file download.

  exportToPDF(): void {
    this.analyticsService.exportToPDF();
  }

  exportUserData(): void {
    if (this.userEngagement) {
      // Exports the daily signup trend rows as a CSV
      this.analyticsService.exportToExcel(this.userEngagement.daily_trend, 'user_engagement');
    }
  }

  exportPropertyData(): void {
    if (this.propertyPerformance) {
      // Exports the top 10 most-booked properties table as a CSV
      this.analyticsService.exportToExcel(this.propertyPerformance.most_booked, 'property_performance');
    }
  }

  exportGeographicData(): void {
    if (this.geographicData) {
      // Exports the properties-by-city breakdown as a CSV
      this.analyticsService.exportToExcel(this.geographicData.properties_by_city, 'geographic_distribution');
    }
  }

  exportBookingData(): void {
    if (this.bookingTrends) {
      // Exports the daily booking trend rows as a CSV
      this.analyticsService.exportToExcel(this.bookingTrends.daily_trend, 'booking_trends');
    }
  }

  // ─── Template utility methods ──────────────────────────────────────────────
  // These are called directly from the HTML template to drive conditional
  // styling and dynamic values. Logic is kept here to avoid cluttering the template.

  // Returns a CSS class name used to colour growth figures green, red, or grey
  getGrowthClass(growth: number): string {
    if (growth > 0) return 'positive';
    if (growth < 0) return 'negative';
    return 'neutral';
  }

  // Returns a plain text arrow indicating the direction of growth.
  // Used in the overview cards next to the percentage figure.
  getGrowthIcon(growth: number): string {
    if (growth > 0) return '(+)';
    if (growth < 0) return '(-)';
    return '(=)';
  }

  // Finds how many users have a specific role (e.g. 'tenant', 'landlord', 'admin')
  // by searching the users_by_role array returned from the API.
  getRoleCount(role: string): number {
    if (!this.userEngagement) return 0;
    const roleData = this.userEngagement.users_by_role.find(r => r._id === role);
    return roleData ? roleData.count : 0;
  }

  // Finds the count for a specific booking status (e.g. 'confirmed', 'pending')
  // within a status breakdown array returned from the API.
  getStatusCount(statusArray: Array<{_id: string; count: number}>, status: string): number {
    const statusData = statusArray.find(s => s._id === status);
    return statusData ? statusData.count : 0;
  }

  // Returns the highest count value in a trend array.
  // Used as the denominator when calculating bar heights so the tallest bar = 100%.
  // Falls back to 1 to prevent division by zero on empty data.
  getMaxCount(data: Array<{count: number}>): number {
    return Math.max(...data.map(d => d.count), 1);
  }

  // Converts a raw count into a 0-100 percentage of the max value.
  // Used as the CSS width/height % for bar chart elements in the template.
  getBarWidth(count: number, max: number): number {
    return (count / max) * 100;
  }
}