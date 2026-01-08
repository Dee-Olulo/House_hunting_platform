import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule, RouterLink, CommonModule],
  templateUrl: './login.html',
  styleUrls: ['./login.css']
})
export class LoginComponent {
  email = '';
  password = '';
  errorMessage = '';
  isLoading = false;
  
  private router = inject(Router);
  private authService = inject(AuthService);

  login(): void {
    if (!this.email || !this.password) {
      this.errorMessage = 'Please fill in all fields';
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';

    this.authService.login({
      email: this.email,
      password: this.password
    }).subscribe({
      next: (response) => {
        console.log('Login successful', response);
        this.isLoading = false;
        
        // Navigate based on role
        const role = response.user.role;
        if (role === 'admin') {
          this.router.navigate(['/admin/dashboard']);
        } else if (role === 'landlord') {
          this.router.navigate(['/landlord/properties']);
        } else if (role === 'tenant') {
          this.router.navigate(['/tenant/bookings']);
        } else {
          this.router.navigate(['/dashboard']);
        }
      },
      error: (error) => {
        console.error('Login failed', error);
        this.isLoading = false;
        this.errorMessage = error.error?.error || 'Login failed. Please try again.';
      }
    });
  }
}