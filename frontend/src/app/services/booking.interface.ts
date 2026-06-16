/**
 * A booking record — represents a tenant's request to view or inquire
 * about renting a property. Includes core fields, status tracking,
 * lifecycle timestamps, and optional enriched data joined in by the API.
 */
export interface Booking {
  _id?: string;                                   // Server-assigned ID (absent before creation)
  property_id: string;
  tenant_id: string;
  landlord_id: string;
  booking_type: 'viewing' | 'rental_inquiry';     // Viewing appointment vs. rental inquiry
  booking_date: string;                           // Requested date, format YYYY-MM-DD
  booking_time: string;                           // Requested time, format HH:MM
  status: 'pending' | 'confirmed' | 'rejected' | 'completed' | 'cancelled';

  // Tenant information (captured at booking time)
  tenant_name: string;
  tenant_email: string;
  tenant_phone?: string;

  // Additional details
  message?: string;   // Optional message from the tenant
  notes?: string;     // Landlord's private internal notes

  // Reasons recorded when a booking is cancelled or rejected
  cancellation_reason?: string;
  rejection_reason?: string;

  // Lifecycle timestamps (set by the backend as the booking progresses)
  created_at?: string;
  updated_at?: string;
  confirmed_at?: string;
  completed_at?: string;
  cancelled_at?: string;

  // Enriched data joined in by the API for convenience (not stored on the booking itself)
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

  tenant_details?: {        // Extra tenant info resolved from the user record
    email: string;
    role: string;
  };

  landlord_contact?: {      // Landlord contact details, shown to the tenant
    name?: string;
    email: string;
    phone?: string;
  };
}

/**
 * Payload for creating a new booking.
 * IDs and timestamps are assigned by the backend, so only the
 * tenant-supplied fields are included here.
 */
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

/**
 * Paginated list response for booking queries.
 */
export interface BookingResponse {
  bookings: Booking[];
  count: number;        // Number of bookings in this page
  total: number;        // Total matching bookings across all pages
  page: number;         // Current page number
  per_page: number;     // Page size
  total_pages: number;  // Total number of pages
}

/**
 * Aggregated booking statistics for dashboards/reporting.
 * Several breakdowns are optional depending on the endpoint/scope.
 */
export interface BookingStatistics {
  status_breakdown: Array<{       // Counts grouped by status (_id = status name)
    _id: string;
    count: number;
  }>;
  booking_type_breakdown?: Array<{ // Counts grouped by booking type
    _id: string;
    count: number;
  }>;
  top_properties?: Array<{        // Most-booked properties
    _id: string;
    property_title: string;
    property_address: string;
    count: number;
  }>;
  recent_bookings_count: number;     // Bookings in the recent window
  pending_bookings_count?: number;   // Bookings awaiting confirmation
  upcoming_bookings_count?: number;  // Confirmed bookings still in the future
}

/**
 * Query parameters for filtering and paginating booking lists.
 * All fields are optional; omitted ones apply no filter.
 */
export interface BookingFilters {
  status?: string;
  property_id?: string;
  booking_type?: string;
  from_date?: string;   // Start of date range (inclusive), YYYY-MM-DD
  to_date?: string;     // End of date range (inclusive), YYYY-MM-DD
  page?: number;
  per_page?: number;
}