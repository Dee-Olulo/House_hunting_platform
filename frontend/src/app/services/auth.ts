// import { Injectable } from '@angular/core';
// import { HttpClient } from '@angular/common/http';
// import { Observable, BehaviorSubject } from 'rxjs';
// import { tap } from 'rxjs/operators';
// import { environment } from '../../environments/environment.development';

// export interface LoginResponse {
//   message: string;
//   access_token: string;
//   user: {
//     email: string;
//     role: string;
//   };
// }

// export interface RegisterResponse {
//   message: string;
//   email: string;
//   role: string;
// }

// export interface UserData {
//   user: {
//     user_id: string;
//     email: string;
//     role: string;
//   };
// }

// @Injectable({
//   providedIn: 'root'
// })
// export class AuthService {
//   private API_URL = `${environment.apiUrl}/auth`;
//   private isAuthenticatedSubject = new BehaviorSubject<boolean>(this.hasToken());
//   public isAuthenticated$ = this.isAuthenticatedSubject.asObservable();

//   constructor(private http: HttpClient) {}

//   private hasToken(): boolean {
//     return !!localStorage.getItem('token');
//   }

//   // REGISTER
//   register(data: { email: string; password: string; role: string }): Observable<RegisterResponse> {
//     return this.http.post<RegisterResponse>(`${this.API_URL}/register`, data);
//   }

//   // LOGIN
//   login(data: { email: string; password: string }): Observable<LoginResponse> {
//     return this.http.post<LoginResponse>(`${this.API_URL}/login`, data).pipe(
//       tap(response => {
//         if (response.access_token) {
//           localStorage.setItem('token', response.access_token);
//           localStorage.setItem('role', response.user.role);
//           localStorage.setItem('email', response.user.email);
//           this.isAuthenticatedSubject.next(true);
//         }
//       })
//     );
//   }

//   // LOGOUT
//   logout(): void {
//     localStorage.removeItem('token');
//     localStorage.removeItem('role');
//     localStorage.removeItem('email');
//     this.isAuthenticatedSubject.next(false);
//   }

//   // GET CURRENT USER
//   getCurrentUser(): Observable<UserData> {
//     return this.http.get<UserData>(`${this.API_URL}/me`);
//   }

//   // GET TENANT BOOKINGS
//   getTenantBookings(): Observable<any> {
//     return this.http.get(`${this.API_URL}/tenant/bookings`);
//   }

//   // GET LANDLORD PROPERTIES
//   getLandlordProperties(): Observable<any> {
//     return this.http.get(`${this.API_URL}/landlord/properties`);
//   }

//   // GET ADMIN DASHBOARD
//   getAdminDashboard(): Observable<any> {
//     return this.http.get(`${this.API_URL}/admin/dashboard`);
//   }

//   // HELPER METHODS
//   isLoggedIn(): boolean {
//     return this.hasToken();
//   }

//   getToken(): string | null {
//     return localStorage.getItem('token');
//   }

//   getUserRole(): string | null {
//     return localStorage.getItem('role');
//   }

//   getUserEmail(): string | null {
//     return localStorage.getItem('email');
//   }
// }
// src/app/services/auth.ts (UPDATED - SAVES USER ID)

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { tap } from 'rxjs/operators';
import { environment } from '../../environments/environment.development';

export interface LoginResponse {
  message: string;
  access_token: string;
  user: {
    user_id: string;  // ⭐ THIS IS IN YOUR BACKEND RESPONSE
    email: string;
    role: string;
  };
}

export interface RegisterResponse {
  message: string;
  email: string;
  role: string;
}

export interface UserData {
  user: {
    user_id: string;
    email: string;
    role: string;
  };
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private API_URL = `${environment.apiUrl}/auth`;
  private isAuthenticatedSubject = new BehaviorSubject<boolean>(this.hasToken());
  public isAuthenticated$ = this.isAuthenticatedSubject.asObservable();

  constructor(private http: HttpClient) {}

  private hasToken(): boolean {
    return !!localStorage.getItem('token');
  }

