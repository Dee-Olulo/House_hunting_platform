// src/app/admin/notification-management/notification-management.component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment.development';

interface NotificationTemplate {
  _id?: string;
  name: string;
  title: string;
  message: string;
  notification_type: string;
  variables: string[];
  is_active: boolean;
}

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

  activeTab: 'broadcast' | 'campaign' | 'templates' | 'schedule' | 'history' = 'broadcast';

  // Broadcast
  broadcastTitle = '';
  broadcastMessage = '';
  targetAudience = 'all';
  notificationType = 'system_announcement';
  broadcastLink = '';

  // Campaign
  campaignTitle = '';
  campaignMessage = '';
  campaignRole = 'landlord';
  inactiveDays = 30;
  propertyStatus = 'inactive';

  // Templates
  templates: NotificationTemplate[] = [];
  editingTemplate: NotificationTemplate | null = null;
  showTemplateModal = false;
  templateForm: NotificationTemplate = {
    name: '',
    title: '',
    message: '',
    notification_type: 'welcome',
    variables: [],
    is_active: true
  };

  // Schedule
  scheduleTitle = '';
  scheduleMessage = '';
  scheduleAudience = 'all';
  scheduleDate = '';
  scheduleTime = '';
  scheduledNotifications: any[] = [];

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
    this.loadTemplates();
  }

  setActiveTab(tab: typeof this.activeTab): void {
    this.activeTab = tab;
    
    if (tab === 'schedule') {
      this.loadScheduledNotifications();
    } else if (tab === 'history') {
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
  // CAMPAIGN
  // ============================================================================

  sendCampaign(): void {
    if (!this.campaignTitle || !this.campaignMessage) {
      this.showError('Title and message are required');
      return;
    }

    if (!confirm('Send targeted campaign? This will send to users matching the criteria.')) {
      return;
    }

    this.isLoading = true;

    const payload = {
      title: this.campaignTitle,
      message: this.campaignMessage,
      criteria: {
        role: this.campaignRole,
        inactive_days: this.inactiveDays,
        property_status: this.propertyStatus
      }
    };

    this.http.post(`${this.API_URL}/campaign`, payload).subscribe({
      next: (response: any) => {
        this.showSuccess(`Campaign sent to ${response.recipients} users`);
        this.clearCampaignForm();
        this.loadStats();
        this.isLoading = false;
      },
      error: (error) => {
        this.showError(error.error?.error || 'Failed to send campaign');
        this.isLoading = false;
      }
    });
  }

  clearCampaignForm(): void {
    this.campaignTitle = '';
    this.campaignMessage = '';
    this.campaignRole = 'landlord';
    this.inactiveDays = 30;
    this.propertyStatus = 'inactive';
  }

  // ============================================================================
  // TEMPLATES
  // ============================================================================

  loadTemplates(): void {
    this.http.get<any>(`${this.API_URL}/templates`).subscribe({
      next: (response) => {
        this.templates = response.templates;
      },
      error: (error) => {
        console.error('Error loading templates:', error);
      }
    });
  }

  openTemplateModal(template?: NotificationTemplate): void {
    if (template) {
      this.editingTemplate = template;
      this.templateForm = { ...template };
    } else {
      this.editingTemplate = null;
      this.templateForm = {
        name: '',
        title: '',
        message: '',
        notification_type: 'welcome',
        variables: [],
        is_active: true
      };
    }
    this.showTemplateModal = true;
  }

  closeTemplateModal(): void {
    this.showTemplateModal = false;
    this.editingTemplate = null;
  }

  saveTemplate(): void {
    if (!this.templateForm.name || !this.templateForm.title || !this.templateForm.message) {
      this.showError('All fields are required');
      return;
    }

    const request = this.editingTemplate
      ? this.http.put(`${this.API_URL}/templates/${this.editingTemplate._id}`, this.templateForm)
      : this.http.post(`${this.API_URL}/templates`, this.templateForm);

    request.subscribe({
      next: () => {
        this.showSuccess(`Template ${this.editingTemplate ? 'updated' : 'created'} successfully`);
        this.closeTemplateModal();
        this.loadTemplates();
      },
      error: (error) => {
        this.showError(error.error?.error || 'Failed to save template');
      }
    });
  }

  deleteTemplate(templateId: string): void {
    if (!confirm('Delete this template?')) return;

    this.http.delete(`${this.API_URL}/templates/${templateId}`).subscribe({
      next: () => {
        this.showSuccess('Template deleted successfully');
        this.loadTemplates();
      },
      error: (error) => {
        this.showError('Failed to delete template');
      }
    });
  }

  // ============================================================================
  // SCHEDULE
  // ============================================================================

  scheduleNotification(): void {
    if (!this.scheduleTitle || !this.scheduleMessage || !this.scheduleDate || !this.scheduleTime) {
      this.showError('All fields are required');
      return;
    }

    const scheduledFor = `${this.scheduleDate}T${this.scheduleTime}:00`;

    const payload = {
      title: this.scheduleTitle,
      message: this.scheduleMessage,
      target_audience: this.scheduleAudience,
      scheduled_for: scheduledFor
    };

    this.http.post(`${this.API_URL}/schedule`, payload).subscribe({
      next: (response: any) => {
        this.showSuccess('Notification scheduled successfully');
        this.clearScheduleForm();
        this.loadScheduledNotifications();
      },
      error: (error) => {
        this.showError(error.error?.error || 'Failed to schedule notification');
      }
    });
  }

  loadScheduledNotifications(): void {
    this.http.get<any>(`${this.API_URL}/schedule`).subscribe({
      next: (response) => {
        this.scheduledNotifications = response.scheduled_notifications;
      },
      error: (error) => {
        console.error('Error loading scheduled notifications:', error);
      }
    });
  }

  cancelScheduled(scheduleId: string): void {
    if (!confirm('Cancel this scheduled notification?')) return;

    this.http.delete(`${this.API_URL}/schedule/${scheduleId}`).subscribe({
      next: () => {
        this.showSuccess('Scheduled notification cancelled');
        this.loadScheduledNotifications();
      },
      error: (error) => {
        this.showError('Failed to cancel notification');
      }
    });
  }

  clearScheduleForm(): void {
    this.scheduleTitle = '';
    this.scheduleMessage = '';
    this.scheduleAudience = 'all';
    this.scheduleDate = '';
    this.scheduleTime = '';
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