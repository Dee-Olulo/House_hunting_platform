// src/app/admin/notification-management/notification-management.component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment.development';

interface BroadcastHistory {
  _id: string;
  title: string;
  message: string;
  target_audience: string;
  recipients_count: number;
  sent_at: string;
}

@Component({
  selector: 'app-notification-management',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './notification-management.html',
  styleUrls: ['./notification-management.css']
})
export class NotificationManagementComponent implements OnInit {
  private API_URL = `${environment.apiUrl}/admin/notifications`;

  activeTab: 'broadcast' | 'history' = 'broadcast';

  // Broadcast
  broadcastTitle = '';
  broadcastMessage = '';
  targetAudience = 'all';
  notificationType = 'system_announcement';
  broadcastLink = '';

  // History
  history: BroadcastHistory[] = [];
  currentPage = 1;
  perPage = 20;

  // Stats
  stats: any = null;

  // UI State
  isLoading = false;
  errorMessage = '';
  successMessage = '';

  constructor(
    private http: HttpClient,
    public router: Router
  ) {}

  ngOnInit(): void {
    this.loadStats();
  }

  setActiveTab(tab: typeof this.activeTab): void {
    this.activeTab = tab;
    if (tab === 'history') {
      this.loadHistory();
    }
  }

  // ============================================================================
  // BROADCAST
  // ============================================================================

  sendBroadcast(): void {
    if (!this.broadcastTitle || !this.broadcastMessage) {
      this.showError('Title and message are required');
      return;
    }

    if (!confirm(`Send broadcast to ${this.targetAudience}? This action cannot be undone.`)) {
      return;
    }

    this.isLoading = true;

    const payload = {
      title: this.broadcastTitle,
      message: this.broadcastMessage,
      target_audience: this.targetAudience,
      notification_type: this.notificationType,
      link: this.broadcastLink || null
    };

    this.http.post(`${this.API_URL}/broadcast`, payload).subscribe({
      next: (response: any) => {
        this.showSuccess(`Broadcast sent to ${response.recipients} users`);
        this.clearBroadcastForm();
        this.loadStats();
        this.isLoading = false;
      },
      error: (error) => {
        this.showError(error.error?.error || 'Failed to send broadcast');
        this.isLoading = false;
      }
    });
  }

  clearBroadcastForm(): void {
    this.broadcastTitle = '';
    this.broadcastMessage = '';
    this.broadcastLink = '';
    this.targetAudience = 'all';
    this.notificationType = 'system_announcement';
  }

  // ============================================================================
  // HISTORY
  // ============================================================================

  loadHistory(): void {
    this.http.get<any>(`${this.API_URL}/history`, {
      params: {
        page: this.currentPage.toString(),
        per_page: this.perPage.toString()
      }
    }).subscribe({
      next: (response) => {
        this.history = response.history;
      },
      error: (error) => {
        console.error('Error loading history:', error);
      }
    });
  }

  // ============================================================================
  // STATS
  // ============================================================================

  loadStats(): void {
    this.http.get<any>(`${this.API_URL}/stats`).subscribe({
      next: (response) => {
        this.stats = response;
      },
      error: (error) => {
        console.error('Error loading stats:', error);
      }
    });
  }

  // ============================================================================
  // UTILITIES
  // ============================================================================

  private showSuccess(message: string): void {
    this.successMessage = message;
    setTimeout(() => this.successMessage = '', 3000);
  }

  private showError(message: string): void {
    this.errorMessage = message;
    setTimeout(() => this.errorMessage = '', 3000);
  }

  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleString();
  }
}