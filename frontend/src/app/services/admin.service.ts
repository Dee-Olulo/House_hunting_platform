import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment.development';

export interface DashboardStats {
  users: {
    total: number;
    by_role: Array<{_id: string; count: number}>;
    recent_30_days: number;
  };
  properties: {
    total: number;
    by_status: Array<{_id: string; count: number}>;
    by_moderation: Array<{_id: string; count: number}>;
    pending_review: number;
    avg_moderation_score: number;
  };
  bookings: {
    total: number;
    by_status: Array<{_id: string; count: number}>;
    recent_30_days: number;
  };
  notifications: {
    total: number;
    unread: number;
  };
  system: {
    status: string;
    timestamp: string;
  };
}

export interface User {
  _id: string;
  email: string;
  role: string;
  created_at?: string;
  is_suspended?: boolean;
  properties_count?: number;
  bookings_count?: number;
}

export interface ModerationProperty {
  _id: string;
  title: string;
  description: string;
  price: number;
  city: string;
  status: string;
  moderation_status: string;
  moderation_score: number;
  moderation_issues: string[];
  images: string[];
  landlord_info: {
    email: string;
    user_id: string;
  };
  created_at: string;
}

@Injectable({
  providedIn: 'root'
})
export class AdminService {
  private API_URL = `${environment.apiUrl}/admin`;

  constructor(private http: HttpClient) {}

  // Dashboard
  getDashboardStats(): Observable<DashboardStats> {
    return this.http.get<DashboardStats>(`${this.API_URL}/dashboard/stats`);
  }

  getRecentActivity(): Observable<any> {
    return this.http.get(`${this.API_URL}/dashboard/recent-activity`);
  }

  // User Management
  getAllUsers(params?: any): Observable<any> {
    return this.http.get(`${this.API_URL}/users`, { params });
  }

  getUserDetails(userId: string): Observable<User> {
    return this.http.get<User>(`${this.API_URL}/users/${userId}`);
  }

  suspendUser(userId: string, reason: string): Observable<any> {
    return this.http.put(`${this.API_URL}/users/${userId}/suspend`, { reason });
  }

  activateUser(userId: string): Observable<any> {
    return this.http.put(`${this.API_URL}/users/${userId}/activate`, {});
  }

  deleteUser(userId: string): Observable<any> {
    return this.http.delete(`${this.API_URL}/users/${userId}`);
  }

  // Property Moderation
  getModerationQueue(params?: any): Observable<any> {
    return this.http.get(`${this.API_URL}/moderation/queue`, { params });
  }

  approveProperty(propertyId: string, notes?: string): Observable<any> {
    return this.http.put(`${this.API_URL}/moderation/${propertyId}/approve`, { notes });
  }

  rejectProperty(propertyId: string, reason: string): Observable<any> {
    return this.http.put(`${this.API_URL}/moderation/${propertyId}/reject`, { reason });
  }

  // Analytics
  getGrowthAnalytics(days: number = 30): Observable<any> {
    return this.http.get(`${this.API_URL}/analytics/growth`, { params: { days: days.toString() } });
  }
}