// src/app/tenant/dashboard/dashboard.component.ts

import { Component, OnInit } from '@angular/core';
import { PropertySearchService } from '../services/property-search.service';
import {
  Property,
  PropertySearchParams,
  FilterOptions
} from '../models/property.interface';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit {
  // Properties data
  properties: Property[] = [];
  totalProperties: number = 0;
  currentPage: number = 1;
  perPage: number = 12;
  totalPages: number = 0;

  // Loading states
  isLoading: boolean = false;
  isLoadingFilters: boolean = false;

  // Filter options from backend
  filterOptions: FilterOptions | null = null;

  // Search filters
  searchFilters: PropertySearchParams = {
    status: 'active',
    sort_by: 'newest',
    page: 1,
    per_page: 12
  };

  // UI state
  showFilters: boolean = false;
  viewMode: 'grid' | 'list' = 'grid';

  // Sort options
  sortOptions = [
    { value: 'newest', label: 'Newest First' },
    { value: 'price_low', label: 'Price: Low to High' },
    { value: 'price_high', label: 'Price: High to Low' },
    { value: 'bedrooms', label: 'Most Bedrooms' }
  ];

  constructor(private propertySearchService: PropertySearchService) {}

  ngOnInit(): void {
    this.loadFilterOptions();
    this.searchProperties();
  }

  /**
   * Load available filter options
   */
  loadFilterOptions(): void {
    this.isLoadingFilters = true;
    this.propertySearchService.getFilterOptions().subscribe({
      next: (options) => {
        this.filterOptions = options;
        this.isLoadingFilters = false;
      },
      error: (error) => {
        console.error('Error loading filter options:', error);
        this.isLoadingFilters = false;
      }
    });
  }

  /**
   * Search properties with current filters
   */
  searchProperties(): void {
    this.isLoading = true;
    this.searchFilters.page = this.currentPage;
    this.searchFilters.per_page = this.perPage;

    this.propertySearchService.searchProperties(this.searchFilters).subscribe({
      next: (response) => {
        this.properties = response.properties;
        this.totalProperties = response.total;
        this.totalPages = response.total_pages;
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error searching properties:', error);
        this.isLoading = false;
      }
    });
  }

  /**
   * Apply filters and search
   */
  applyFilters(): void {
    this.currentPage = 1;
    this.searchProperties();
  }

  /**
   * Reset all filters
   */
  resetFilters(): void {
    this.searchFilters = {
      status: 'active',
      sort_by: 'newest',
      page: 1,
      per_page: 12
    };
    this.currentPage = 1;
    this.searchProperties();
  }

  /**
   * Change sort order
   */
  onSortChange(sortBy: string): void {
    this.searchFilters.sort_by = sortBy as any;
    this.currentPage = 1;
    this.searchProperties();
  }

  /**
   * Search by text
   */
  onSearchTextChange(searchText: string): void {
    this.searchFilters.search = searchText || undefined;
    this.currentPage = 1;
    this.searchProperties();
  }

  /**
   * Pagination
   */
  goToPage(page: number): void {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.searchProperties();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }

  previousPage(): void {
    this.goToPage(this.currentPage - 1);
  }

  nextPage(): void {
    this.goToPage(this.currentPage + 1);
  }

  /**
   * Toggle filter panel
   */
  toggleFilters(): void {
    this.showFilters = !this.showFilters;
  }

  /**
   * Toggle view mode
   */
  toggleViewMode(): void {
    this.viewMode = this.viewMode === 'grid' ? 'list' : 'grid';
  }

  /**
   * Get page numbers for pagination
   */
  getPageNumbers(): number[] {
    const pages: number[] = [];
    const maxVisible = 5;
    let start = Math.max(1, this.currentPage - Math.floor(maxVisible / 2));
    let end = Math.min(this.totalPages, start + maxVisible - 1);

    if (end - start < maxVisible - 1) {
      start = Math.max(1, end - maxVisible + 1);
    }

    for (let i = start; i <= end; i++) {
      pages.push(i);
    }

    return pages;
  }

  /**
   * Format price with currency
   */
  formatPrice(price: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(price);
  }
}