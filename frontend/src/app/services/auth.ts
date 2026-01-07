// 
import { Injectable, Inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { tap } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private API_URL = 'http://127.0.0.1:5000/auth';

  constructor(private http: HttpClient) {}

  private httpOptions = {
    headers: new HttpHeaders({
      'Content-Type': 'application/json'
    })
  };

  // REGISTER
  register(data: { email: string; password: string; role: string }) {
    return this.http.post(`${this.API_URL}/register`, data, this.httpOptions);
  }

  // LOGIN
  login(data: { email: string; password: string }) {
    return this.http.post<any>(`${this.API_URL}/login`, data, this.httpOptions)
      .pipe(
        tap(response => {
          if (response.access_token) {
            localStorage.setItem('token', response.access_token);
            localStorage.setItem('role', response.role);
          }
        })
      );
  }

  // LOGOUT
  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
  }

  // Example: GET protected tenant bookings
  getTenantBookings() {
    const token = localStorage.getItem('token');
    const headers = new HttpHeaders({
      'Authorization': `Bearer ${token}`
    });
    return this.http.get(`${this.API_URL}/tenant/bookings`, { headers });
  }
}
