// src/app/admin/financial-dashboard/financial-dashboard.component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import {
  FinancialService,
  FinancialOverview,
  SubscriptionAnalytics,
  Transaction,
  RevenueReport
} from '../../services/financial.service';

@Component({
  selector: 'app-financial-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './financial-dashboard.html',
  styleUrls: ['./financial-dashboard.css']
})
export class FinancialDashboardComponent implements OnInit {
  isLoading = true;
  errorMessage = '';
  successMessage = '';

  // Data
  financialOverview: FinancialOverview | null = null;
  subscriptionAnalytics: SubscriptionAnalytics | null = null;
  transactions: Transaction[] = [];
  revenueReport: RevenueReport | null = null;

  // Filters
  selectedPeriod = 30;
  transactionType = '';
  transactionStatus = '';
  currentPage = 1;
  perPage = 20;
  totalTransactions = 0;
  totalPages = 0;

  // Active tab
  activeTab: 'overview' | 'subscriptions' | 'transactions' | 'reports' = 'overview';

  // Date range for reports
  reportStartDate = '';
  reportEndDate = '';

  constructor(
    private financialService: FinancialService,
    public router: Router
  ) {}

  ngOnInit(): void {
    this.loadFinancialData();
  }

  loadFinancialData(): void {
    this.isLoading = true;
    this.errorMessage = '';

    // Load financial overview
    this.financialService.getFinancialOverview(this.selectedPeriod).subscribe({
      next: (data) => {
        this.financialOverview = data;
      },
      error: (error) => {
        this.errorMessage = 'Failed to load financial overview';
        console.error('Error:', error);
      }
    });

    // Load subscription analytics
    this.financialService.getSubscriptionAnalytics().subscribe({
      next: (data) => {
        this.subscriptionAnalytics = data;
      },
      error: (error) => console.error('Error loading subscription analytics:', error)
    });

    // Load transactions
    this.loadTransactions();
  }

  loadTransactions(): void {
    const params: any = {
      page: this.currentPage,
      per_page: this.perPage
    };

    if (this.transactionType) params.type = this.transactionType;
    if (this.transactionStatus) params.status = this.transactionStatus;

    this.financialService.getAllTransactions(params).subscribe({
      next: (response) => {
        this.transactions = response.transactions;
        this.totalTransactions = response.total;
        this.totalPages = response.total_pages;
        this.isLoading = false;
      },
      error: (error) => {
        this.errorMessage = 'Failed to load transactions';
        this.isLoading = false;
        console.error('Error:', error);
      }
    });
  }

  onPeriodChange(): void {
    this.loadFinancialData();
  }

  onFilterChange(): void {
    this.currentPage = 1;
    this.loadTransactions();
  }

  setActiveTab(tab: typeof this.activeTab): void {
    this.activeTab = tab;
    
    if (tab === 'reports' && !this.revenueReport) {
      this.generateReport();
    }
  }

  generateReport(): void {
    this.financialService.getRevenueReport(
      this.reportStartDate,
      this.reportEndDate
    ).subscribe({
      next: (data) => {
        this.revenueReport = data;
        this.successMessage = 'Report generated successfully';
        setTimeout(() => this.successMessage = '', 3000);
      },
      error: (error) => {
        this.errorMessage = 'Failed to generate report';
        console.error('Error:', error);
      }
    });
  }

  exportOverview(): void {
    if (!this.financialOverview) return;
    
    const data = [
      {
        metric: 'Total Revenue',
        value: this.financialOverview.summary.total_revenue,
        period: `${this.selectedPeriod} days`
      },
      {
        metric: 'Subscription Revenue',
        value: this.financialOverview.summary.subscription_revenue,
        period: `${this.selectedPeriod} days`
      },
      {
        metric: 'Commission Revenue',
        value: this.financialOverview.summary.commission_revenue,
        period: `${this.selectedPeriod} days`
      },
      {
        metric: 'Monthly Recurring Revenue (MRR)',
        value: this.financialOverview.summary.mrr,
        period: 'Current'
      }
    ];

    this.financialService.exportToCSV(data, 'financial_overview');
  }

  exportTransactions(): void {
    const exportData = this.transactions.map(t => ({
      transaction_id: t._id,
      landlord_email: t.landlord_email,
      type: t.type,
      tier: t.tier || 'N/A',
      amount: t.amount,
      currency: t.currency,
      status: t.status,
      created_at: t.created_at,
      completed_at: t.completed_at || 'N/A'
    }));

    this.financialService.exportToCSV(exportData, 'transactions');
  }

  exportReport(): void {
    if (!this.revenueReport) return;

    this.financialService.exportToCSV(
      this.revenueReport.top_landlords,
      'revenue_report'
    );
  }

  nextPage(): void {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
      this.loadTransactions();
    }
  }

  previousPage(): void {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.loadTransactions();
    }
  }

  formatCurrency(amount: number): string {
    return new Intl.NumberFormat('en-KE', {
      style: 'currency',
      currency: 'KES'
    }).format(amount);
  }

  getGrowthClass(growth: number): string {
    if (growth > 0) return 'positive';
    if (growth < 0) return 'negative';
    return 'neutral';
  }

  getTierCount(tier: string): number {
    if (!this.subscriptionAnalytics) return 0;
    const tierData = this.subscriptionAnalytics.tier_distribution.find(t => t._id === tier);
    return tierData ? tierData.count : 0;
  }

  getStatusBadgeClass(status: string): string {
    const classes: { [key: string]: string } = {
      'completed': 'badge-success',
      'pending': 'badge-warning',
      'failed': 'badge-danger'
    };
    return classes[status] || 'badge-default';
  }

  getTypeBadgeClass(type: string): string {
    const classes: { [key: string]: string } = {
      'subscription': 'badge-subscription',
      'commission': 'badge-commission'
    };
    return classes[type] || 'badge-default';
  }

  getMaxRevenue(data: Array<{revenue?: number; estimated_revenue?: number}>): number {
    const revenues = data.map(d => d.revenue || d.estimated_revenue || 0);
    return Math.max(...revenues, 1);
  }

  getBarWidth(value: number, max: number): number {
    return (value / max) * 100;
  }

  setDefaultDates(): void {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 30);
    
    this.reportEndDate = end.toISOString().split('T')[0];
    this.reportStartDate = start.toISOString().split('T')[0];
  }
}