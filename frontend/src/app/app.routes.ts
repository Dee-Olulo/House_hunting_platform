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
      }
    ]
  },

//   //Default route
//   { path: '', redirectTo: 'login', pathMatch: 'full' },

//  // Catch-all
//   { path: '**', redirectTo: 'login' }
];