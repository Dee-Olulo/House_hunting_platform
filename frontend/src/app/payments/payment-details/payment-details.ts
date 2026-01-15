import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { PaymentService, Payment } from '../../services/payment.service';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-payment-details',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './payment-details.html',
  styleUrls: ['./payment-details.css']
})
export class PaymentDetailsComponent implements OnInit {
  private paymentService = inject(PaymentService);
  private authService = inject(AuthService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);

  payment: Payment | null = null;
  loading = true;
  error = '';
  userRole = '';

  ngOnInit(): void {
    this.userRole = this.authService.getUserRole() || '';
    
    const paymentId = this.route.snapshot.paramMap.get('id');
    if (paymentId) {
      this.loadPaymentDetails(paymentId);
    } else {
      this.error = 'Payment ID not found';
      this.loading = false;
    }
  }

  loadPaymentDetails(paymentId: string): void {
    this.loading = true;
    this.error = '';

    this.paymentService.getPaymentDetails(paymentId).subscribe({
      next: (response) => {
        this.payment = response.payment;
        this.loading = false;
      },
      error: (error) => {
        this.error = error.error?.error || 'Failed to load payment details';
        this.loading = false;
      }
    });
  }

  goBack(): void {
    if (this.userRole === 'tenant') {
      this.router.navigate(['/tenant/payments/history']);
    } else if (this.userRole === 'landlord') {
      this.router.navigate(['/landlord/payments']);
    }
  }

  getStatusClass(status: string): string {
    const statusClasses: { [key: string]: string } = {
      'completed': 'status-completed',
      'pending': 'status-pending',
      'processing': 'status-processing',
      'failed': 'status-failed',
      'refunded': 'status-refunded',
      'failed_reason':'status-failed'
    };
    return statusClasses[status] || '';
  }

  getStatusIcon(status: string): string {
    const statusIcons: { [key: string]: string } = {
      'completed': '✓',
      'pending': '⏳',
      'processing': '⚡',
      'failed': '✗',
      'refunded': '↩'
    };
    return statusIcons[status] || '•';
  }

  formatDate(dateString: string): string {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  formatCurrency(amount: number, currency: string): string {
    return `${currency} ${amount.toLocaleString('en-US', { 
      minimumFractionDigits: 2, 
      maximumFractionDigits: 2 
    })}`;
  }

  copyToClipboard(text: string): void {
    navigator.clipboard.writeText(text).then(() => {
      alert('Copied to clipboard!');
    }).catch(err => {
      console.error('Failed to copy:', err);
    });
  }
}