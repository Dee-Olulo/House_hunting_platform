import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { BehaviorSubject, Observable, interval } from 'rxjs';
import { tap, switchMap, catchError } from 'rxjs/operators';
import { environment } from '../../environments/environment.development';
import {
  Notification,
  NotificationResponse,
  NotificationStatistics,
  NotificationFilters
} from './notification.interface';

@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  private API_URL = `${environment.apiUrl}/notifications`;
  
  // BehaviorSubject to track unread count in real-time
  private unreadCountSubject = new BehaviorSubject<number>(0);
  public unreadCount$ = this.unreadCountSubject.asObservable();
  
  // BehaviorSubject to track recent notifications
  private notificationsSubject = new BehaviorSubject<Notification[]>([]);
  public notifications$ = this.notificationsSubject.asObservable();
  
  // Polling interval (30 seconds)
  private pollingInterval = 30000;
  private pollingSubscription: any;

  constructor(private http: HttpClient) {}

  // ============================================
  // NOTIFICATION CRUD OPERATIONS
  // ============================================

  /**
   * Get all notifications with optional filters
   */
  getNotifications(filters?: NotificationFilters): Observable<NotificationResponse> {
    let params = new HttpParams();
    
    if (filters) {
      if (filters.is_read !== undefined) params = params.set('is_read', filters.is_read.toString());
      if (filters.type) params = params.set('type', filters.type);
      if (filters.page) params = params.set('page', filters.page.toString());
      if (filters.per_page) params = params.set('per_page', filters.per_page.toString());
    }

    return this.http.get<NotificationResponse>(`${this.API_URL}/`, { params });
  }

  /**
   * Get unread notification count
   */
  getUnreadCount(): Observable<{ unread_count: number }> {
    return this.http.get<{ unread_count: number }>(`${this.API_URL}/unread-count`).pipe(
      tap(response => this.unreadCountSubject.next(response.unread_count))
    );
  }

  /**
   * Mark notification as read
   */
  markAsRead(notificationId: string): Observable<{ message: string }> {
    return this.http.put<{ message: string }>(
      `${this.API_URL}/${notificationId}/read`,
      {}
    ).pipe(
      tap(() => this.refreshUnreadCount())
    );
  }

  /**
   * Mark all notifications as read
   */
  markAllAsRead(): Observable<{ message: string }> {
    return this.http.put<{ message: string }>(`${this.API_URL}/read-all`, {}).pipe(
      tap(() => {
        this.unreadCountSubject.next(0);
        this.refreshNotifications();
      })
    );
  }

  /**
   * Delete a notification
   */
  deleteNotification(notificationId: string): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(`${this.API_URL}/${notificationId}`).pipe(
      tap(() => this.refreshNotifications())
    );
  }

  /**
   * Delete all notifications
   */
  deleteAllNotifications(): Observable<{ message: string; deleted_count: number }> {
    return this.http.delete<{ message: string; deleted_count: number }>(`${this.API_URL}/delete-all`).pipe(
      tap(() => {
        this.unreadCountSubject.next(0);
        this.notificationsSubject.next([]);
      })
    );
  }

  /**
   * Get notification statistics
   */
  getStatistics(): Observable<NotificationStatistics> {
    return this.http.get<NotificationStatistics>(`${this.API_URL}/statistics`);
  }

  // ============================================
  // REAL-TIME UPDATES
  // ============================================

  /**
   * Start polling for new notifications
   */
  startPolling(): void {
    if (this.pollingSubscription) {
      return; // Already polling
    }

    // Initial fetch
    this.refreshUnreadCount();
    this.refreshNotifications();

    // Poll every 30 seconds
    this.pollingSubscription = interval(this.pollingInterval)
      .pipe(
        switchMap(() => this.getUnreadCount()),
        catchError(error => {
          console.error('Polling error:', error);
          return [];
        })
      )
      .subscribe();
  }

  /**
   * Stop polling
   */
  stopPolling(): void {
    if (this.pollingSubscription) {
      this.pollingSubscription.unsubscribe();
      this.pollingSubscription = null;
    }
  }

  /**
   * Refresh unread count
   */
  refreshUnreadCount(): void {
    this.getUnreadCount().subscribe();
  }

  /**
   * Refresh recent notifications (last 10)
   */
  refreshNotifications(): void {
    this.getNotifications({ page: 1, per_page: 10 }).subscribe(
      response => this.notificationsSubject.next(response.notifications)
    );
  }

  // ============================================
  // HELPER METHODS
  // ============================================

  /**
   * Get icon for notification type
   */
  getNotificationIcon(type: string): string {
    const icons: { [key: string]: string } = {
      'booking_confirmed': '✅',
      'booking_rejected': '❌',
      'booking_cancelled': '🚫',
      'new_booking': '🔔',
      'booking_reminder': '⏰',
      'property_expiring': '⚠️',
      'welcome': '🎉'
    };
    return icons[type] || '📬';
  }

  /**
   * Get color class for notification type
   */
  getNotificationColor(type: string): string {
    const colors: { [key: string]: string } = {
      'booking_confirmed': 'notification-success',
      'booking_rejected': 'notification-danger',
      'booking_cancelled': 'notification-warning',
      'new_booking': 'notification-info',
      'booking_reminder': 'notification-warning',
      'property_expiring': 'notification-warning',
      'welcome': 'notification-success'
    };
    return colors[type] || 'notification-default';
  }

  /**
   * Format relative time
   */
  getRelativeTime(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)} days ago`;
    
    return date.toLocaleDateString();
  }

  /**
   * Format notification date
   */
  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  /**
   * Get current unread count value
   */
  getCurrentUnreadCount(): number {
    return this.unreadCountSubject.value;
  }

  /**
   * Get current notifications value
   */
  getCurrentNotifications(): Notification[] {
    return this.notificationsSubject.value;
  }
}