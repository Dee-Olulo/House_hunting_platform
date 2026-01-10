// src/app/tenant/models/property.interface.ts

export interface Property {
  _id: string;
  landlord_id: string;
  title: string;
  description: string;
  property_type: string;
  address: string;
  city: string;
  state: string;
  zip_code: string;
  country: string;
  latitude?: number;
  longitude?: number;
  price: number;
  bedrooms: number;
  bathrooms: number;
  area_sqft: number;
  images: string[];
  videos: string[];
  amenities: string[];
  status: 'active' | 'inactive' | 'pending' | 'expired';
  is_featured: boolean;
  views: number;
  created_at: string;
  updated_at: string;
  last_confirmed_at?: string;
}

export interface PropertySearchParams {
  city?: string;
  state?: string;
  min_price?: number;
  max_price?: number;
  bedrooms?: number;
  bathrooms?: number;
  property_type?: string;
  status?: string;
  sort_by?: 'newest' | 'price_low' | 'price_high' | 'bedrooms';
  page?: number;
  per_page?: number;
  search?: string;
}

export interface PropertySearchResponse {
  properties: Property[];
  count: number;
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  filters_applied: PropertySearchParams;
}

export interface AdvancedSearchParams {
  city?: string;
  state?: string;
  country?: string;
  min_price?: number;
  max_price?: number;
  min_bedrooms?: number;
  max_bedrooms?: number;
  min_bathrooms?: number;
  min_area?: number;
  max_area?: number;
  property_types?: string[];
  amenities?: string[];
  search_text?: string;
  featured_only?: boolean;
  sort_by?: string;
  page?: number;
  per_page?: number;
}

export interface FilterOptions {
  cities: string[];
  states: string[];
  property_types: string[];
  price_range: {
    min_price: number;
    max_price: number;
  };
  bedroom_range: {
    min_bedrooms: number;
    max_bedrooms: number;
  };
  amenities: string[];
}