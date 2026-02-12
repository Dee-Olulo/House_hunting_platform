/**
 * services/listing-confirmation.service.ts
 * ─────────────────────────────────────────
 * Wraps the /listing-confirmation/* Flask endpoints.
 * Injected into PropertiesComponent so each property card can show
 * its confirmation countdown and let the landlord confirm in one tap.
 */

import { Injectable }            from '@angular/core';
import { HttpClient }            from '@angular/common/http';
import { Observable }            from 'rxjs';
import { environment }           from '../../environments/environment';   // adjust path if needed


export interface ConfirmationStatus {
  property_id:            string;
  status:                 string;         // 'active' | 'inactive' …
  last_confirmed:         string | null;  // ISO-8601
  days_since_confirmed:   number;
  days_until_reminder:    number;
  confirmation_pending:   boolean;
  will_deactivate_in:     number;         // days until auto-deactivation
}

export interface PendingProperty {
  _id:                    string;
  title:                  string;
  city:                   string;
  state:                  string;
  last_confirmed:         string | null;
  days_since_confirmed:   number;
  images:                 string[];
}

export interface ConfirmationLog {
  _id:            string;
  property_id:    string;
  landlord_id:    string;
  action:         string;   // reminder_early | reminder | warning | deactivated | confirmed
  detail:         string | null;
  timestamp:      string;
}


@Injectable({ providedIn: 'root' })
export class ListingConfirmationService {

  private readonly baseUrl = `${environment.apiUrl}/listing-confirmation`;

  constructor(private http: HttpClient) {}

  // ── confirm a listing ──────────────────────────────────────────────────
  confirmListing(propertyId: string): Observable<{ message: string; property_id: string; confirmed_at: string }> {
    return this.http.post<any>(`${this.baseUrl}/${propertyId}/confirm`, {});
  }

  // ── get confirmation status for one property ──────────────────────────
  getConfirmationStatus(propertyId: string): Observable<ConfirmationStatus> {
    return this.http.get<ConfirmationStatus>(`${this.baseUrl}/${propertyId}/status`);
  }

  // ── get all pending properties for the current landlord ───────────────
  getPendingProperties(): Observable<{ pending_properties: PendingProperty[]; count: number }> {
    return this.http.get<any>(`${this.baseUrl}/pending`);
  }

  // ── admin: get confirmation audit logs ─────────────────────────────────
  getConfirmationLogs(page = 1, perPage = 20, action?: string): Observable<{ logs: ConfirmationLog[]; total: number; total_pages: number }> {
    let params: any = { page, per_page: perPage };
    if (action) params.action = action;
    return this.http.get<any>(`${this.baseUrl}/logs`, { params });
  }
}