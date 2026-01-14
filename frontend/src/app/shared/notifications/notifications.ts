import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { NotificationService } from '../../services/notification.service';
import { Notification, NotificationStatistics } from '../../services/notification.interface';

@Component({
  selector: 'app-notifications',
  standalone: true,
  imports: [CommonModule, FormsModule,],
  templateUrl: './notifications.html',
  styleUrls: ['./notifications.css']
})
export class NotificationsComponent implements OnInit {
  notifications: Notification[] = [];
  statistics: NotificationStatistics | null = null;
  isLoading = false;
  errorMessage = '';
  successMessage = '';

  // Filters
  filterReadStatus: string = 'all'; // all, unread, read
  filterType: string = '';
  
  // Pagination
  currentPage = 1;
  totalPages = 1;
  perPage = 20;
  totalNotifications = 0;

  // Selection
  selectedNotifications: Set<string> = new Set();
  selectAll = false;

  constructor(
    private notificationService: NotificationService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadNotifications();
    this.loadStatistics();
  }

  loadNotifications(): void {
    this.isLoading = true;
    this.errorMessage = '';

    const filters: any = {
      page: this.currentPage,
      per_page: this.perPage
    };

    if (this.filterReadStatus === 'unread') {
      filters.is_read = false;
    } else if (this.filterReadStatus === 'read') {
      filters.is_read = true;
    }

    if (this.filterType) {
      filters.type = this.filterType;
    }

    this.notificationService.getNotifications(filters).subscribe({
      next: (response) => {
        this.notifications = response.notifications;
        this.totalNotifications = response.total;
        this.totalPages = response.total_pages;
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading notifications:', error);
        this.errorMessage = 'Failed to load notifications';
        this.isLoading = false;
      }
    });
  }

  loadStatistics(): void {
    this.notificationService.getStatistics().subscribe({
      next: (stats) => {
        this.statistics = stats;
      },
      error: (error) => {
        console.error('Error loading statistics:', error);
      }
    });
  }

  applyFilters(): void {
    this.currentPage = 1;
    this.selectedNotifications.clear();
    this.selectAll = false;
    this.loadNotifications();
  }

  clearFilters(): void {
    this.filterReadStatus = 'all';
    this.filterType = '';
    this.currentPage = 1;
    this.loadNotifications();
  }

  handleNotificationClick(notification: Notification): void {
    // Mark as read if unread
    if (!notification.is_read) {
      this.notificationService.markAsRead(notification._id).subscribe({
        next: () => {
          notification.is_read = true;
          this.loadStatistics();
        }
      });
    }

    // Navigate to link if provided
    if (notification.link) {
      this.router.navigate([notification.link]);
    }
  }

  markAsRead(notificationId: string, event: Event): void {
    event.stopPropagation();
    
    this.notificationService.markAsRead(notificationId).subscribe({
      next: () => {
        const notification = this.notifications.find(n => n._id === notificationId);
        if (notification) {
          notification.is_read = true;
        }
        this.loadStatistics();
        this.showSuccess('Notification marked as read');
      },
      error: (error) => {
        this.showError('Failed to mark as read');
      }
    });
  }

  markAllAsRead(): void {
    if (confirm('Mark all notifications as read?')) {
      this.notificationService.markAllAsRead().subscribe({
        next: () => {
          this.loadNotifications();
          this.loadStatistics();
          this.showSuccess('All notifications marked as read');
        },
        error: (error) => {
          this.showError('Failed to mark all as read');
        }
      });
    }
  }

  deleteNotification(notificationId: string, event: Event): void {
    event.stopPropagation();
    
    if (confirm('Delete this notification?')) {
      this.notificationService.deleteNotification(notificationId).subscribe({
        next: () => {
          this.loadNotifications();
          this.loadStatistics();
          this.showSuccess('Notification deleted');
        },
        error: (error) => {
          this.showError('Failed to delete notification');
        }
      });
    }
  }

  deleteAllNotifications(): void {
    if (confirm('Delete ALL notifications? This action cannot be undone.')) {
      this.notificationService.deleteAllNotifications().subscribe({
        next: (response) => {
          this.loadNotifications();
          this.loadStatistics();
          this.showSuccess(`Deleted ${response.deleted_count} notifications`);
        },
        error: (error) => {
          this.showError('Failed to delete all notifications');
        }
      });
    }
  }

  toggleSelection(notificationId: string): void {
    if (this.selectedNotifications.has(notificationId)) {
      this.selectedNotifications.delete(notificationId);
    } else {
      this.selectedNotifications.add(notificationId);
    }
    this.updateSelectAll();
  }

  toggleSelectAll(): void {
    this.selectAll = !this.selectAll;
    
    if (this.selectAll) {
      this.notifications.forEach(n => this.selectedNotifications.add(n._id));
    } else {
      this.selectedNotifications.clear();
    }
  }

  updateSelectAll(): void {
    this.selectAll = this.notifications.length > 0 && 
                     this.notifications.every(n => this.selectedNotifications.has(n._id));
  }

  deleteSelected(): void {
    if (this.selectedNotifications.size === 0) {
      return;
    }

    if (confirm(`Delete ${this.selectedNotifications.size} selected notifications?`)) {
      const deletePromises = Array.from(this.selectedNotifications).map(id =>
        this.notificationService.deleteNotification(id).toPromise()
      );

      Promise.all(deletePromises).then(() => {
        this.selectedNotifications.clear();
        this.selectAll = false;
        this.loadNotifications();
        this.loadStatistics();
        this.showSuccess('Selected notifications deleted');
      }).catch(() => {
        this.showError('Failed to delete some notifications');
      });
    }
  }

  goToPage(page: number): void {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.loadNotifications();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }

  previousPage(): void {
    this.goToPage(this.currentPage - 1);
  }

  nextPage(): void {
    this.goToPage(this.currentPage + 1);
  }

  getPageNumbers(): number[] {
    const pages: number[] = [];
    const maxVisible = 5;
    let start = Math.max(1, this.currentPage - Math.floor(maxVisible / 2));
    let end = Math.min(this.totalPages, start + maxVisible - 1);

    if (end - start < maxVisible - 1) {
      start = Math.max(1, end - maxVisible + 1);
    }

    for (let i = start; i <= end; i++) {
      pages.push(i);
    }

    return pages;
  }

  getNotificationIcon(type: string): string {
    return this.notificationService.getNotificationIcon(type);
  }

  getNotificationColor(type: string): string {
    return this.notificationService.getNotificationColor(type);
  }

  getRelativeTime(dateString: string): string {
    return this.notificationService.getRelativeTime(dateString);
  }

  formatDate(dateString: string): string {
    return this.notificationService.formatDate(dateString);
  }

  private showSuccess(message: string): void {
    this.successMessage = message;
    setTimeout(() => this.successMessage = '', 3000);
  }

  private showError(message: string): void {
    this.errorMessage = message;
    setTimeout(() => this.errorMessage = '', 3000);
  }

}