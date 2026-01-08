import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment.development';

export interface UploadResponse {
  message: string;
  url: string;
  filename: string;
}

export interface MultipleUploadResponse {
  message: string;
  files: Array<{
    original_name: string;
    url: string;
    filename: string;
  }>;
  errors?: string[];
}

export interface DeleteFileResponse {
  message: string;
}

@Injectable({
  providedIn: 'root'
})
export class UploadService {
  private API_URL = `${environment.apiUrl}/upload`;

  constructor(private http: HttpClient) {}

  // Upload single image
  uploadImage(file: File): Observable<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<UploadResponse>(`${this.API_URL}/image`, formData);
  }

  // Upload single video
  uploadVideo(file: File): Observable<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<UploadResponse>(`${this.API_URL}/video`, formData);
  }

  // Upload multiple images
  uploadMultipleImages(files: File[]): Observable<MultipleUploadResponse> {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });
    return this.http.post<MultipleUploadResponse>(`${this.API_URL}/images/multiple`, formData);
  }

  // Delete file
  deleteFile(url: string): Observable<DeleteFileResponse> {
    return this.http.delete<DeleteFileResponse>(`${this.API_URL}/delete`, {
      body: { url }
    });
  }

  // Validate file size
  validateFileSize(file: File, maxSizeMB: number): boolean {
    const maxSizeBytes = maxSizeMB * 1024 * 1024;
    return file.size <= maxSizeBytes;
  }

  // Validate file type
  validateImageType(file: File): boolean {
    const allowedTypes = ['image/png', 'image/jpg', 'image/jpeg', 'image/gif', 'image/webp'];
    return allowedTypes.includes(file.type);
  }

  // Validate video type
  validateVideoType(file: File): boolean {
    const allowedTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/wmv', 'video/webm'];
    return allowedTypes.includes(file.type);
  }
}