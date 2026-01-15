

// import { Injectable } from '@angular/core';
// import { HttpClient } from '@angular/common/http';
// import { Observable } from 'rxjs';
// import { environment } from '../../environments/environment.development';

// // Match backend response format
// export interface UploadResponse {
//   message: string;
//   files: Array<{
//     original_name: string;
//     url: string;
//     filename: string;
//   }>;
//   errors?: string[];
// }

// export interface SingleUploadResponse {
//   message: string;
//   url: string;
//   filename: string;
// }

// @Injectable({
//   providedIn: 'root'
// })
// export class UploadService {
//   private API_URL = `${environment.apiUrl}/upload`;

//   constructor(private http: HttpClient) {
//     console.log('UploadService initialized. API URL:', this.API_URL);
//   }

//   // Upload multiple images - MATCHES BACKEND
//   uploadMultipleImages(files: File[]): Observable<UploadResponse> {
//     console.log('📤 UploadService.uploadMultipleImages called');
//     console.log(`   Files count: ${files.length}`);
//     console.log(`   Files array:`, files);
//     console.log(`   API endpoint: ${this.API_URL}/images/multiple`);
    
//     const formData = new FormData();
    
//     // Backend expects field name 'files' (plural)
//     files.forEach((file, index) => {
//       console.log(`   Processing file ${index + 1}:`, {
//         name: file.name,
//         size: file.size,
//         type: file.type,
//         lastModified: file.lastModified
//       });
      
//       // Append file WITHOUT the third parameter (filename)
//       // This is critical for Flask to recognize the file
//       formData.append('files', file);
//     });

//     // Debug: Check FormData contents
//     console.log('📤 FormData entries:');
//     for (let pair of (formData as any).entries()) {
//       console.log('   ', pair[0], ':', pair[1]);
//     }

//     console.log('📤 Sending POST request...');
    
//     // CRITICAL: Don't set any headers - let browser handle it
//     return this.http.post<UploadResponse>(
//       `${this.API_URL}/images/multiple`,
//       formData
//       // No headers here!
//     );
//   }

//   // Upload single image - MATCHES BACKEND
//   uploadSingleImage(file: File): Observable<SingleUploadResponse> {
//     const formData = new FormData();
//     formData.append('file', file, file.name); // Backend expects 'file' for single upload
    
//     return this.http.post<SingleUploadResponse>(
//       `${this.API_URL}/image`,
//       formData
//     );
//   }

//   // Upload video - MATCHES BACKEND
//   uploadVideo(file: File): Observable<SingleUploadResponse> {
//     const formData = new FormData();
//     formData.append('file', file, file.name); // Backend expects 'file'
    
//     return this.http.post<SingleUploadResponse>(
//       `${this.API_URL}/video`,
//       formData
//     );
//   }

//   // Delete file - MATCHES BACKEND
//   deleteFile(fileUrl: string): Observable<any> {
//     return this.http.delete(`${this.API_URL}/delete`, {
//       body: { url: fileUrl }
//     });
//   }

//   // Validate image type
//   validateImageType(file: File): boolean {
//     const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
//     const isValid = validTypes.includes(file.type);
    
//     if (!isValid) {
//       console.warn(`❌ Invalid file type: ${file.type} for file: ${file.name}`);
//     }
    
//     return isValid;
//   }

//   // Validate file size (in MB)
//   validateFileSize(file: File, maxSizeMB: number): boolean {
//     const maxSizeBytes = maxSizeMB * 1024 * 1024;
//     const isValid = file.size <= maxSizeBytes;
    
//     if (!isValid) {
//       console.warn(`❌ File too large: ${file.name} is ${file.size} bytes (max: ${maxSizeBytes} bytes)`);
//     }
    
//     return isValid;
//   }

//   // Get full image URL
//   getImageUrl(path: string): string {
//     if (!path) return '';
//     if (path.startsWith('http')) return path;
    
//     // If path starts with /uploads, use it as-is
//     if (path.startsWith('/uploads')) {
//       return `${environment.apiUrl}${path}`;
//     }
    
