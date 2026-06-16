import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { tap } from 'rxjs/operators';
import { environment } from '../../environments/environment.development';

/**
 * Shape of a successful login response.
 * Contains the JWT access token and basic info about the logged-in user.
 */
export interface LoginResponse {
  message: string;
  access_token: string;       // JWT used to authenticate subsequent requests
  user: {
    user_id: string;          // Unique user identifier from the backend
    email: string;
    role: string;             // e.g. tenant, landlord, admin
  };
}

/** Shape of a successful registration response. */
export interface RegisterResponse {
  message: string;
  email: string;
  role: string;
}

/** Shape returned by the "current user" endpoint. */
export interface UserData {
  user: {
    user_id: string;
    email: string;
    role: string;
  };
}

/**
 * Handles authentication: register, login, logout, password management,
 * and role-specific data fetches. Also exposes a reactive stream that
 * reflects whether the user is currently authenticated.
 * Provided in root, so a single instance is shared across the app.
 */
@Injectable({
  providedIn: 'root'
})
export class AuthService {
  // Base URL for all auth endpoints, built from the environment config.
  private API_URL = `${environment.apiUrl}/auth`;

  // Tracks authentication state; seeded from any token already in storage.
  private isAuthenticatedSubject = new BehaviorSubject<boolean>(this.hasToken());
  // Public stream components can subscribe to for reactive auth state.
  public isAuthenticated$ = this.isAuthenticatedSubject.asObservable();

  constructor(private http: HttpClient) {}

  /** Returns true if a token is present in localStorage. */
  private hasToken(): boolean {
    return !!localStorage.getItem('token');
  }

  /** Register a new account. */
  register(data: { email: string; password: string; role: string }): Observable<RegisterResponse> {
    return this.http.post<RegisterResponse>(`${this.API_URL}/register`, data);
  }

  /**
   * Log in and, on success, persist the auth data (token, role, email,
   * user ID) to localStorage and flip the authenticated state to true.
   */
  login(data: { email: string; password: string }): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${this.API_URL}/login`, data).pipe(
      tap(response => {
        if (response.access_token) {
          console.log(' Saving auth data:', response);

          // Persist all auth data so the session survives a page reload.
          localStorage.setItem('token', response.access_token);
          localStorage.setItem('role', response.user.role);
          localStorage.setItem('email', response.user.email);
          localStorage.setItem('userId', response.user.user_id);

          // Notify subscribers that the user is now authenticated.
          this.isAuthenticatedSubject.next(true);

          // Debug logging of what was stored (token is truncated).
          console.log('📦 Stored in localStorage:');
          console.log('  - token:', localStorage.getItem('token')?.substring(0, 20) + '...');
          console.log('  - role:', localStorage.getItem('role'));
          console.log('  - email:', localStorage.getItem('email'));
          console.log('  - userId:', localStorage.getItem('userId'));
        }
      })
    );
  }

  /** Clear all stored auth data and mark the user as logged out. */
  logout(): void {
    console.log('🚪 Logging out...');
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    localStorage.removeItem('email');
    localStorage.removeItem('userId');
    this.isAuthenticatedSubject.next(false);
  }

  /** Fetch the currently authenticated user's details from the backend. */
  getCurrentUser(): Observable<UserData> {
    return this.http.get<UserData>(`${this.API_URL}/me`);
  }

  /** Fetch bookings for the logged-in tenant. */
  getTenantBookings(): Observable<any> {
    return this.http.get(`${this.API_URL}/tenant/bookings`);
  }

  /** Fetch properties owned by the logged-in landlord. */
  getLandlordProperties(): Observable<any> {
    return this.http.get(`${this.API_URL}/landlord/properties`);
  }

  /** Fetch the admin dashboard payload. */
  getAdminDashboard(): Observable<any> {
    return this.http.get(`${this.API_URL}/admin/dashboard`);
  }

  // Helper methods for reading auth state synchronously from localStorage.

  /** Synchronous check for whether a token exists. */
  isLoggedIn(): boolean {
    return this.hasToken();
  }

  /** Get the stored JWT, or null if not logged in. */
  getToken(): string | null {
    return localStorage.getItem('token');
  }

  /** Get the stored user role, or null. */
  getUserRole(): string | null {
    return localStorage.getItem('role');
  }

  /** Get the stored user email, or null. */
  getUserEmail(): string | null {
    return localStorage.getItem('email');
  }

  /** Get the stored user ID, or null. */
  getUserId(): string | null {
    return localStorage.getItem('userId');
  }

  /**
   * Check whether the stored JWT has expired by decoding its payload.
   * Returns true if there is no token or it cannot be parsed.
   */
  isTokenExpired(): boolean {
    const token = this.getToken();
    if (!token) return true;

    try {
      // Decode the JWT payload (second segment) and read its expiry.
      const payload = JSON.parse(atob(token.split('.')[1]));
      const expiry = payload.exp * 1000; // exp is in seconds; convert to ms
      return Date.now() > expiry;
    } catch (e) {
      // Malformed token -> treat as expired.
      return true;
    }
  }

  // Password reset / change methods

  /**
   * Request a password reset email.
   * @returns Message plus an optional dev_token (returned only in dev).
   */
  forgotPassword(email: string): Observable<{message: string; email: string; dev_token?: string}> {
    return this.http.post<{message: string; email: string; dev_token?: string}>(
      `${this.API_URL}/forgot-password`,
      { email }
    );
  }

  /** Verify that a password reset token is valid for the given email. */
  verifyResetToken(email: string, token: string): Observable<{message: string; email: string}> {
    return this.http.post<{message: string; email: string}>(
      `${this.API_URL}/verify-reset-token`,
      { email, token }
    );
  }

  /** Complete a password reset using the emailed token. */
  resetPassword(email: string, token: string, newPassword: string): Observable<{message: string; email: string}> {
    return this.http.post<{message: string; email: string}>(
      `${this.API_URL}/reset-password`,
      { email, token, new_password: newPassword }
    );
  }

  /** Change the password for an already-logged-in user. */
  changePassword(currentPassword: string, newPassword: string): Observable<{message: string}> {
    return this.http.post<{message: string}>(
      `${this.API_URL}/change-password`,
      { current_password: currentPassword, new_password: newPassword }
    );
  }
}