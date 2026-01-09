import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { PropertyService, Property } from '../services/property.service';
import { AuthService } from '../services/auth';

@Component({
  selector: 'app-property-details',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './property-details.html',
  styleUrls: ['./property-details.css']
})
export class PropertyDetailsComponent implements OnInit {
  property: Property | null = null;
  propertyId: string = '';
  currentImageIndex = 0;
  isLoading = true;
  errorMessage = '';
  isLoggedIn = false;
  userRole: string | null = null;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private propertyService: PropertyService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.propertyId = this.route.snapshot.params['id'];
    this.isLoggedIn = this.authService.isLoggedIn();
    this.userRole = this.authService.getUserRole();
    
    console.log('Loading property:', this.propertyId);
    console.log('User logged in:', this.isLoggedIn);
    console.log('User role:', this.userRole);
    
    this.loadProperty();
  }

  loadProperty(): void {
    this.isLoading = true;
    this.errorMessage = '';
    
    this.propertyService.getProperty(this.propertyId).subscribe({
      next: (property) => {
        console.log('✅ Property loaded:', property);
        this.property = property;
        this.isLoading = false;
      },
      error: (error) => {
        console.error('❌ Error loading property:', error);
        this.errorMessage = 'Property not found or failed to load';
        this.isLoading = false;
      }
    });
  }

  getImageUrl(imagePath: string): string {
    if (!imagePath) return '';
    return this.propertyService.getImageUrl(imagePath);
  }

  hasImages(): boolean {
    return !!(this.property?.images && this.property.images.length > 0);
  }

  nextImage(): void {
    if (this.property && this.property.images && this.property.images.length > 0) {
      this.currentImageIndex = (this.currentImageIndex + 1) % this.property.images.length;
    }
  }

  previousImage(): void {
    if (this.property && this.property.images && this.property.images.length > 0) {
      this.currentImageIndex = this.currentImageIndex === 0 
        ? this.property.images.length - 1 
        : this.currentImageIndex - 1;
    }
  }

  selectImage(index: number): void {
    this.currentImageIndex = index;
  }

  contactLandlord(): void {
    if (!this.isLoggedIn) {
      alert('Please login to contact the landlord');
      this.router.navigate(['/login'], { 
        queryParams: { returnUrl: `/properties/${this.propertyId}` }
      });
      return;
    }
    // TODO: Implement contact/messaging functionality
    alert('Contact functionality will be implemented in the messaging system.\n\nFor now, you can reach out to the property owner through the booking system.');
  }

  bookViewing(): void {
    if (!this.isLoggedIn) {
      alert('Please login to book a viewing');
      this.router.navigate(['/login'], { 
        queryParams: { returnUrl: `/properties/${this.propertyId}` }
      });
      return;
    }
    if (this.userRole !== 'tenant') {
      alert('Only tenants can book property viewings');
      return;
    }
    // TODO: Navigate to booking page
    alert('Booking system coming soon!\n\nYou will be able to:\n• Schedule property viewings\n• Choose time slots\n• Get confirmation from landlord');
    // Future: this.router.navigate(['/tenant/book-viewing', this.propertyId]);
  }

  goBack(): void {
     window.history.back();
  }

  editProperty(): void {
    this.router.navigate(['/landlord/properties/edit', this.propertyId]);
  }

  isOwner(): boolean {
    // Check if current user is the landlord who owns this property
    if (!this.isLoggedIn || !this.property) return false;
    const currentUser = this.authService.getCurrentUser;
    // This would need the landlord_id comparison - simplified for now
    return this.userRole === 'landlord';
  }
}