import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment.development';

/**
 * Aggregated statistics shown on the admin dashboard.
 * Mirrors the shape returned by GET /admin/dashboard/stats.
 */
export interface DashboardStats {
  users: {
    total: number;                                    // Total registered users
    by_role: Array<{_id: string; count: number}>;     // User counts grouped by role (_id = role name)
    recent_30_days: number;                           // New users in the last 30 days
  };
  properties: {
    total: number;                                    // Total property listings
    by_status: Array<{_id: string; count: number}>;   // Counts grouped by listing status
    by_moderation: Array<{_id: string; count: number}>; // Counts grouped by moderation status
    pending_review: number;                           // Listings awaiting moderation
    avg_moderation_score: number;                     // Mean automated moderation score
  };
  bookings: {
    total: number;                                    // Total bookings
    by_status: Array<{_id: string; count: number}>;   // Counts grouped by booking status
    recent_30_days: number;                           // Bookings created in the last 30 days
  };
  notifications: {
    total: number;                                    // Total notifications
    unread: number;                                   // Unread notifications
  };
  system: {
    status: string;                                   // Health indicator (e.g. "ok")
    timestamp: string;                                // ISO timestamp of the snapshot
  };
}

/**
 * A user record as returned by the admin user-management endpoints.
 * Optional fields are only present on certain responses (e.g. detail views).
 */
export interface User {
  _id: string;
  email: string;
  role: string;
  created_at?: string;        // ISO creation date
  is_suspended?: boolean;     // True if the account is currently suspended
  properties_count?: number;  // Number of listings owned by this user
  bookings_count?: number;    // Number of bookings made by this user
}

/**
 * A property listing as seen in the moderation queue,
 * including automated moderation metadata and landlord contact info.
 */
export interface ModerationProperty {
  _id: string;
  title: string;
  description: string;
  price: number;
  city: string;
  status: string;               // Listing status (e.g. active, draft)
  moderation_status: string;    // Moderation state (e.g. pending, approved, rejected)
  moderation_score: number;     // Automated risk/quality score
  moderation_issues: string[];  // List of flagged issues detected automatically
  images: string[];             // Image URLs for the listing
  landlord_info: {
    email: string;
    user_id: string;
  };
  created_at: string;           // ISO creation date
}

/**
 * Service for all admin-panel API calls (dashboard, user management,
 * property moderation, and analytics). Provided in root, so a single
 * instance is shared across the app.
 */
@Injectable({
  providedIn: 'root'
})
export class AdminService {
  // Base URL for all admin endpoints, built from the environment config.
  private API_URL = `${environment.apiUrl}/admin`;

  constructor(private http: HttpClient) {}

  // Dashboard

  /** Fetch aggregated dashboard statistics. */
  getDashboardStats(): Observable<DashboardStats> {
    return this.http.get<DashboardStats>(`${this.API_URL}/dashboard/stats`);
  }

  /** Fetch the recent activity feed for the dashboard. */
  getRecentActivity(): Observable<any> {
    return this.http.get(`${this.API_URL}/dashboard/recent-activity`);
  }

  // User Management

  /**
   * List users, optionally filtered/paginated.
   * @param params Query params (e.g. page, limit, role, search).
   */
  getAllUsers(params?: any): Observable<any> {
    return this.http.get(`${this.API_URL}/users`, { params });
  }

  /** Fetch a single user's full details by ID. */
  getUserDetails(userId: string): Observable<User> {
    return this.http.get<User>(`${this.API_URL}/users/${userId}`);
  }

  /**
   * Suspend a user account.
   * @param reason Explanation recorded with the suspension.
   */
  suspendUser(userId: string, reason: string): Observable<any> {
    return this.http.put(`${this.API_URL}/users/${userId}/suspend`, { reason });
  }

  /** Reactivate a previously suspended user. */
  activateUser(userId: string): Observable<any> {
    return this.http.put(`${this.API_URL}/users/${userId}/activate`, {});
  }

  /** Permanently delete a user account. */
  deleteUser(userId: string): Observable<any> {
    return this.http.delete(`${this.API_URL}/users/${userId}`);
  }

  // Property Moderation

  /**
   * Fetch the queue of properties awaiting moderation.
   * @param params Query params (e.g. page, status filters).
   */
  getModerationQueue(params?: any): Observable<any> {
    return this.http.get(`${this.API_URL}/moderation/queue`, { params });
  }

  /**
   * Approve a property listing.
   * @param notes Optional moderator notes.
   */
  approveProperty(propertyId: string, notes?: string): Observable<any> {
    return this.http.put(`${this.API_URL}/moderation/${propertyId}/approve`, { notes });
  }

  /**
   * Reject a property listing.
   * @param reason Required explanation shown to the landlord.
   */
  rejectProperty(propertyId: string, reason: string): Observable<any> {
    return this.http.put(`${this.API_URL}/moderation/${propertyId}/reject`, { reason });
  }

  // Analytics

  /**
   * Fetch growth analytics over a time window.
   * @param days Number of days to look back (defaults to 30).
   */
  getGrowthAnalytics(days: number = 30): Observable<any> {
    return this.http.get(`${this.API_URL}/analytics/growth`, { params: { days: days.toString() } });
  }
}