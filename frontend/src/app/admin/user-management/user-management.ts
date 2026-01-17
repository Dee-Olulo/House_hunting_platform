// user-management.component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AdminService, User } from '../../services/admin.service';

@Component({
  selector: 'app-user-management',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './user-management.html',
  styleUrls: ['./user-management.css']
})
export class UserManagementComponent implements OnInit {
  users: User[] = [];
  isLoading = true;
  errorMessage = '';
  successMessage = '';

  // Filters
  selectedRole = '';
  searchQuery = '';
  sortBy = 'newest';

  // Pagination
  currentPage = 1;
  perPage = 20;
  totalUsers = 0;
  totalPages = 0;

  // Modal state
  showDeleteModal = false;
  showSuspendModal = false;
  selectedUser: User | null = null;
  suspendReason = '';

  constructor(
    private adminService: AdminService,
    public router: Router
  ) {}

  ngOnInit(): void {
    this.loadUsers();
  }

  loadUsers(): void {
    this.isLoading = true;
    this.errorMessage = '';

    const params: any = {
      page: this.currentPage,
      per_page: this.perPage,
      sort_by: this.sortBy
    };

    if (this.selectedRole) {
      params.role = this.selectedRole;
    }

    if (this.searchQuery) {
      params.search = this.searchQuery;
    }

    this.adminService.getAllUsers(params).subscribe({
      next: (response) => {
        this.users = response.users;
        this.totalUsers = response.total;
        this.totalPages = response.total_pages;
        this.isLoading = false;
      },
      error: (error) => {
        this.errorMessage = 'Failed to load users';
        this.isLoading = false;
        console.error('Error:', error);
      }
    });
  }

  onFilterChange(): void {
    this.currentPage = 1;
    this.loadUsers();
  }

  onSearch(): void {
    this.currentPage = 1;
    this.loadUsers();
  }

  clearSearch(): void {
    this.searchQuery = '';
    this.onSearch();
  }

  nextPage(): void {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
      this.loadUsers();
    }
  }

  previousPage(): void {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.loadUsers();
    }
  }

  viewUserDetails(userId: string): void {
    this.router.navigate(['/admin/users', userId]);
  }

  openSuspendModal(user: User): void {
    this.selectedUser = user;
    this.suspendReason = '';
    this.showSuspendModal = true;
  }

  closeSuspendModal(): void {
    this.showSuspendModal = false;
    this.selectedUser = null;
    this.suspendReason = '';
  }

  confirmSuspend(): void {
    if (!this.selectedUser || !this.suspendReason.trim()) {
      this.errorMessage = 'Please provide a suspension reason';
      return;
    }

    this.adminService.suspendUser(this.selectedUser._id, this.suspendReason).subscribe({
      next: () => {
        this.successMessage = 'User suspended successfully';
        this.closeSuspendModal();
        this.loadUsers();
        setTimeout(() => this.successMessage = '', 3000);
      },
      error: (error) => {
        this.errorMessage = error.error?.error || 'Failed to suspend user';
        console.error('Error:', error);
      }
    });
  }

  activateUser(user: User): void {
    if (!confirm(`Are you sure you want to activate ${user.email}?`)) {
      return;
    }

    this.adminService.activateUser(user._id).subscribe({
      next: () => {
        this.successMessage = 'User activated successfully';
        this.loadUsers();
        setTimeout(() => this.successMessage = '', 3000);
      },
      error: (error) => {
        this.errorMessage = error.error?.error || 'Failed to activate user';
        console.error('Error:', error);
      }
    });
  }

  openDeleteModal(user: User): void {
    this.selectedUser = user;
    this.showDeleteModal = true;
  }

  closeDeleteModal(): void {
    this.showDeleteModal = false;
    this.selectedUser = null;
  }

  confirmDelete(): void {
    if (!this.selectedUser) return;

    this.adminService.deleteUser(this.selectedUser._id).subscribe({
      next: () => {
        this.successMessage = 'User deleted successfully';
        this.closeDeleteModal();
        this.loadUsers();
        setTimeout(() => this.successMessage = '', 3000);
      },
      error: (error) => {
        this.errorMessage = error.error?.error || 'Failed to delete user';
        console.error('Error:', error);
      }
    });
  }

  getRoleBadgeClass(role: string): string {
    const classes: { [key: string]: string } = {
      'admin': 'badge-admin',
      'landlord': 'badge-landlord',
      'tenant': 'badge-tenant'
    };
    return classes[role] || 'badge-default';
  }
}