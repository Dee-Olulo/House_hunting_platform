// src/app/admin/analytics-dashboard/analytics-dashboard.component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import {
  AnalyticsService,
  AnalyticsSummary,
  UserEngagement,
  PropertyPerformance,
  GeographicDistribution,
  BookingTrends
} from '../../services/analytics.service';

@Component({
  selector: 'app-analytics-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './analytics-dashboard.html',
  styleUrls: ['./analytics-dashboard.css']
})
export class AnalyticsDashboardComponent implements OnInit {
  isLoading = true;
  errorMessage = '';
  selectedPeriod = 30;

  // Data
  summary: AnalyticsSummary | null = null;
  userEngagement: UserEngagement | null = null;
  propertyPerformance: PropertyPerformance | null = null;
  geographicData: GeographicDistribution | null = null;
  bookingTrends: BookingTrends | null = null;

  // Active tab
  activeTab: 'overview' | 'users' | 'properties' | 'geography' | 'bookings' = 'overview';

  constructor(
    private analyticsService: AnalyticsService,
    public router: Router
  ) {}

  ngOnInit(): void {
    this.loadAnalytics();
  }

  loadAnalytics(): void {
    this.isLoading = true;
    this.errorMessage = '';

    // Load summary
    this.analyticsService.getSummary(this.selectedPeriod).subscribe({
      next: (data) => {
        this.summary = data;
      },
      error: (error) => {
        this.errorMessage = 'Failed to load analytics summary';
        console.error('Error:', error);
      }
    });

    // Load user engagement
    this.analyticsService.getUserEngagement(this.selectedPeriod).subscribe({
      next: (data) => {
        this.userEngagement = data;
      },
      error: (error) => console.error('Error loading user engagement:', error)
    });

    // Load property performance
    this.analyticsService.getPropertyPerformance(this.selectedPeriod).subscribe({
      next: (data) => {
        this.propertyPerformance = data;
      },
      error: (error) => console.error('Error loading property performance:', error)
    });

    // Load geographic data
    this.analyticsService.getGeographicDistribution().subscribe({
      next: (data) => {
        this.geographicData = data;
      },
      error: (error) => console.error('Error loading geographic data:', error)
    });

    // Load booking trends
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

  onPeriodChange(): void {
    this.loadAnalytics();
  }

  setActiveTab(tab: typeof this.activeTab): void {
    this.activeTab = tab;
  }

  exportToPDF(): void {
    this.analyticsService.exportToPDF();
  }

  exportUserData(): void {
    if (this.userEngagement) {
      this.analyticsService.exportToExcel(
        this.userEngagement.daily_trend,
        'user_engagement'
      );
    }
  }

  exportPropertyData(): void {
    if (this.propertyPerformance) {
      this.analyticsService.exportToExcel(
        this.propertyPerformance.most_booked,
        'property_performance'
      );
    }
  }

  exportGeographicData(): void {
    if (this.geographicData) {
      this.analyticsService.exportToExcel(
        this.geographicData.properties_by_city,
        'geographic_distribution'
      );
    }
  }

  exportBookingData(): void {
    if (this.bookingTrends) {
      this.analyticsService.exportToExcel(
        this.bookingTrends.daily_trend,
        'booking_trends'
      );
    }
  }

  getGrowthClass(growth: number): string {
    if (growth > 0) return 'positive';
    if (growth < 0) return 'negative';
    return 'neutral';
  }

  getGrowthIcon(growth: number): string {
    if (growth > 0) return '📈';
    if (growth < 0) return '📉';
    return '➡️';
  }

  getRoleCount(role: string): number {
    if (!this.userEngagement) return 0;
    const roleData = this.userEngagement.users_by_role.find(r => r._id === role);
    return roleData ? roleData.count : 0;
  }

  getStatusCount(statusArray: Array<{_id: string; count: number}>, status: string): number {
    const statusData = statusArray.find(s => s._id === status);
    return statusData ? statusData.count : 0;
  }

  getMaxCount(data: Array<{count: number}>): number {
    return Math.max(...data.map(d => d.count), 1);
  }

  getBarWidth(count: number, max: number): number {
    return (count / max) * 100;
  }
}