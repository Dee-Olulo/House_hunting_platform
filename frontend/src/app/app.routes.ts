
import { Routes } from '@angular/router';
import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { LoginComponent } from './auth/login/login';
import { RegisterComponent } from './auth/register/register';
import { authGuard } from './guards/auth-guard';
import { roleGuard } from './guards/role.guard';
import { CreateBookingComponent } from './tenant/create-booking/create-booking.component';
import { TenantBookingsComponent } from './tenant/bookings/bookings.component';
import { LandlordBookingsComponent } from './landlord/bookings/bookings.component';
import { adminGuard } from './guards/admin.guard';

export const routes: Routes = [
  // Auth routes
  {
    path: 'login',
    loadComponent: () =>
      import('./auth/login/login')
        .then(m => m.LoginComponent)
  },
  {
    path: 'register',
    loadComponent: () =>
      import('./auth/register/register')
        .then(m => m.RegisterComponent)
  },
  {
  path: 'forgot-password',
  loadComponent: () =>
    import('./auth/forgot-password/forgot-password.component')
      .then(m => m.ForgotPasswordComponent)
},

  // ✅ FIXED: Add general properties list route (accessible to all authenticated users)
  {
    path: 'properties',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./tenant/dashboard/dashboard.component')
        .then(m => m.DashboardComponent)
  },

  // General property details view route (accessible to all authenticated users)
  {
    path: 'properties/:id',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./property-details/property-details')
        .then(m => m.PropertyDetailsComponent)
  },

  // Landlord routes
  {
    path: 'landlord',
    canActivate: [authGuard, roleGuard],
    data: { role: 'landlord' },
    children: [
      {
        path: 'properties',
        loadComponent: () =>
          import('./landlord/properties')
            .then(m => m.PropertiesComponent)
      },
      {
        path: 'properties/add',
        loadComponent: () =>
          import('./landlord/add-property/add-property')
            .then(m => m.AddPropertyComponent)
      },
      {
        path: 'properties/edit/:id',
        loadComponent: () =>
          import('./landlord/edit-property/edit-property')
            .then(m => m.EditPropertyComponent)
      },
      // Booking routes for landlord
      {
        path: 'bookings',
        loadComponent: () =>
          import('./landlord/bookings/bookings.component')
            .then(m => m.LandlordBookingsComponent)
      },
      // Notification routes
      {
        path: 'notifications',
        loadComponent: () =>
          import('./shared/notifications/notifications')
            .then(m => m.NotificationsComponent)
      },
      {
        path: 'payments',
        loadComponent: () =>
          import('./payments/payment-history/payment-history')
            .then(m => m.PaymentHistoryComponent)
      },
      {
        path: 'payments/:id',
        loadComponent: () =>
          import('./payments/payment-details/payment-details')
            .then(m => m.PaymentDetailsComponent)
      },
    // ? Subscription plan route
      {
        path: 'subscription',
        loadComponent: () =>
          import('./landlord/subscription-plans/suscription-plans')
            .then(m => m.SubscriptionPlansComponent)
      },
      {
        path: 'reviews',
        loadComponent: () =>
          import('./landlord/my-reviews/my-reviews')
            .then(m => m.MyReviewsComponent)
      }

    ]
  },

  // Tenant routes
  {
    path: 'tenant',
    canActivate: [authGuard, roleGuard],
    data: { role: 'tenant' },
    children: [
      {
        path: '',
        redirectTo: 'dashboard',
        pathMatch: 'full'
      },
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./tenant/dashboard/dashboard.component')
            .then(m => m.DashboardComponent)
      },
      {
        path: 'property/:id',
        loadComponent: () =>
          import('./property-details/property-details')
            .then(m => m.PropertyDetailsComponent)
      },
      {
        path: 'nearby',
        loadComponent: () =>
          import('./tenant/nearby-search/nearby-search.component')
            .then(m => m.NearbySearchComponent)
      },
      {
        path: 'book-viewing/:id',
        loadComponent: () =>
          import('./tenant/create-booking/create-booking.component')
            .then(m => m.CreateBookingComponent)
      },
      {
        path: 'bookings',
        loadComponent: () =>
          import('./tenant/bookings/bookings.component')
            .then(m => m.TenantBookingsComponent)
      },
      {
        path: 'notifications',
        loadComponent: () =>
          import('./shared/notifications/notifications')
            .then(m => m.NotificationsComponent)
      },
      {
        path: 'favourites',
        loadComponent: () =>
          import('./tenant/favourites/favourites.component')
            .then(m => m.FavouritesComponent)
      },
      {
        path: 'payments/create',
        loadComponent: () =>
          import('./payments/create-payment/create-payment')
            .then(m => m.CreatePaymentComponent)
      },
      {
        path: 'payments/history',
        loadComponent: () =>
          import('./payments/payment-history/payment-history')
            .then(m => m.PaymentHistoryComponent)
      },
      {
        path: 'payments/:id',
        loadComponent: () =>
          import('./payments/payment-details/payment-details')
            .then(m => m.PaymentDetailsComponent)
      },
      {
        path: 'reviews',
        loadComponent: () =>
          import('./tenant/create-review/create-review')
            .then(m => m.CreateReviewComponent)
      }
    ]
  },
  // Admin routes
{
    path: 'admin',
    canActivate: [adminGuard],
    children: [
      {
        path: 'dashboard',
        loadComponent: () => import('./admin/admin-dashboard/admin-dashboard')
          .then(m => m.AdminDashboardComponent)
      },
      {
        path: 'users',
        loadComponent: () => import('./admin/user-management/user-management')
          .then(m => m.UserManagementComponent)
      },
      {
        path: 'moderation',
        loadComponent: () => import('./admin/moderation-queue/moderation-queue')
          .then(m => m.ModerationQueueComponent)
      },
      {
        path: 'analytics',
        loadComponent: () => import('./admin/analytics-dashboard/analytics-dashboard')
          .then(m => m.AnalyticsDashboardComponent)
      },
      {
        path: 'financial',
        loadComponent: () => import('./admin/financial-dashboard/financial-dashboard')
          .then(m => m.FinancialDashboardComponent)
      },
      {
        path:'notifications',
        loadComponent:() => import('./admin/notification-management/notification-management')
          .then(m => m.NotificationManagementComponent)
      },
      {
        path: '',
        redirectTo: 'dashboard',
        pathMatch: 'full'
      }
    
  
  ],
},


  // Default route
  { path: '', redirectTo: 'login', pathMatch: 'full' },

  // Catch-all route
  { path: '**', redirectTo: 'login' }


];