  // REGISTER
  register(data: { email: string; password: string; role: string }): Observable<RegisterResponse> {
    return this.http.post<RegisterResponse>(`${this.API_URL}/register`, data);
  }

  // LOGIN - ⭐ FIXED TO SAVE USER_ID
  login(data: { email: string; password: string }): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${this.API_URL}/login`, data).pipe(
      tap(response => {
        if (response.access_token) {
          console.log('✅ Saving auth data:', response);
          
          // Save all auth data to localStorage
          localStorage.setItem('token', response.access_token);
          localStorage.setItem('role', response.user.role);
          localStorage.setItem('email', response.user.email);
          localStorage.setItem('userId', response.user.user_id); // ⭐ SAVE USER ID
          
          // Update authenticated state
          this.isAuthenticatedSubject.next(true);
          
          // Log what was saved for debugging
          console.log('📦 Stored in localStorage:');
          console.log('  - token:', localStorage.getItem('token')?.substring(0, 20) + '...');
          console.log('  - role:', localStorage.getItem('role'));
          console.log('  - email:', localStorage.getItem('email'));
          console.log('  - userId:', localStorage.getItem('userId'));
        }
      })
    );
  }

  // LOGOUT
  logout(): void {
    console.log('🚪 Logging out...');
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    localStorage.removeItem('email');
    localStorage.removeItem('userId'); // ⭐ REMOVE USER ID
    this.isAuthenticatedSubject.next(false);
  }

  // GET CURRENT USER
  getCurrentUser(): Observable<UserData> {
    return this.http.get<UserData>(`${this.API_URL}/me`);
  }

  // GET TENANT BOOKINGS
  getTenantBookings(): Observable<any> {
    return this.http.get(`${this.API_URL}/tenant/bookings`);
  }

  // GET LANDLORD PROPERTIES
  getLandlordProperties(): Observable<any> {
    return this.http.get(`${this.API_URL}/landlord/properties`);
  }

  // GET ADMIN DASHBOARD
  getAdminDashboard(): Observable<any> {
    return this.http.get(`${this.API_URL}/admin/dashboard`);
  }

  // HELPER METHODS
  isLoggedIn(): boolean {
    return this.hasToken();
  }

  getToken(): string | null {
    return localStorage.getItem('token');
  }

  getUserRole(): string | null {
    return localStorage.getItem('role');
  }

  getUserEmail(): string | null {
    return localStorage.getItem('email');
  }

  // ⭐ NEW METHOD TO GET USER ID
  getUserId(): string | null {
    return localStorage.getItem('userId');
  }

  // Check if token is expired
  isTokenExpired(): boolean {
    const token = this.getToken();
    if (!token) return true;
    
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const expiry = payload.exp * 1000; // Convert to milliseconds
      return Date.now() > expiry;
    } catch (e) {
      return true;
    }
  }

  // ⭐ PASSWORD RESET METHODS

  /**
   * Request password reset
   */
  forgotPassword(email: string): Observable<{message: string; email: string; dev_token?: string}> {
    return this.http.post<{message: string; email: string; dev_token?: string}>(
      `${this.API_URL}/forgot-password`,
      { email }
    );
  }

  /**
   * Verify reset token
   */
  verifyResetToken(email: string, token: string): Observable<{message: string; email: string}> {
    return this.http.post<{message: string; email: string}>(
      `${this.API_URL}/verify-reset-token`,
      { email, token }
    );
  }

  /**
   * Reset password with token
   */
  resetPassword(email: string, token: string, newPassword: string): Observable<{message: string; email: string}> {
    return this.http.post<{message: string; email: string}>(
      `${this.API_URL}/reset-password`,
      { email, token, new_password: newPassword }
    );
  }

  /**
   * Change password (for logged-in users)
   */
  changePassword(currentPassword: string, newPassword: string): Observable<{message: string}> {
    return this.http.post<{message: string}>(
      `${this.API_URL}/change-password`,
      { current_password: currentPassword, new_password: newPassword }
    );
  }
}