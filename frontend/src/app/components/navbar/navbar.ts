// import { Component, inject, OnInit } from '@angular/core';
// import { Router, RouterLink, RouterLinkActive } from '@angular/router';
// import { CommonModule } from '@angular/common';
// import { AuthService } from '../../services/auth';
// import { NotificationBellComponent } from '../../shared/notification-bell/notification-bell';

// @Component({
//   selector: 'app-navbar',
//   standalone: true,
//   imports: [CommonModule, RouterLink, NotificationBellComponent, RouterLinkActive],
//   templateUrl: './navbar.html',
//   styleUrls: ['./navbar.css'],
// })
// export class NavbarComponent implements OnInit {
//   private authService = inject(AuthService);
//   private router = inject(Router);
  
//   isLoggedIn = false;
//   userRole: string | null = null;
//   userEmail: string | null = null;

//   ngOnInit(): void {
//     // Subscribe to authentication status
//     this.authService.isAuthenticated$.subscribe(isAuth => {
//       this.isLoggedIn = isAuth;
//       if (isAuth) {
//         this.userRole = this.authService.getUserRole();
//         this.userEmail = this.authService.getUserEmail();
//       } else {
//         this.userRole = null;
//         this.userEmail = null;
//       }
//     });
//   }

//   logout(): void {
//     this.authService.logout();
//     this.router.navigate(['/login']);
//   }
// }
import { Component, inject, OnInit, HostListener } from '@angular/core';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../services/auth';
import { NotificationBellComponent } from '../../shared/notification-bell/notification-bell';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule, RouterLink, NotificationBellComponent, RouterLinkActive],
  templateUrl: './navbar.html',
  styleUrls: ['./navbar.css'],
})
export class NavbarComponent implements OnInit {
  private authService = inject(AuthService);
  private router = inject(Router);
  
  isLoggedIn = false;
  userRole: string | null = null;
  userEmail: string | null = null;
  favouritesCount = 0;
  
  // Mobile menu state
  isMobileMenuOpen = false;
  
  // User dropdown state
  isUserMenuOpen = false;

  ngOnInit(): void {
    // Subscribe to authentication status
    this.authService.isAuthenticated$.subscribe(isAuth => {
      this.isLoggedIn = isAuth;
      if (isAuth) {
        this.userRole = this.authService.getUserRole();
        this.userEmail = this.authService.getUserEmail();
        
        // Load favourites count for tenants
        if (this.userRole === 'tenant') {
          this.loadFavouritesCount();
        }
      } else {
        this.userRole = null;
        this.userEmail = null;
        this.favouritesCount = 0;
      }
    });
  }

  /**
   * Get home route based on user role
   */
  getHomeRoute(): string {
    if (!this.isLoggedIn) {
      return '/';
    }
    
    switch (this.userRole) {
      case 'tenant':
        return '/tenant/dashboard';
      case 'landlord':
        return '/landlord/properties';
      case 'admin':
        return '/admin/dashboard';
      default:
        return '/';
    }
  }

  /**
   * Get user initials for avatar
   */
  getUserInitials(): string {
    if (!this.userEmail) {
      return 'U';
    }
    
    const emailParts = this.userEmail.split('@')[0];
    const nameParts = emailParts.split(/[._-]/);
    
    if (nameParts.length >= 2) {
      return (nameParts[0][0] + nameParts[1][0]).toUpperCase();
    }
    
    return emailParts.substring(0, 2).toUpperCase();
  }

  /**
   * Load favourites count (for tenants)
   */
  loadFavouritesCount(): void {
    // TODO: Implement favourites service call
    // this.favouritesService.getFavouritesCount().subscribe({
    //   next: (count) => {
    //     this.favouritesCount = count;
    //   },
    //   error: (error) => {
    //     console.error('Failed to load favourites count:', error);
    //   }
    // });
    
    // Placeholder - get from localStorage
    const favourites = localStorage.getItem('favourites');
    if (favourites) {
      try {
        this.favouritesCount = JSON.parse(favourites).length;
      } catch (e) {
        this.favouritesCount = 0;
      }
    }
  }

  /**
   * Toggle mobile menu
   */
  toggleMobileMenu(): void {
    this.isMobileMenuOpen = !this.isMobileMenuOpen;
    this.isUserMenuOpen = false; // Close user menu when opening mobile menu
  }

  /**
   * Toggle user dropdown menu
   */
  toggleUserMenu(): void {
    this.isUserMenuOpen = !this.isUserMenuOpen;
  }

  /**
   * Close user dropdown menu
   */
  closeUserMenu(): void {
    this.isUserMenuOpen = false;
  }

  /**
   * Close menus when clicking outside
   */
  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    const target = event.target as HTMLElement;
    
    // Close user menu if clicking outside
    if (!target.closest('.user-profile-dropdown')) {
      this.isUserMenuOpen = false;
    }
    
    // Close mobile menu if clicking outside
    if (!target.closest('.navbar-container') && this.isMobileMenuOpen) {
      this.isMobileMenuOpen = false;
    }
  }

  /**
   * Logout user
   */
  logout(): void {
    this.authService.logout();
    this.closeUserMenu();
    this.isMobileMenuOpen = false;
    this.router.navigate(['/login']);
  }
}