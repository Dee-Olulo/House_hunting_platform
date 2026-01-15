// src/app/auth/forgot-password/forgot-password.component.ts

import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-forgot-password',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <div class="forgot-password-page">
      <div class="forgot-password-container">
        <div class="back-link">
          <a routerLink="/login">← Back to Login</a>
        </div>

        <div class="forgot-password-card">
          <!-- Step 1: Request Reset -->
          <div *ngIf="step === 'request'" class="step-content">
            <div class="icon-container">
              <span class="icon">🔒</span>
            </div>
            
            <h2>Forgot Password?</h2>
            <p class="description">
              Enter your email address and we'll send you a code to reset your password.
            </p>

            <div *ngIf="errorMessage" class="error-message">
              {{ errorMessage }}
            </div>

            <form (ngSubmit)="requestReset()" #requestForm="ngForm">
              <div class="form-group">
                <label for="email">Email Address</label>
                <input
                  id="email"
                  type="email"
                  name="email"
                  [(ngModel)]="email"
                  required
                  email
                  placeholder="Enter your email"
                  class="form-input"
                  [disabled]="isLoading"
                />
              </div>

              <button
                type="submit"
                [disabled]="!requestForm.valid || isLoading"
                class="submit-btn"
              >
                {{ isLoading ? 'Sending...' : 'Send Reset Code' }}
              </button>
            </form>
          </div>

          <!-- Step 2: Enter Token -->
          <div *ngIf="step === 'verify'" class="step-content">
            <div class="icon-container">
              <span class="icon">📧</span>
            </div>
            
            <h2>Enter Reset Code</h2>
            <p class="description">
              We've sent a 6-digit code to <strong>{{ email }}</strong>
            </p>

            <div *ngIf="errorMessage" class="error-message">
              {{ errorMessage }}
            </div>

            <div *ngIf="devToken" class="dev-token">
              <strong>Development Token:</strong> {{ devToken }}
            </div>

            <form (ngSubmit)="verifyToken()" #tokenForm="ngForm">
              <div class="form-group">
                <label for="token">Reset Code</label>
                <input
                  id="token"
                  type="text"
                  name="token"
                  [(ngModel)]="token"
                  required
                  maxlength="6"
                  placeholder="Enter 6-digit code"
                  class="form-input token-input"
                  [disabled]="isLoading"
                />
              </div>

              <button
                type="submit"
                [disabled]="!tokenForm.valid || isLoading"
                class="submit-btn"
              >
                {{ isLoading ? 'Verifying...' : 'Verify Code' }}
              </button>

              <button
                type="button"
                class="resend-btn"
                (click)="resendCode()"
                [disabled]="isLoading"
              >
                Resend Code
              </button>
            </form>
          </div>

          <!-- Step 3: Reset Password -->
          <div *ngIf="step === 'reset'" class="step-content">
            <div class="icon-container">
              <span class="icon">🔑</span>
            </div>
            
            <h2>Create New Password</h2>
            <p class="description">
              Enter a new password for your account
            </p>

            <div *ngIf="errorMessage" class="error-message">
              {{ errorMessage }}
            </div>

            <form (ngSubmit)="resetPassword()" #resetForm="ngForm">
              <div class="form-group">
                <label for="new-password">New Password</label>
                <input
                  id="new-password"
                  type="password"
                  name="newPassword"
                  [(ngModel)]="newPassword"
                  required
                  minlength="6"
                  placeholder="Enter new password"
                  class="form-input"
                  [disabled]="isLoading"
                />
              </div>

              <div class="form-group">
                <label for="confirm-password">Confirm Password</label>
                <input
                  id="confirm-password"
                  type="password"
                  name="confirmPassword"
                  [(ngModel)]="confirmPassword"
                  required
                  minlength="6"
                  placeholder="Confirm new password"
                  class="form-input"
                  [disabled]="isLoading"
                />
              </div>

              <button
                type="submit"
                [disabled]="!resetForm.valid || isLoading"
                class="submit-btn"
              >
                {{ isLoading ? 'Resetting...' : 'Reset Password' }}
              </button>
            </form>
          </div>

          <!-- Step 4: Success -->
          <div *ngIf="step === 'success'" class="step-content success-content">
            <div class="icon-container success">
              <span class="icon">✓</span>
            </div>
            
            <h2>Password Reset Successful!</h2>
            <p class="description">
              Your password has been reset successfully. You can now log in with your new password.
            </p>

            <button
              class="submit-btn"
              (click)="goToLogin()"
            >
              Go to Login
            </button>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .forgot-password-page {
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      padding: 20px;
    }

    .forgot-password-container {
      width: 100%;
      max-width: 500px;
    }

    .back-link {
      margin-bottom: 20px;
    }

    .back-link a {
      color: white;
      text-decoration: none;
      font-size: 14px;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      transition: opacity 0.3s;
    }

    .back-link a:hover {
      opacity: 0.8;
    }

    .forgot-password-card {
      background: white;
      border-radius: 12px;
      padding: 40px;
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
    }

    .icon-container {
      width: 80px;
      height: 80px;
      background: #f0f4ff;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 24px;
    }

    .icon-container.success {
      background: #e8f5e9;
    }

    .icon {
      font-size: 40px;
    }

    h2 {
      text-align: center;
      color: #2c3e50;
      margin: 0 0 12px 0;
    }

    .description {
      text-align: center;
      color: #7f8c8d;
      margin: 0 0 32px 0;
      line-height: 1.5;
    }

    .form-group {
      margin-bottom: 20px;
    }

    label {
      display: block;
      margin-bottom: 8px;
      color: #2c3e50;
      font-weight: 500;
      font-size: 14px;
    }

    .form-input {
      width: 100%;
      padding: 12px 16px;
      border: 2px solid #e0e0e0;
      border-radius: 8px;
      font-size: 15px;
      transition: all 0.3s;
    }

    .form-input:focus {
      outline: none;
      border-color: #667eea;
    }

    .form-input:disabled {
      background: #f5f5f5;
      cursor: not-allowed;
    }

    .token-input {
      text-align: center;
      font-size: 24px;
      letter-spacing: 8px;
      font-weight: 600;
    }

    .submit-btn {
      width: 100%;
      padding: 14px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border: none;
      border-radius: 8px;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s;
    }

    .submit-btn:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }

    .submit-btn:disabled {
      opacity: 0.6;
      cursor: not-allowed;
      transform: none;
    }

    .resend-btn {
      width: 100%;
      padding: 12px;
      background: transparent;
      color: #667eea;
      border: 2px solid #667eea;
      border-radius: 8px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      margin-top: 12px;
      transition: all 0.3s;
    }

    .resend-btn:hover:not(:disabled) {
      background: #f0f4ff;
    }

    .resend-btn:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    .error-message {
      background: #fee;
      color: #c33;
      padding: 12px;
      border-radius: 8px;
      margin-bottom: 20px;
      text-align: center;
      font-size: 14px;
    }

    .dev-token {
      background: #fff3cd;
      border: 2px solid #ffc107;
      padding: 12px;
      border-radius: 8px;
      margin-bottom: 20px;
      text-align: center;
      font-size: 14px;
    }

    .success-content {
      text-align: center;
    }

    @media (max-width: 600px) {
      .forgot-password-card {
        padding: 24px;
      }
    }
  `]
})
export class ForgotPasswordComponent {
  step: 'request' | 'verify' | 'reset' | 'success' = 'request';
  email = '';
  token = '';
  newPassword = '';
  confirmPassword = '';
  errorMessage = '';
  isLoading = false;
  devToken = ''; // For development only

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  requestReset(): void {
    this.isLoading = true;
    this.errorMessage = '';

    this.authService.forgotPassword(this.email).subscribe({
      next: (response) => {
        console.log('Reset requested:', response);
        this.devToken = response.dev_token || ''; // For development
        this.step = 'verify';
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Reset request failed:', error);
        this.errorMessage = error.error?.error || 'Failed to send reset code';
        this.isLoading = false;
      }
    });
  }

  verifyToken(): void {
    this.isLoading = true;
    this.errorMessage = '';

    this.authService.verifyResetToken(this.email, this.token).subscribe({
      next: () => {
        console.log('Token verified');
        this.step = 'reset';
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Token verification failed:', error);
        this.errorMessage = error.error?.error || 'Invalid or expired code';
        this.isLoading = false;
      }
    });
  }

  resetPassword(): void {
    if (this.newPassword !== this.confirmPassword) {
      this.errorMessage = 'Passwords do not match';
      return;
    }

    if (this.newPassword.length < 6) {
      this.errorMessage = 'Password must be at least 6 characters';
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';

    this.authService.resetPassword(this.email, this.token, this.newPassword).subscribe({
      next: () => {
        console.log('Password reset successful');
        this.step = 'success';
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Password reset failed:', error);
        this.errorMessage = error.error?.error || 'Failed to reset password';
        this.isLoading = false;
      }
    });
  }

  resendCode(): void {
    this.requestReset();
  }

  goToLogin(): void {
    this.router.navigate(['/login']);
  }
}