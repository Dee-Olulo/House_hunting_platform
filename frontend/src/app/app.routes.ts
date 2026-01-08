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

// export const routes: Routes = [
//   {
//     path: 'login',
//     loadComponent: () =>
//       import('./auth/login/login')
//         .then(m => m.LoginComponent)
//   },
//   {
//     path: 'register',
//     loadComponent: () =>
//       import('./auth/register/register')
//         .then(m => m.RegisterComponent)
//   },

//   // Default route
//   { path: '', redirectTo: 'login', pathMatch: 'full' },

//   // Catch-all
//   { path: '**', redirectTo: 'login' }
// ];


// @Injectable({
//   providedIn: 'root'
// })
// export class AuthService {
//   // Flask backend base URL
//   private API_URL = 'http://127.0.0.1:5000/auth';

//   constructor(private http: HttpClient) {}

//   // REGISTER user
//   register(data: { email: string; password: string; role: string }): Observable<any> {
//     return this.http.post(`${this.API_URL}/register`, data);
//   }

//   // LOGIN user
//   login(data: { email: string; password: string }): Observable<any> {
//     return this.http.post(`${this.API_URL}/login`, data);
//   }
// }



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
      }
    ]
  },

  // Default route
//   { path: '', redirectTo: 'login', pathMatch: 'full' },

  // Catch-all
//   { path: '**', redirectTo: 'login' }
];