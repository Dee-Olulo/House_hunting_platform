// src/app/landlord/subscription-plans/subscription-plans.component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import {
  SubscriptionService,
  SubscriptionPlan,
  CurrentSubscription
} from '../../services/subscription.service';

@Component({
  selector: 'app-subscription-plans',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './subscription-plans.html',
  styleUrls: ['./subscription-plans.css']
})
export class SubscriptionPlansComponent implements OnInit {
  plans: SubscriptionPlan[] = [];
  currentSubscription: CurrentSubscription | null = null;
  isLoading = true;
  errorMessage = '';
  successMessage = '';

  showPaymentModal = false;
  selectedPlan: SubscriptionPlan | null = null;
  pendingPaymentId = '';

  constructor(
    private subscriptionService: SubscriptionService,
    public router: Router
  ) {}

  ngOnInit(): void {
    this.loadPlans();
    this.loadCurrentSubscription();
  }

  loadPlans(): void {
    this.subscriptionService.getPlans().subscribe({
      next: (response) => {
        this.plans = response.plans;
      },
      error: (error) => {
        this.errorMessage = 'Failed to load subscription plans';
        console.error('Error:', error);
      }
    });
  }

  loadCurrentSubscription(): void {
    this.subscriptionService.getCurrentSubscription().subscribe({
      next: (data) => {
        this.currentSubscription = data;
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading subscription:', error);
        this.isLoading = false;
      }
    });
  }

  selectPlan(plan: SubscriptionPlan): void {
    if (plan.id === 'free') {
      this.errorMessage = 'You are already on the free plan';
      return;
    }

    if (this.currentSubscription?.subscription.tier === plan.id) {
      this.errorMessage = 'You are already on this plan';
      return;
    }

    this.selectedPlan = plan;
    this.initiateSubscription();
  }

  initiateSubscription(): void {
    if (!this.selectedPlan) return;

    this.subscriptionService.subscribe(this.selectedPlan.id, 'monthly', true).subscribe({
      next: (response) => {
        this.pendingPaymentId = response.payment_id;
        this.showPaymentModal = true;
      },
      error: (error) => {
        this.errorMessage = error.error?.error || 'Failed to initiate subscription';
        console.error('Error:', error);
      }
    });
  }

  confirmPayment(): void {
    if (!this.pendingPaymentId) return;

    this.subscriptionService.confirmPayment(this.pendingPaymentId).subscribe({
      next: () => {
        this.successMessage = 'Subscription activated successfully!';
        this.showPaymentModal = false;
        this.selectedPlan = null;
        this.pendingPaymentId = '';
        this.loadCurrentSubscription();
        setTimeout(() => this.successMessage = '', 3000);
      },
      error: (error) => {
        this.errorMessage = error.error?.error || 'Payment confirmation failed';
        console.error('Error:', error);
      }
    });
  }

  closePaymentModal(): void {
    this.showPaymentModal = false;
    this.selectedPlan = null;
    this.pendingPaymentId = '';
  }

  isCurrentPlan(planId: string): boolean {
    return this.currentSubscription?.subscription.tier === planId;
  }

  canSelectPlan(planId: string): boolean {
    if (!this.currentSubscription) return planId !== 'free';
    const current = this.currentSubscription.subscription.tier;
    return planId !== current && planId !== 'free';
  }

  getPlanBadgeClass(planId: string): string {
    const classes: { [key: string]: string } = {
      'free': 'badge-free',
      'basic': 'badge-basic',
      'premium': 'badge-premium'
    };
    return classes[planId] || '';
  }

  formatPrice(price: number): string {
    return new Intl.NumberFormat('en-KE', {
      style: 'currency',
      currency: 'KES'
    }).format(price);
  }
}