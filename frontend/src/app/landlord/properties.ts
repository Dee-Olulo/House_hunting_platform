import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { PropertyService, Property } from '../services/property.service';

@Component({
  selector: 'app-properties',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './properties.html',
  styleUrls: ['./properties.css']
})
export class PropertiesComponent implements OnInit {
  properties: Property[] = [];
  isLoading = false;
  errorMessage = '';
  successMessage = '';

  constructor(
    private propertyService: PropertyService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadProperties();
  }

  loadProperties(): void {
    this.isLoading = true;
    this.errorMessage = '';

    this.propertyService.getMyProperties().subscribe({
      next: (response) => {
        this.properties = response.properties;
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading properties:', error);
        this.errorMessage = error.error?.error || 'Failed to load properties';
        this.isLoading = false;
      }
    });
  }

  getImageUrl(imagePath: string): string {
    return this.propertyService.getImageUrl(imagePath);
  }

  editProperty(propertyId: string): void {
    this.router.navigate(['/landlord/properties/edit', propertyId]);
    
  }

  deleteProperty(propertyId: string, title: string): void {
    if (confirm(`Are you sure you want to delete "${title}"?`)) {
      this.propertyService.deleteProperty(propertyId).subscribe({
        next: (response) => {
          this.successMessage = response.message;
          this.loadProperties(); // Reload list
          setTimeout(() => this.successMessage = '', 3000);
        },
        error: (error) => {
          console.error('Error deleting property:', error);
          this.errorMessage = error.error?.error || 'Failed to delete property';
          setTimeout(() => this.errorMessage = '', 3000);
        }
      });
    }
  }

  confirmProperty(propertyId: string): void {
    this.propertyService.confirmProperty(propertyId).subscribe({
      next: (response) => {
        this.successMessage = response.message;
        this.loadProperties(); // Reload list
        setTimeout(() => this.successMessage = '', 3000);
      },
      error: (error) => {
        console.error('Error confirming property:', error);
        this.errorMessage = error.error?.error || 'Failed to confirm property';
        setTimeout(() => this.errorMessage = '', 3000);
      }
    });
  }

  viewProperty(propertyId: string): void {
    this.router.navigate(['/properties', propertyId]);
  }

  getStatusClass(status: string): string {
    const statusClasses: { [key: string]: string } = {
      'active': 'status-active',
      'inactive': 'status-inactive',
      'pending': 'status-pending',
      'expired': 'status-expired'
    };
    return statusClasses[status] || 'status-default';
  }
}
