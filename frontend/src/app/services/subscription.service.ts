// src/app/services/subscription.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment.development';

export interface SubscriptionPlan {
  id: string;
  name: string;
  price: number;
  currency: string;
  billing_cycle?: string;
  max_properties: number;
  max_photos: number;
  max_videos: number;
  commission_rate: number;
  listing_duration_days: number;
  featured_placement: boolean;
  priority_search: boolean;
  analytics: boolean;
  support_level: string;
  api_access: boolean;
  dedicated_manager?: boolean;
}

export interface CurrentSubscription {
  subscription: {
    tier: string;
    status: string;
    started_at: string;
    expires_at: string;
    auto_renew: boolean;
    name: string;
    price: number;
    max_properties: number;
    max_photos: number;
    max_videos: number;
    commission_rate: number;
    listing_duration_days: number;
    featured_placement: boolean;
    priority_search: boolean;
    analytics: boolean;
    support_level: string;
    api_access: boolean;
  };
  usage: {
    properties_count: number;
    properties_limit: number;
    total_bookings: number;
  };
  can_upgrade: boolean;
}

export interface SubscriptionPayment {
  _id: string;
  landlord_id: string;
  type: string;
  tier: string;
  amount: number;
  currency: string;
  billing_cycle: string;
  status: string;
  created_at: string;
  completed_at?: string;
}

@Injectable({
  providedIn: 'root'
})
export class SubscriptionService {
  private API_URL = `${environment.apiUrl}/subscription`;

  constructor(private http: HttpClient) {}

  getPlans(): Observable<{ plans: SubscriptionPlan[] }> {
    return this.http.get<{ plans: SubscriptionPlan[] }>(`${this.API_URL}/plans`);
  }

  getCurrentSubscription(): Observable<CurrentSubscription> {
    return this.http.get<CurrentSubscription>(`${this.API_URL}/current`);
  }

  subscribe(tier: string, billingCycle: string = 'monthly', autoRenew: boolean = true): Observable<any> {
    return this.http.post(`${this.API_URL}/subscribe`, {
      tier,
      billing_cycle: billingCycle,
      auto_renew: autoRenew
    });
  }

  confirmPayment(paymentId: string): Observable<any> {
    return this.http.post(`${this.API_URL}/confirm-payment/${paymentId}`, {});
  }

  cancelSubscription(): Observable<any> {
    return this.http.post(`${this.API_URL}/cancel`, {});
  }

  upgradeSubscription(tier: string): Observable<any> {
    return this.http.post(`${this.API_URL}/upgrade`, { tier });
  }

  getSubscriptionHistory(): Observable<{ payments: SubscriptionPayment[] }> {
    return this.http.get<{ payments: SubscriptionPayment[] }>(`${this.API_URL}/history`);
  }
}