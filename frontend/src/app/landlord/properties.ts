import { Component, OnInit, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { PropertyService, Property } from '../services/property.service';
import { ListingConfirmationService, ConfirmationStatus }
        from '../services/listing-confirmation.service';   // ← NEW

@Component({
  selector: 'app-properties',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './properties.html',
  styleUrls: ['./properties.css'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class PropertiesComponent implements OnInit {
  properties: Property[] = [];
  isLoading = false;
  errorMessage = '';
  successMessage = '';

  /** NEW: maps property._id → its confirmation status */
  confirmationStatuses: Map<string, ConfirmationStatus> = new Map();

  // Prevent double navigation
  private isNavigating = false;

  constructor(
    private propertyService: PropertyService,
    private router: Router,
    private cdr: ChangeDetectorRef,
    private listingConfirmationService: ListingConfirmationService   // ← NEW
  ) {}

  ngOnInit(): void {
    this.loadProperties();
  }

  loadProperties(): void {
    this.isLoading = true;
    this.errorMessage = '';
    this.cdr.markForCheck();

    this.propertyService.getMyProperties().subscribe({
      next: (response) => {
        this.properties = response.properties;
        this.isLoading = false;
        this.cdr.markForCheck();

        // ── NEW: fetch confirmation status for every active property ─
        this.properties.forEach(p => this.loadConfirmationStatus(p._id!));
      },
      error: (error) => {
        console.error('Error loading properties:', error);
        this.errorMessage = error.error?.error || 'Failed to load properties';
        this.isLoading = false;
        this.cdr.markForCheck();
      }
    });
  }

  // ── NEW: pull confirmation status for one property ──────────────────
  private loadConfirmationStatus(propertyId: string): void {
    this.listingConfirmationService.getConfirmationStatus(propertyId).subscribe({
      next: (status) => {
        this.confirmationStatuses.set(propertyId, status);
        this.cdr.markForCheck();
      },
      error: () => {
        // Non-critical — card still renders, just without the badge
        console.warn('Could not load confirmation status for', propertyId);
      }
    });
  }

  /** NEW: returns the cached ConfirmationStatus (or undefined) for template use */
  getConfirmationStatus(propertyId: string): ConfirmationStatus | undefined {
    return this.confirmationStatuses.get(propertyId);
  }

  getImageUrl(imagePath: string): string {
    return this.propertyService.getImageUrl(imagePath);
  }

  // ── navigation helpers (unchanged) ────────────────────────────────────
  editProperty(propertyId: string, event?: MouseEvent): void {
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }
    if (this.isNavigating) {
      console.log('⚠️ Navigation already in progress, ignoring click');
      return;
    }
    console.log('🔵 Edit button clicked for property:', propertyId);
    this.isNavigating = true;
    this.router.navigate(['/landlord/properties/edit', propertyId]).then(success => {
      console.log(success ? '✅ Navigation successful' : '❌ Navigation failed');
    }).finally(() => { setTimeout(() => { this.isNavigating = false; }, 500); });
  }

  viewProperty(propertyId: string, event?: MouseEvent): void {
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }
    if (this.isNavigating) {
      console.log('⚠️ Navigation already in progress, ignoring click');
      return;
    }
    console.log('🔵 View button clicked for property:', propertyId);
    this.isNavigating = true;
    this.router.navigate(['/properties', propertyId]).then(success => {
      console.log(success ? '✅ Navigation successful' : '❌ Navigation failed');
    }).finally(() => { setTimeout(() => { this.isNavigating = false; }, 500); });
  }

  deleteProperty(propertyId: string, title: string, event?: MouseEvent): void {
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }
    if (confirm(`Are you sure you want to delete "${title}"?`)) {
      this.propertyService.deleteProperty(propertyId).subscribe({
        next: (response) => {
          this.successMessage = response.message;
          this.loadProperties();
          this.cdr.markForCheck();
          setTimeout(() => { this.successMessage = ''; this.cdr.markForCheck(); }, 3000);
        },
        error: (error) => {
          console.error('Error deleting property:', error);
          this.errorMessage = error.error?.error || 'Failed to delete property';
          this.cdr.markForCheck();
          setTimeout(() => { this.errorMessage = ''; this.cdr.markForCheck(); }, 3000);
        }
      });
    }
  }

  /**
   * NEW: calls the dedicated listing-confirmation endpoint instead of
   * the generic property confirm.  On success it refreshes the status badge.
   */
  confirmProperty(propertyId: string, event?: MouseEvent): void {
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }

    this.listingConfirmationService.confirmListing(propertyId).subscribe({
      next: (response) => {
        this.successMessage = response.message;

        // Optimistically update the local status map
        const existing = this.confirmationStatuses.get(propertyId);
        if (existing) {
          existing.confirmation_pending    = false;
          existing.days_since_confirmed    = 0;
          existing.days_until_reminder     = 30;
          existing.will_deactivate_in      = 60;
          existing.last_confirmed          = response.confirmed_at;
          this.confirmationStatuses.set(propertyId, existing);
        }

        this.cdr.markForCheck();
        setTimeout(() => { this.successMessage = ''; this.cdr.markForCheck(); }, 3000);
      },
      error: (error) => {
        console.error('Error confirming property:', error);
        this.errorMessage = error.error?.error || 'Failed to confirm property';
        this.cdr.markForCheck();
        setTimeout(() => { this.errorMessage = ''; this.cdr.markForCheck(); }, 3000);
      }
    });
  }

  getStatusClass(status: string): string {
    const statusClasses: { [key: string]: string } = {
      'active':   'status-active',
      'inactive': 'status-inactive',
      'pending':  'status-pending',
      'expired':  'status-expired'
    };
    return statusClasses[status] || 'status-default';
  }
}