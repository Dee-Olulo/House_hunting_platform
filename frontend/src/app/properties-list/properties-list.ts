import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { PropertyService, Property } from '../services/property.service';

@Component({
  selector: 'app-properties-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './properties-list.html',
  styleUrls: ['./properties-list.css']
})
export class PropertiesListComponent implements OnInit {
  properties: Property[] = [];
  filteredProperties: Property[] = [];
  
  // Filter states
  showFilters = false;
  searchCity = '';
  minPrice: number | null = null;
  maxPrice: number | null = null;
  selectedBedrooms: number | null = null;
  selectedType = '';
  sortBy = 'newest';
  
  isLoading = false;
  errorMessage = '';
  
  propertyTypes = ['apartment', 'house', 'studio', 'condo', 'townhouse', 'villa'];
  bedroomOptions = [0, 1, 2, 3, 4, 5];
  
  constructor(
    private propertyService: PropertyService,
    private router: Router
  ) {}

  ngOnInit(): void {
    console.log('PropertiesListComponent initialized');
    this.loadProperties();
  }

  loadProperties(): void {
    this.isLoading = true;
    this.errorMessage = '';
    
    console.log('Loading properties...');
    
    this.propertyService.getMyProperties().subscribe({
      next: (response) => {
        // Extract properties array from the response object
        console.log('✅ Properties loaded successfully:', response.properties.length, 'properties');
        this.properties = response.properties;
        this.filteredProperties = [...response.properties];
        this.applyFilters();
        this.isLoading = false;
      },
      error: (error: HttpErrorResponse) => {
        console.error('❌ Error loading properties:', error);
        this.errorMessage = error.error?.message || 'Failed to load properties. Please try again.';
        this.isLoading = false;
      }
    });
  }

  getImageUrl(imagePath: string): string {
    return this.propertyService.getImageUrl(imagePath);
  }

  viewProperty(propertyId: string): void {
    if (!propertyId) {
      console.error('Invalid property ID');
      return;
    }

    const userRole = this.getUserRole();
    console.log('Viewing property:', propertyId, 'User role:', userRole);
    
    // Navigate based on role
    if (userRole === 'landlord') {
      this.router.navigate(['/properties', propertyId]);
    } else {
      this.router.navigate(['/tenant/property', propertyId]);
    }
  }

  private getUserRole(): string {
    const role = localStorage.getItem('userRole') || 'tenant';
    console.log('User role from localStorage:', role);
    return role;
  }

  toggleFilters(): void {
    this.showFilters = !this.showFilters;
    console.log('Filters visibility:', this.showFilters ? 'shown' : 'hidden');
  }

  applyFilters(): void {
    console.log('Applying filters...', {
      city: this.searchCity,
      minPrice: this.minPrice,
      maxPrice: this.maxPrice,
      bedrooms: this.selectedBedrooms,
      type: this.selectedType
    });

    let filtered = [...this.properties];
    const initialCount = filtered.length;

    // Filter by city
    if (this.searchCity && this.searchCity.trim()) {
      const searchTerm = this.searchCity.toLowerCase().trim();
      filtered = filtered.filter(p => 
        p.city?.toLowerCase().includes(searchTerm) ||
        p.state?.toLowerCase().includes(searchTerm) ||
        p.address?.toLowerCase().includes(searchTerm)
      );
      console.log(`City filter: ${filtered.length} properties match "${searchTerm}"`);
    }

    // Filter by price range
    if (this.minPrice !== null && this.minPrice > 0) {
      filtered = filtered.filter(p => p.price >= this.minPrice!);
      console.log(`Min price filter (>= ${this.minPrice}): ${filtered.length} properties`);
    }
    if (this.maxPrice !== null && this.maxPrice > 0) {
      filtered = filtered.filter(p => p.price <= this.maxPrice!);
      console.log(`Max price filter (<= ${this.maxPrice}): ${filtered.length} properties`);
    }

    // Filter by bedrooms
    if (this.selectedBedrooms !== null) {
      filtered = filtered.filter(p => p.bedrooms === this.selectedBedrooms);
      console.log(`Bedrooms filter (${this.selectedBedrooms}): ${filtered.length} properties`);
    }

    // Filter by property type
    if (this.selectedType) {
      filtered = filtered.filter(p => p.property_type === this.selectedType);
      console.log(`Type filter (${this.selectedType}): ${filtered.length} properties`);
    }

    console.log(`Filter results: ${initialCount} -> ${filtered.length} properties`);
    this.filteredProperties = filtered;
    this.applySorting();
  }

