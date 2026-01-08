import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { AuthService } from '../services/auth';

export const roleGuard = (allowedRoles: string[]): CanActivateFn => {
  return (route, state) => {
    const authService = inject(AuthService);
    const router = inject(Router);

    if (!authService.isLoggedIn()) {
      router.navigate(['/login']);
      return false;
    }

    const userRole = authService.getUserRole();
    if (userRole && allowedRoles.includes(userRole)) {
      return true;
    }

    // Redirect to unauthorized page or dashboard
    router.navigate(['/unauthorized']);
    return false;
  };
};