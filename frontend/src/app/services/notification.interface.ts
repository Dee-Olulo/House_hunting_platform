export interface Notification {
  _id: string;
  user_id: string;
  notification_type: 
    | 'booking_confirmed'
    | 'booking_rejected'
    | 'booking_cancelled'
    | 'new_booking'
    | 'booking_reminder'
    | 'property_expiring'
    | 'welcome';
  title: string;
  message: string;
  link?: string;
  data?: {
    booking_id?: string;
    property_id?: string;
    tenant_id?: string;
    days_remaining?: number;
    [key: string]: any;
  };
  is_read: boolean;
  read_at?: string;
  created_at: string;
  expires_at?: string;
}

export interface NotificationResponse {
  notifications: Notification[];
  count: number;
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface NotificationStatistics {
  total_notifications: number;
  unread_count: number;
  read_count: number;
  by_type: Array<{
    _id: string;
    count: number;
  }>;
  recent_count: number;
}

export interface NotificationFilters {
  is_read?: boolean;
  type?: string;
  page?: number;
  per_page?: number;
}