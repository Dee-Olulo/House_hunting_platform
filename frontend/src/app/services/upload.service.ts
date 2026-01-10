// import { Injectable } from '@angular/core';
// import { HttpClient } from '@angular/common/http';
// import { Observable } from 'rxjs';
// import { environment } from '../../environments/environment.development';

// export interface UploadResponse {
//   message: string;
//   files: Array<{
//     original_name: string;
//   url: string;
//   filename: string;
// }>;
// }

// export interface MultipleUploadResponse {
//   message: string;
//   files: Array<{
//     original_name: string;
//     url: string;
//     filename: string;
//   }>;
//   errors?: string[];
// }

// export interface DeleteFileResponse {
//   message: string;
// }

// @Injectable({
//   providedIn: 'root'
// })
// export class UploadService {
//   private API_URL = `${environment.apiUrl}/upload`;

//   constructor(private http: HttpClient) {}

//   // Upload single image
//   uploadImage(file: File): Observable<UploadResponse> {
//     const formData = new FormData();
//     formData.append('file', file);
//     return this.http.post<UploadResponse>(`${this.API_URL}/image`, formData);
//   }

//   // Upload single video
//   uploadVideo(file: File): Observable<UploadResponse> {
//     const formData = new FormData();
//     formData.append('file', file);
//     return this.http.post<UploadResponse>(`${this.API_URL}/video`, formData);
//   }

//   // Upload multiple images
//   uploadMultipleImages(files: File[]): Observable<MultipleUploadResponse> {
//     const formData = new FormData();
//     files.forEach(file => {
//       formData.append('files', file);
//     });
//     return this.http.post<MultipleUploadResponse>(`${this.API_URL}/images/multiple`, formData);
//   }

//   // Delete file
//   deleteFile(url: string): Observable<DeleteFileResponse> {
//     return this.http.delete<DeleteFileResponse>(`${this.API_URL}/delete`, {
//       body: { url }
//     });
//   }

//   // Validate file size
//   validateFileSize(file: File, maxSizeMB: number): boolean {
//     const maxSizeBytes = maxSizeMB * 1024 * 1024;
//     return file.size <= maxSizeBytes;
//   }

//   // Validate file type
//   validateImageType(file: File): boolean {
//     const allowedTypes = ['image/png', 'image/jpg', 'image/jpeg', 'image/gif', 'image/webp'];
//     return allowedTypes.includes(file.type);
//   }

//   // Validate video type
//   validateVideoType(file: File): boolean {
//     const allowedTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/wmv', 'video/webm'];
//     return allowedTypes.includes(file.type);
//   }
// }

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment.development';

// Match backend response format
export interface UploadResponse {
  message: string;
  files: Array<{
    original_name: string;
    url: string;
    filename: string;
  }>;
  errors?: string[];
}

export interface SingleUploadResponse {
  message: string;
  url: string;
  filename: string;
}

@Injectable({
  providedIn: 'root'
})
export class UploadService {
  private API_URL = `${environment.apiUrl}/upload`;

  constructor(private http: HttpClient) {
    console.log('UploadService initialized. API URL:', this.API_URL);
  }

  // Upload multiple images - MATCHES BACKEND
  uploadMultipleImages(files: File[]): Observable<UploadResponse> {
    console.log('📤 UploadService.uploadMultipleImages called');
    console.log(`   Files count: ${files.length}`);
    console.log(`   Files array:`, files);
    console.log(`   API endpoint: ${this.API_URL}/images/multiple`);
    
    const formData = new FormData();
    
    // Backend expects field name 'files' (plural)
    files.forEach((file, index) => {
      console.log(`   Processing file ${index + 1}:`, {
        name: file.name,
        size: file.size,
        type: file.type,
        lastModified: file.lastModified
      });
      
      // Append file WITHOUT the third parameter (filename)
      // This is critical for Flask to recognize the file
      formData.append('files', file);
    });

    // Debug: Check FormData contents
    console.log('📤 FormData entries:');
    for (let pair of (formData as any).entries()) {
      console.log('   ', pair[0], ':', pair[1]);
    }

    console.log('📤 Sending POST request...');
    
    // CRITICAL: Don't set any headers - let browser handle it
    return this.http.post<UploadResponse>(
      `${this.API_URL}/images/multiple`,
      formData
      // No headers here!
    );
  }

  // Upload single image - MATCHES BACKEND
  uploadSingleImage(file: File): Observable<SingleUploadResponse> {
    const formData = new FormData();
    formData.append('file', file, file.name); // Backend expects 'file' for single upload
    
    return this.http.post<SingleUploadResponse>(
      `${this.API_URL}/image`,
      formData
    );
  }

  // Upload video - MATCHES BACKEND
  uploadVideo(file: File): Observable<SingleUploadResponse> {
    const formData = new FormData();
    formData.append('file', file, file.name); // Backend expects 'file'
    
    return this.http.post<SingleUploadResponse>(
      `${this.API_URL}/video`,
      formData
    );
  }

  // Delete file - MATCHES BACKEND
  deleteFile(fileUrl: string): Observable<any> {
    return this.http.delete(`${this.API_URL}/delete`, {
      body: { url: fileUrl }
    });
  }

  // Validate image type
  validateImageType(file: File): boolean {
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
    const isValid = validTypes.includes(file.type);
    
    if (!isValid) {
      console.warn(`❌ Invalid file type: ${file.type} for file: ${file.name}`);
    }
    
    return isValid;
  }

  // Validate file size (in MB)
  validateFileSize(file: File, maxSizeMB: number): boolean {
    const maxSizeBytes = maxSizeMB * 1024 * 1024;
    const isValid = file.size <= maxSizeBytes;
    
    if (!isValid) {
      console.warn(`❌ File too large: ${file.name} is ${file.size} bytes (max: ${maxSizeBytes} bytes)`);
    }
    
    return isValid;
  }

  // Get full image URL
  getImageUrl(path: string): string {
    if (!path) return '';
    if (path.startsWith('http')) return path;
    
    // If path starts with /uploads, use it as-is
    if (path.startsWith('/uploads')) {
      return `${environment.apiUrl}${path}`;
    }
    
    // Otherwise prepend /uploads
    return `${environment.apiUrl}/uploads/${path}`;
  }
}