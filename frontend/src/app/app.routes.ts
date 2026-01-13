
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
   // General property view route (accessible to all authenticated users)
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
      // ✨ NOTIFICATION ROUTE
      {
        path: 'notifications',
        loadComponent: () =>
          import('./shared/notifications/notifications')
            .then(m => m.NotificationsComponent)
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
      path: 'nearby',  // ✅ Add this route
      loadComponent: () =>
        import('./tenant/nearby-search/nearby-search.component')
          .then(m => m.NearbySearchComponent)
      },
      {
        path: 'book-viewing/:id',
        loadComponent: () =>
        import('./tenant/create-booking/create-booking.component')
          .then(m => m.CreateBookingComponent),
        // canActivate: [authGuard, roleGuard],
        // title: 'Book Viewing'
      },
      {
        path: 'bookings',
              loadComponent: () =>
        import('./tenant/bookings/bookings.component')
          .then(m => m.TenantBookingsComponent)
      },
       // ✨ NOTIFICATION ROUTE
      {
        path: 'notifications',
        loadComponent: () =>
          import('./shared/notifications/notifications')
            .then(m => m.NotificationsComponent)
      }
    ],

//   //Default route
//   { path: '', redirectTo: 'login', pathMatch: 'full' },

//  // Catch-all
//   { path: '**', redirectTo: 'login' }
  },
];