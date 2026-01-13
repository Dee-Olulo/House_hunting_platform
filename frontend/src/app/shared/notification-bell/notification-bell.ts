import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { NotificationService } from '../../services/notification.service';
import { Notification } from '../../services/notification.interface';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-notification-bell',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './notification-bell.html',
  styleUrls: ['./notification-bell.css']
})
export class NotificationBellComponent implements OnInit, OnDestroy {
  unreadCount = 0;
  recentNotifications: Notification[] = [];
  showDropdown = false;
  isLoading = false;

  private subscriptions: Subscription[] = [];

  constructor(
    private notificationService: NotificationService,
    private router: Router
  ) {}

  ngOnInit(): void {
    // Subscribe to unread count
    this.subscriptions.push(
      this.notificationService.unreadCount$.subscribe(
        count => this.unreadCount = count
      )
    );

    // Subscribe to recent notifications
    this.subscriptions.push(
      this.notificationService.notifications$.subscribe(
        notifications => this.recentNotifications = notifications
      )
    );

    // Start polling for updates
    this.notificationService.startPolling();

    // Close dropdown when clicking outside
    document.addEventListener('click', this.handleClickOutside.bind(this));
  }

  ngOnDestroy(): void {
    // Unsubscribe from all subscriptions
    this.subscriptions.forEach(sub => sub.unsubscribe());
    
    // Stop polling
    this.notificationService.stopPolling();

    // Remove click listener
    document.removeEventListener('click', this.handleClickOutside.bind(this));
  }

  toggleDropdown(event: Event): void {
    event.stopPropagation();
    this.showDropdown = !this.showDropdown;

    if (this.showDropdown && this.recentNotifications.length === 0) {
      this.loadRecentNotifications();
    }
  }

  loadRecentNotifications(): void {
    this.isLoading = true;
    this.notificationService.getNotifications({ page: 1, per_page: 5 }).subscribe({
      next: (response) => {
        this.recentNotifications = response.notifications;
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading notifications:', error);
        this.isLoading = false;
      }
    });
  }

  handleNotificationClick(notification: Notification, event: Event): void {
    event.stopPropagation();

    // Mark as read if unread
    if (!notification.is_read) {
      this.notificationService.markAsRead(notification._id).subscribe();
    }

    // Close dropdown
    this.showDropdown = false;

    // Navigate to link if provided
    if (notification.link) {
      this.router.navigate([notification.link]);
    }
  }

  markAllAsRead(): void {
    this.notificationService.markAllAsRead().subscribe({
      next: () => {
        console.log('All notifications marked as read');
      },
      error: (error) => {
        console.error('Error marking all as read:', error);
      }
    });
  }

  viewAllNotifications(event: Event): void {
    event.stopPropagation();
    this.showDropdown = false;
    
    // Get user role from localStorage
    const userRole = localStorage.getItem('userRole') || 'tenant';
    this.router.navigate([`/${userRole}/notifications`]);
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

  private handleClickOutside(event: Event): void {
    const target = event.target as HTMLElement;
    const bellElement = document.querySelector('.notification-bell-container');
    
    if (bellElement && !bellElement.contains(target)) {
      this.showDropdown = false;
    }
  }
}