export interface Booking {
  _id?: string;
  property_id: string;
  tenant_id: string;
  landlord_id: string;
  booking_type: 'viewing' | 'rental_inquiry';
  booking_date: string; // YYYY-MM-DD
  booking_time: string; // HH:MM
  status: 'pending' | 'confirmed' | 'rejected' | 'completed' | 'cancelled';
  
  // Tenant information
  tenant_name: string;
  tenant_email: string;
  tenant_phone?: string;
  
  // Additional details
  message?: string;
  notes?: string; // Landlord's internal notes
  
  // Reasons
  cancellation_reason?: string;
  rejection_reason?: string;
  
  // Timestamps
  created_at?: string;
  updated_at?: string;
  confirmed_at?: string;
  completed_at?: string;
  cancelled_at?: string;
  
  // Enriched data from API
  property_details?: {
    title: string;
    address: string;
    city: string;
    state?: string;
    price: number;
    bedrooms?: number;
    bathrooms?: number;
    images?: string[];
  };
  
  tenant_details?: {
    email: string;
    role: string;
  };
  
  landlord_contact?: {
    name?: string;
    email: string;
    phone?: string;
  };
}

export interface CreateBookingRequest {
  property_id: string;
  booking_type: 'viewing' | 'rental_inquiry';
  booking_date: string;
  booking_time: string;
  tenant_name: string;
  tenant_email: string;
  tenant_phone?: string;
  message?: string;
}

export interface BookingResponse {
  bookings: Booking[];
  count: number;
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface BookingStatistics {
  status_breakdown: Array<{
    _id: string;
    count: number;
  }>;
  booking_type_breakdown?: Array<{
    _id: string;
    count: number;
  }>;
  top_properties?: Array<{
    _id: string;
    property_title: string;
    property_address: string;
    count: number;
  }>;
  recent_bookings_count: number;
  pending_bookings_count?: number;
  upcoming_bookings_count?: number;
}

export interface BookingFilters {
  status?: string;
  property_id?: string;
  booking_type?: string;
  from_date?: string;
  to_date?: string;
  page?: number;
  per_page?: number;
}