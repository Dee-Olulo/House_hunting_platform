// moderation-queue.component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AdminService, ModerationProperty } from '../../services/admin.service';
import { environment } from '../../../environments/environment.development';

@Component({
  selector: 'app-moderation-queue',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './moderation-queue.html',
  styleUrls: ['./moderation-queue.css']
})
export class ModerationQueueComponent implements OnInit {
  properties: ModerationProperty[] = [];
  isLoading = true;
  errorMessage = '';
  successMessage = '';

  // Filters
  sortBy = 'score_low';

  // Pagination
  currentPage = 1;
  perPage = 20;
  totalProperties = 0;
  totalPages = 0;

  // Modal state
  showApproveModal = false;
  showRejectModal = false;
  selectedProperty: ModerationProperty | null = null;
  approvalNotes = '';
  rejectionReason = '';

  // API URL for images
  apiUrl = environment.apiUrl;

  constructor(
    private adminService: AdminService,
    public router: Router
  ) {}

  ngOnInit(): void {
    this.loadQueue();
  }

  loadQueue(): void {
    this.isLoading = true;
    this.errorMessage = '';

    const params = {
      page: this.currentPage,
      per_page: this.perPage,
      sort_by: this.sortBy
    };

    this.adminService.getModerationQueue(params).subscribe({
      next: (response) => {
        this.properties = response.properties;
        this.totalProperties = response.total;
        this.totalPages = response.total_pages;
        this.isLoading = false;
      },
      error: (error) => {
        this.errorMessage = 'Failed to load moderation queue';
        this.isLoading = false;
        console.error('Error:', error);
      }
    });
  }

  onSortChange(): void {
    this.currentPage = 1;
    this.loadQueue();
  }

  nextPage(): void {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
      this.loadQueue();
    }
  }

  previousPage(): void {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.loadQueue();
    }
  }

  openApproveModal(property: ModerationProperty): void {
    this.selectedProperty = property;
    this.approvalNotes = '';
    this.showApproveModal = true;
  }

  closeApproveModal(): void {
    this.showApproveModal = false;
    this.selectedProperty = null;
    this.approvalNotes = '';
  }

  confirmApprove(): void {
    if (!this.selectedProperty) return;

    this.adminService.approveProperty(
      this.selectedProperty._id,
      this.approvalNotes
    ).subscribe({
      next: () => {
        this.successMessage = 'Property approved successfully';
        this.closeApproveModal();
        this.loadQueue();
        setTimeout(() => this.successMessage = '', 3000);
      },
      error: (error) => {
        this.errorMessage = error.error?.error || 'Failed to approve property';
        console.error('Error:', error);
      }
    });
  }

  openRejectModal(property: ModerationProperty): void {
    this.selectedProperty = property;
    this.rejectionReason = '';
    this.showRejectModal = true;
  }

  closeRejectModal(): void {
    this.showRejectModal = false;
    this.selectedProperty = null;
    this.rejectionReason = '';
  }

  confirmReject(): void {
    if (!this.selectedProperty || !this.rejectionReason.trim()) {
      this.errorMessage = 'Please provide a rejection reason';
      return;
    }

    this.adminService.rejectProperty(
      this.selectedProperty._id,
      this.rejectionReason
    ).subscribe({
      next: () => {
        this.successMessage = 'Property rejected successfully';
        this.closeRejectModal();
        this.loadQueue();
        setTimeout(() => this.successMessage = '', 3000);
      },
      error: (error) => {
        this.errorMessage = error.error?.error || 'Failed to reject property';
        console.error('Error:', error);
      }
    });
  }

  getScoreBadgeClass(score: number): string {
    if (score >= 0.8) return 'score-high';
    if (score >= 0.6) return 'score-medium';
    return 'score-low';
  }

  getImageUrl(imagePath: string): string {
    if (!imagePath) return '/assets/placeholder-property.jpg';
    if (imagePath.startsWith('http')) return imagePath;
    return `${this.apiUrl}/${imagePath}`;
  }

  truncateText(text: string, maxLength: number): string {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  }
}