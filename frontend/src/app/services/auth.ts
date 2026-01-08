import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { tap } from 'rxjs/operators';
import { environment } from '../../environments/environment.development';

export interface LoginResponse {
  message: string;
  access_token: string;
  user: {
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

  // LOGIN
  login(data: { email: string; password: string }): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${this.API_URL}/login`, data).pipe(
      tap(response => {
        if (response.access_token) {
          localStorage.setItem('token', response.access_token);
          localStorage.setItem('role', response.user.role);
          localStorage.setItem('email', response.user.email);
          this.isAuthenticatedSubject.next(true);
        }
      })
    );
  }

  // LOGOUT
  logout(): void {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    localStorage.removeItem('email');
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
}