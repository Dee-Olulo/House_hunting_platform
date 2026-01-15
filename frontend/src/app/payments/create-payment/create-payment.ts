import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { PaymentService, CreatePaymentRequest } from '../../services/payment.service';

@Component({
  selector: 'app-create-payment',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './create-payment.html',
  styleUrls: ['./create-payment.css']
})
export class CreatePaymentComponent implements OnInit {
  private paymentService = inject(PaymentService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);

  propertyId: string = '';
  bookingId: string = '';
  
  payment: CreatePaymentRequest = {
    property_id: '',
    amount: 0,
    currency: 'KES',
    payment_type: 'booking_fee',
    payment_method: 'mpesa',
    description: ''
  };

  mpesaPhoneNumber: string = '';
  
  loading = false;
  error: string = '';
  success: string = '';
  
  showMpesaPrompt = false;
  checkoutRequestId: string = '';
  pollingInterval: any;

  paymentTypes = [
    { value: 'booking_fee', label: 'Booking Fee' },
    { value: 'deposit', label: 'Deposit' },
    { value: 'rent', label: 'Rent Payment' },
    { value: 'security_deposit', label: 'Security Deposit' },
    { value: 'other', label: 'Other' }
  ];

  paymentMethods = [
    { value: 'mpesa', label: 'M-Pesa', icon: '📱' },
    { value: 'card', label: 'Credit/Debit Card', icon: '💳' },
    { value: 'bank_transfer', label: 'Bank Transfer', icon: '🏦' },
    { value: 'cash', label: 'Cash', icon: '💵' }
  ];

  ngOnInit(): void {
    // Get property and booking IDs from route params
    this.route.queryParams.subscribe(params => {
      this.propertyId = params['propertyId'] || '';
      this.bookingId = params['bookingId'] || '';
      
      if (this.propertyId) {
        this.payment.property_id = this.propertyId;
      }
      if (this.bookingId) {
        this.payment.booking_id = this.bookingId;
      }

      // Get suggested amount from params
      if (params['amount']) {
        this.payment.amount = parseFloat(params['amount']);
      }
    });
  }

  createPayment(): void {
    this.error = '';
    this.success = '';
    this.loading = true;

    // Validate
    if (!this.payment.property_id) {
      this.error = 'Property ID is required';
      this.loading = false;
      return;
    }

    if (this.payment.amount <= 0) {
      this.error = 'Amount must be greater than 0';
      this.loading = false;
      return;
    }

    if (this.payment.payment_method === 'mpesa' && !this.mpesaPhoneNumber) {
      this.error = 'M-Pesa phone number is required';
      this.loading = false;
      return;
    }

    // Create payment
    this.paymentService.createPayment(this.payment).subscribe({
      next: (response) => {
        const paymentId = response.payment._id;
        
        if (this.payment.payment_method === 'mpesa') {
          // Initiate M-Pesa STK Push
          this.initiateMpesaPayment(paymentId);
        } else {
          // For other payment methods, show success
          this.success = 'Payment created successfully!';
          this.loading = false;
          
          // Redirect to payment history after 2 seconds
          setTimeout(() => {
            this.router.navigate(['/tenant/payments/history']);
          }, 2000);
        }
      },
      error: (error) => {
        this.error = error.error?.error || 'Failed to create payment';
        this.loading = false;
      }
    });
  }

  initiateMpesaPayment(paymentId: string): void {
    this.paymentService.initiateMpesaPayment(paymentId, this.mpesaPhoneNumber).subscribe({
      next: (response) => {
        if (response.success) {
          this.showMpesaPrompt = true;
          this.checkoutRequestId = response.checkout_request_id;
          this.success = response.message || 'Check your phone for M-Pesa prompt';
          
          // Start polling for payment status
          this.startPolling(paymentId);
        } else {
          this.error = response.error || 'Failed to initiate M-Pesa payment';
          this.loading = false;
        }
      },
      error: (error) => {
        this.error = error.error?.error || 'Failed to initiate M-Pesa payment';
        this.loading = false;
      }
    });
  }

  startPolling(paymentId: string): void {
    let pollCount = 0;
    const maxPolls = 40; // 2 minutes (40 * 3 seconds)

    this.pollingInterval = setInterval(() => {
      pollCount++;

      this.paymentService.getPaymentDetails(paymentId).subscribe({
        next: (response) => {
          const payment = response.payment;
          
          if (payment.status === 'completed') {
            clearInterval(this.pollingInterval);
            this.loading = false;
            this.showMpesaPrompt = false;
            this.success = 'Payment completed successfully!';
            
            // Redirect to payment history
            setTimeout(() => {
              this.router.navigate(['/tenant/payments/history']);
            }, 2000);
         }
        //   else if (payment.status === 'failed') {
        //     clearInterval(this.pollingInterval);
        //     this.loading = false;
        //     this.showMpesaPrompt = false;
        //     this.error = payment.failure_reason || 'Payment failed';
        //   }
          
          // Stop polling after max attempts
          if (pollCount >= maxPolls) {
            clearInterval(this.pollingInterval);
            this.loading = false;
            this.error = 'Payment timeout. Please check your payment history.';
          }
        },
        error: (error) => {
          console.error('Polling error:', error);
        }
      });
    }, 3000); // Poll every 3 seconds
  }

  cancelPayment(): void {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
    }
    this.router.navigate(['/tenant/dashboard']);
  }

  ngOnDestroy(): void {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
    }
  }

  getPaymentTypeLabel(): string {
    const type = this.paymentTypes.find(t => t.value === this.payment.payment_type);
    return type ? type.label : this.payment.payment_type;
  }

  getPaymentMethodLabel(): string {
    const method = this.paymentMethods.find(m => m.value === this.payment.payment_method);
    return method ? method.label : this.payment.payment_method;
  }
}