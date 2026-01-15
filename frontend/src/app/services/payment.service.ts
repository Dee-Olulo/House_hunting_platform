import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface Payment {
  _id: string;
  tenant_id: string;
  property_id: string;
  landlord_id: string;
  booking_id?: string;
  amount: number;
  currency: string;
  payment_type: 'deposit' | 'rent' | 'booking_fee' | 'security_deposit' | 'other';
  payment_method: 'card' | 'bank_transfer' | 'mpesa' | 'paypal' | 'stripe' | 'cash' | 'cheque';
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'refunded';
  transaction_id?: string;
  gateway_reference?: string;
  description?: string;
  metadata?: any;
  refund_status?: string;
  refund_amount?: number;
  refund_reason?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  property_details?: {
    title: string;
    address: string;
    city: string;
  };
  tenant_details?: {
    name: string;
    email: string;
  };
}

export interface CreatePaymentRequest {
  property_id: string;
  booking_id?: string;
  amount: number;
  currency?: string;
  payment_type: string;
  payment_method: string;
  description?: string;
  metadata?: any;
}

export interface MpesaSTKRequest {
  payment_id: string;
  phone_number: string;
}

export interface PaymentStats {
  total_payments: number;
  completed: number;
  pending: number;
  failed: number;
  refunded: number;
  total_amount: number;
}

export interface PaginatedPayments {
  payments: Payment[];
  pagination: {
    total: number;
    page: number;
    limit: number;
    pages: number;
  };
}

@Injectable({
  providedIn: 'root'
})
export class PaymentService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/payments`;

  private getHeaders(): HttpHeaders {
    const token = localStorage.getItem('token');
    return new HttpHeaders({
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    });
  }

  // Create a new payment
  createPayment(paymentData: CreatePaymentRequest): Observable<any> {
    return this.http.post(`${this.apiUrl}/create`, paymentData, {
      headers: this.getHeaders()
    });
  }

  // Process a pending payment
  processPayment(paymentId: string, data?: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/process/${paymentId}`, data || {}, {
      headers: this.getHeaders()
    });
  }

  // Get tenant payment history
  getTenantPaymentHistory(page: number = 1, limit: number = 10, status?: string): Observable<PaginatedPayments> {
    let url = `${this.apiUrl}/tenant/history?page=${page}&limit=${limit}`;
    if (status) {
      url += `&status=${status}`;
    }
    return this.http.get<PaginatedPayments>(url, {
      headers: this.getHeaders()
    });
  }

  // Get landlord payment history
  getLandlordPaymentHistory(page: number = 1, limit: number = 10, status?: string, propertyId?: string): Observable<PaginatedPayments> {
    let url = `${this.apiUrl}/landlord/history?page=${page}&limit=${limit}`;
    if (status) {
      url += `&status=${status}`;
    }
    if (propertyId) {
      url += `&property_id=${propertyId}`;
    }
    return this.http.get<PaginatedPayments>(url, {
      headers: this.getHeaders()
    });
  }

  // Get payment details
  getPaymentDetails(paymentId: string): Observable<{ payment: Payment }> {
    return this.http.get<{ payment: Payment }>(`${this.apiUrl}/${paymentId}`, {
      headers: this.getHeaders()
    });
  }

  // Request refund
  requestRefund(paymentId: string, reason: string, amount?: number): Observable<any> {
    return this.http.post(`${this.apiUrl}/refund/${paymentId}`, {
      reason,
      amount
    }, {
      headers: this.getHeaders()
    });
  }

  // Approve refund (admin only)
  approveRefund(paymentId: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/refund/${paymentId}/approve`, {}, {
      headers: this.getHeaders()
    });
  }

  // Get payment statistics
  getPaymentStats(): Observable<{ stats: PaymentStats }> {
    return this.http.get<{ stats: PaymentStats }>(`${this.apiUrl}/stats`, {
      headers: this.getHeaders()
    });
  }

  // ==================== M-PESA SPECIFIC METHODS ====================

  // Initiate M-Pesa STK Push
  initiateMpesaPayment(paymentId: string, phoneNumber: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/mpesa/stk-push`, {
      payment_id: paymentId,
      phone_number: phoneNumber
    }, {
      headers: this.getHeaders()
    });
  }

  // Query M-Pesa payment status
  queryMpesaPayment(paymentId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/mpesa/query/${paymentId}`, {
      headers: this.getHeaders()
    });
  }

  // ==================== FLUTTERWAVE SPECIFIC METHODS ====================

  // Initialize Flutterwave payment
  initializeFlutterwavePayment(paymentId: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/flutterwave/initialize`, {
      payment_id: paymentId
    }, {
      headers: this.getHeaders()
    });
  }

  // Verify Flutterwave transaction
  verifyFlutterwaveTransaction(transactionId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/flutterwave/verify/${transactionId}`, {
      headers: this.getHeaders()
    });
  }
}