//     // Otherwise prepend /uploads
//     return `${environment.apiUrl}/uploads/${path}`;
//   }
// }
import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
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
  private apiUrl = `${environment.apiUrl}/upload`;

  constructor(private http: HttpClient) {
    console.log('UploadService initialized. API URL:', this.apiUrl);
  }

  // Get auth headers
  private getAuthHeaders(): HttpHeaders {
    const token = localStorage.getItem('token');
    return new HttpHeaders({
      'Authorization': token ? `Bearer ${token}` : ''
    });
  }

  // Upload multiple images - MATCHES BACKEND
  uploadMultipleImages(files: File[]): Observable<UploadResponse> {
    console.log('📤 UploadService.uploadMultipleImages called');
    console.log(`   Files count: ${files.length}`);
    console.log(`   Files array:`, files);
    console.log(`   API endpoint: ${this.apiUrl}/images/multiple`);
    
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
    
    // CRITICAL: Don't set Content-Type header - let browser handle it
    return this.http.post<UploadResponse>(
      `${this.apiUrl}/images/multiple`,
      formData,
      { headers: this.getAuthHeaders() }
    );
  }

  // Upload single image - MATCHES BACKEND
  uploadSingleImage(file: File): Observable<SingleUploadResponse> {
    const formData = new FormData();
    formData.append('file', file, file.name); // Backend expects 'file' for single upload
    
    return this.http.post<SingleUploadResponse>(
      `${this.apiUrl}/image`,
      formData,
      { headers: this.getAuthHeaders() }
    );
  }

  // Upload multiple videos - FIXED TO MATCH BACKEND
  uploadMultipleVideos(files: File[]): Observable<UploadResponse> {
    console.log('📹 UploadService.uploadMultipleVideos called');
    console.log(`   Files count: ${files.length}`);
    console.log(`   API endpoint: ${this.apiUrl}/videos/multiple`);
    
    const formData = new FormData();
    
    // Backend expects field name 'files' (plural) - same as images
    files.forEach((file, index) => {
      console.log(`   Processing video ${index + 1}:`, {
        name: file.name,
        size: file.size,
        type: file.type
      });
      
      // Append WITHOUT the third parameter, just like images
      formData.append('files', file);
    });

    console.log('📹 Sending POST request to /videos/multiple...');

    // FIXED: Changed from /debug to /videos/multiple
    return this.http.post<UploadResponse>(
      `${this.apiUrl}/videos/multiple`,
      formData,
      { headers: this.getAuthHeaders() }
    );
  }

  // Upload single video - FIXED TO MATCH BACKEND
  uploadSingleVideo(file: File): Observable<SingleUploadResponse> {
    console.log('📹 UploadService.uploadSingleVideo called');
    console.log(`   File: ${file.name} (${file.size} bytes)`);
    
    const formData = new FormData();
    formData.append('file', file, file.name); // Backend expects 'file' for single upload
    
    // FIXED: Changed from /debug to /video
    return this.http.post<SingleUploadResponse>(
      `${this.apiUrl}/video`,
      formData,
      { headers: this.getAuthHeaders() }
    );
  }

  // Delete file - MATCHES BACKEND
  deleteFile(url: string, resourceType?: string): Observable<any> {
    // Extract public_id from Cloudinary URL if needed
    // For now, sending the full URL to backend
    return this.http.request('delete', `${this.apiUrl}/delete`, {
      headers: this.getAuthHeaders(),
      body: {
        url: url,
        resource_type: resourceType || 'image'
      }
    });
  }

  // Validate image type
  validateImageType(file: File): boolean {
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
    const isValid = validTypes.includes(file.type);
    
    if (!isValid) {
      console.warn(`❌ Invalid image type: ${file.type} for file: ${file.name}`);
    }
    
    return isValid;
  }

  // Validate video type
  validateVideoType(file: File): boolean {
    const validTypes = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/webm'];
    const isValid = validTypes.includes(file.type);
    
    if (!isValid) {
      console.warn(`❌ Invalid video type: ${file.type} for file: ${file.name}`);
    }
    
    return isValid;
  }

  // Validate file size (in MB)
  validateFileSize(file: File, maxSizeMB: number): boolean {
    const maxSizeBytes = maxSizeMB * 1024 * 1024;
    const isValid = file.size <= maxSizeBytes;
    
    if (!isValid) {
      console.warn(`❌ File too large: ${file.name} is ${(file.size / 1024 / 1024).toFixed(2)}MB (max: ${maxSizeMB}MB)`);
    }
    
    return isValid;
  }

  // Validate video size (default 100MB)
  validateVideoSize(file: File, maxSizeMB: number = 100): boolean {
    return this.validateFileSize(file, maxSizeMB);
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