import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { PaymentService, Payment, PaymentStats } from '../../services/payment.service';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-payment-history',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './payment-history.html',
  styleUrls: ['./payment-history.css']
})
export class PaymentHistoryComponent implements OnInit {
  private paymentService = inject(PaymentService);
  private authService = inject(AuthService);
  private router = inject(Router);

  payments: Payment[] = [];
  stats: PaymentStats | null = null;
  
  loading = false;
  error = '';
  
  // Pagination
  currentPage = 1;
  itemsPerPage = 10;
  totalPages = 1;
  totalItems = 0;
  
  // Filters
  statusFilter = '';
  userRole = '';
  
  // Refund modal
  showRefundModal = false;
  selectedPayment: Payment | null = null;
  refundReason = '';
  refundAmount = 0;

  ngOnInit(): void {
    this.userRole = this.authService.getUserRole() || '';
    this.loadPayments();
    this.loadStats();
  }

  loadPayments(): void {
    this.loading = true;
    this.error = '';

    const loadMethod = this.userRole === 'landlord' 
      ? this.paymentService.getLandlordPaymentHistory(this.currentPage, this.itemsPerPage, this.statusFilter)
      : this.paymentService.getTenantPaymentHistory(this.currentPage, this.itemsPerPage, this.statusFilter);

    loadMethod.subscribe({
      next: (response) => {
        this.payments = response.payments;
        this.totalItems = response.pagination.total;
        this.totalPages = response.pagination.pages;
        this.loading = false;
      },
      error: (error) => {
        this.error = error.error?.error || 'Failed to load payments';
        this.loading = false;
      }
    });
  }

  loadStats(): void {
    this.paymentService.getPaymentStats().subscribe({
      next: (response) => {
        this.stats = response.stats;
      },
      error: (error) => {
        console.error('Failed to load stats:', error);
      }
    });
  }

  filterByStatus(status: string): void {
    this.statusFilter = status === this.statusFilter ? '' : status;
    this.currentPage = 1;
    this.loadPayments();
  }

  goToPage(page: number): void {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.loadPayments();
    }
  }

  viewPaymentDetails(paymentId: string): void {
    this.router.navigate(['/tenant/payments', paymentId]);
  }

  openRefundModal(payment: Payment): void {
    this.selectedPayment = payment;
    this.refundAmount = payment.amount;
    this.refundReason = '';
    this.showRefundModal = true;
  }

  closeRefundModal(): void {
    this.showRefundModal = false;
    this.selectedPayment = null;
    this.refundReason = '';
  }

  requestRefund(): void {
    if (!this.selectedPayment || !this.refundReason) {
      return;
    }

    this.paymentService.requestRefund(
      this.selectedPayment._id,
      this.refundReason,
      this.refundAmount
    ).subscribe({
      next: () => {
        this.closeRefundModal();
        this.loadPayments();
        alert('Refund request submitted successfully');
      },
      error: (error) => {
        alert(error.error?.error || 'Failed to request refund');
      }
    });
  }

  getStatusClass(status: string): string {
    const statusClasses: { [key: string]: string } = {
      'completed': 'status-completed',
      'pending': 'status-pending',
      'processing': 'status-processing',
      'failed': 'status-failed',
      'refunded': 'status-refunded'
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
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  formatCurrency(amount: number, currency: string): string {
    return `${currency} ${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }

  canRequestRefund(payment: Payment): boolean {
    return payment.status === 'completed' && 
           !payment.refund_status &&
           this.userRole === 'tenant';
  }
}