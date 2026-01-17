import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { AdminService, DashboardStats } from '../../services/admin.service';

@Component({
  selector: 'app-admin-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './admin-dashboard.html',
  styleUrls: ['./admin-dashboard.css']
})
export class AdminDashboardComponent implements OnInit {
  stats: DashboardStats | null = null;
  recentActivity: any = null;
  isLoading = true;
  errorMessage = '';

  constructor(
    private adminService: AdminService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadDashboard();
  }

  loadDashboard(): void {
    this.isLoading = true;

    // Load stats
    this.adminService.getDashboardStats().subscribe({
      next: (stats) => {
        this.stats = stats;
        this.isLoading = false;
      },
      error: (error) => {
        this.errorMessage = 'Failed to load dashboard';
        this.isLoading = false;
        console.error('Error:', error);
      }
    });

    // Load recent activity
    this.adminService.getRecentActivity().subscribe({
      next: (activity) => {
        this.recentActivity = activity;
      },
      error: (error) => {
        console.error('Error loading activity:', error);
      }
    });
  }

  navigateToUsers(): void {
    this.router.navigate(['/admin/users']);
  }

  navigateToModeration(): void {
    this.router.navigate(['/admin/moderation']);
  }

  getRoleCount(role: string): number {
    if (!this.stats) return 0;
    const roleData = this.stats.users.by_role.find(r => r._id === role);
    return roleData ? roleData.count : 0;
  }

  getStatusCount(type: 'properties' | 'bookings', status: string): number {
    if (!this.stats) return 0;
    const array = type === 'properties' ? this.stats.properties.by_status : this.stats.bookings.by_status;
    const statusData = array.find(s => s._id === status);
    return statusData ? statusData.count : 0;
  }
}