  clearFilters(): void {
    console.log('Clearing all filters');
    this.searchCity = '';
    this.minPrice = null;
    this.maxPrice = null;
    this.selectedBedrooms = null;
    this.selectedType = '';
    this.sortBy = 'newest';
    this.applyFilters();
  }

  hasActiveFilters(): boolean {
    return !!(
      this.searchCity ||
      this.minPrice ||
      this.maxPrice ||
      this.selectedBedrooms !== null ||
      this.selectedType
    );
  }

  onSortChange(): void {
    console.log('Sort changed to:', this.sortBy);
    this.applySorting();
  }

  private applySorting(): void {
    const beforeSort = [...this.filteredProperties];
    
    switch (this.sortBy) {
      case 'newest':
        this.filteredProperties.sort((a, b) => {
          const dateA = a.created_at ? new Date(a.created_at).getTime() : 0;
          const dateB = b.created_at ? new Date(b.created_at).getTime() : 0;
          return dateB - dateA;
        });
        console.log('Sorted by newest first');
        break;
        
      case 'price_low':
        this.filteredProperties.sort((a, b) => a.price - b.price);
        console.log('Sorted by price: low to high');
        break;
        
      case 'price_high':
        this.filteredProperties.sort((a, b) => b.price - a.price);
        console.log('Sorted by price: high to low');
        break;
        
      case 'bedrooms':
        this.filteredProperties.sort((a, b) => b.bedrooms - a.bedrooms);
        console.log('Sorted by most bedrooms');
        break;
        
      default:
        console.log('No sorting applied');
    }

    // Check if order actually changed
    const orderChanged = beforeSort.some((prop, index) => 
      prop._id !== this.filteredProperties[index]?._id
    );
    
    if (orderChanged) {
      console.log('Property order changed after sorting');
    }
  }

  // Helper method to format price
  formatPrice(price: number): string {
    return new Intl.NumberFormat('en-KE', {
      style: 'currency',
      currency: 'KES',
      minimumFractionDigits: 0
    }).format(price);
  }

  // Helper method to get property status badge class
  getStatusClass(status?: string): string {
    switch (status?.toLowerCase()) {
      case 'active':
        return 'status-active';
      case 'pending':
        return 'status-pending';
      case 'rented':
        return 'status-rented';
      default:
        return 'status-unknown';
    }
  }
  getModerationClass(status?: string): string {
  switch (status) {
    case 'approved':
      return 'moderation-approved';
    case 'pending_review':
      return 'moderation-pending';
    case 'rejected':
      return 'moderation-rejected';
    default:
      return 'moderation-unknown';
  }
}

/**
 * Get human-readable label for moderation status
 */
getModerationLabel(status?: string): string {
  switch (status) {
    case 'approved':
      return '✓ Approved';
    case 'pending_review':
      return '⏳ Under Review';
    case 'rejected':
      return '✗ Needs Improvement';
    default:
      return 'Unknown';
  }
}

/**
 * View moderation details
 */
viewModerationDetails(propertyId: string): void {
  this.propertyService.getModerationStatus(propertyId).subscribe({
    next: (details) => {
      console.log('Moderation details:', details);
      
      // Show in alert (or create a modal)
      let message = `Status: ${details.moderation_status}\n`;
      message += `Score: ${details.moderation_score}/100\n`;
      if (details.moderation_issues.length > 0) {
        message += `\nIssues:\n${details.moderation_issues.join('\n')}`;
      }
      alert(message);
    },
    error: (error) => {
      console.error('Error fetching moderation details:', error);
    }
  });
}

/**
 * Request re-moderation after fixes
 */
requestRemoderation(propertyId: string): void {
  if (confirm('Request re-moderation? Make sure you\'ve fixed all issues first.')) {
    this.propertyService.remoderateProperty(propertyId).subscribe({
      next: (response) => {
        alert(response.moderation.message);
        this.loadProperties();  // Refresh list
      },
      error: (error) => {
        console.error('Error re-moderating:', error);
        alert('Failed to remoderate property');
      }
    });
  }
}

}