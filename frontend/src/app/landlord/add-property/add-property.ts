// src/app/landlord/add-property/add-property.component.ts

import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { PropertyService, Property } from '../../services/property.service';
import { UploadService } from '../../services/upload.service';
import { LocationPickerComponent, LocationData } from '../location-picker/location-picker.component';

@Component({
  selector: 'app-add-property',
  standalone: true,
  imports: [CommonModule, FormsModule, LocationPickerComponent],
  templateUrl: './add-property.html',
  styleUrls: ['./add-property.css']
})
export class AddPropertyComponent {
  property: Property = {
    title: '',
    description: '',
    property_type: '',
    address: '',
    city: '',
    state: '',
    zip_code: '',
    country: 'Kenya',
    latitude: undefined,
    longitude: undefined,
    price: 0,
    bedrooms: 0,
    bathrooms: 0,
    area_sqft: 0,
    images: [],
    videos: [],
    amenities: []
  };

  // Image properties
  selectedImages: File[] = [];
  selectedImagePreviews: string[] = [];
  uploadedImageUrls: string[] = [];
  
  // Video properties (NEW)
  selectedVideos: File[] = [];
  videoPreviewUrls: string[] = [];
  uploadedVideoUrls: string[] = [];
  
  // Other properties
  selectedAmenities: string[] = [];
  locationData: LocationData = {
    latitude: null,
    longitude: null,
    address: '',
    city: '',
    state: '',
    country: ''
  };
  
  isLoading = false;
  isUploading = false;
  errorMessage = '';
  successMessage = '';
  
  propertyTypes = ['apartment', 'house', 'studio', 'condo', 'townhouse', 'villa'];
  
  availableAmenities = [
    'parking', 'wifi', 'security', 'gym', 'pool', 
    'garden', 'backup_generator', 'water', 'elevator',
    'balcony', 'furnished', 'pet_friendly'
  ];

  constructor(
    private propertyService: PropertyService,
    private uploadService: UploadService,
    private router: Router
  ) {}

  // ============================================
  // IMAGE HANDLING
  // ============================================
  
  onImageSelect(event: any): void {
    console.log('📸 onImageSelect triggered');
    const files = Array.from(event.target.files) as File[];
    
    if (!files || files.length === 0) {
      console.log('❌ No files detected');
      return;
    }

    // Validate files
    const validFiles = files.filter(file => {
      console.log(`Validating file: ${file.name}`);
      
      if (!this.uploadService.validateImageType(file)) {
        this.errorMessage = `${file.name} is not a valid image type`;
        setTimeout(() => this.errorMessage = '', 3000);
        return false;
      }
      if (!this.uploadService.validateFileSize(file, 5)) {
        this.errorMessage = `${file.name} exceeds 5MB limit`;
        setTimeout(() => this.errorMessage = '', 3000);
        return false;
      }
      return true;
    });

    if (this.selectedImages.length + validFiles.length > 20) {
      this.errorMessage = 'Maximum 20 images allowed';
      setTimeout(() => this.errorMessage = '', 3000);
      return;
    }

    // Generate preview URLs
    validFiles.forEach(file => {
      const reader = new FileReader();
      reader.onload = (e: any) => {
        this.selectedImagePreviews.push(e.target.result);
      };
      reader.readAsDataURL(file);
    });

    this.selectedImages = [...this.selectedImages, ...validFiles];
    console.log(`✅ Total selected images: ${this.selectedImages.length}`);
    
    event.target.value = '';
  }

  removeImage(index: number): void {
    this.selectedImages.splice(index, 1);
    this.selectedImagePreviews.splice(index, 1);
  }

  removeUploadedImage(index: number): void {
    const url = this.uploadedImageUrls[index];
    this.uploadService.deleteFile(url).subscribe({
      next: () => {
        this.uploadedImageUrls.splice(index, 1);
      },
      error: (error) => {
        console.error('Error deleting image:', error);
      }
    });
  }

  async uploadImages(): Promise<string[]> {
    if (this.selectedImages.length === 0) {
      console.log('⚠️ No images to upload');
      return [];
    }

    console.log(`📤 Starting upload of ${this.selectedImages.length} images...`);
    this.isUploading = true;
    
    try {
      const response = await this.uploadService.uploadMultipleImages(this.selectedImages).toPromise();
      this.isUploading = false;
      
      if (response && response.files) {
        const urls = response.files.map((file: any) => file.url);
        console.log('✅ Images uploaded:', urls);
        return urls;
      }
      
      return [];
    } catch (error: any) {
      this.isUploading = false;
      console.error('❌ Upload error:', error);
      
      if (error.status === 401) {
        throw new Error('Authentication failed. Please log in again.');
      } else if (error.status === 400) {
        throw new Error(`Upload failed: ${error.error?.error || 'Invalid request'}`);
      } else if (error.status === 413) {
        throw new Error('Files too large. Maximum size is 5MB per image.');
      }
      
      throw new Error(error.error?.message || 'Failed to upload images');
    }
  }

  // ============================================
  // VIDEO HANDLING (NEW)
  // ============================================
  
  onVideoSelect(event: any): void {
    console.log('🎥 onVideoSelect triggered');
    const files = Array.from(event.target.files) as File[];
    
    if (!files || files.length === 0) {
      console.log('❌ No files detected');
      return;
    }

    // Validate files
    const validFiles = files.filter(file => {
      console.log(`Validating video: ${file.name}`);
      
      if (!this.uploadService.validateVideoType(file)) {
        this.errorMessage = `${file.name} is not a valid video type. Accepted: MP4, MOV, AVI, WEBM`;
        setTimeout(() => this.errorMessage = '', 3000);
        return false;
      }
      if (!this.uploadService.validateVideoSize(file, 100)) {
        this.errorMessage = `${file.name} exceeds 100MB limit`;
        setTimeout(() => this.errorMessage = '', 3000);
        return false;
      }
      return true;
    });

    if (this.selectedVideos.length + validFiles.length > 5) {
      this.errorMessage = 'Maximum 5 videos allowed';
      setTimeout(() => this.errorMessage = '', 3000);
      return;
    }

    // Generate preview URLs
    validFiles.forEach(file => {
      const reader = new FileReader();
      reader.onload = (e: any) => {
        this.videoPreviewUrls.push(e.target.result);
      };
      reader.readAsDataURL(file);
    });

    this.selectedVideos = [...this.selectedVideos, ...validFiles];
    console.log(`✅ Total selected videos: ${this.selectedVideos.length}`);
    
    event.target.value = '';
  }

  removeVideo(index: number): void {
    this.selectedVideos.splice(index, 1);
    this.videoPreviewUrls.splice(index, 1);
  }

  removeUploadedVideo(index: number): void {
    const url = this.uploadedVideoUrls[index];
    this.uploadService.deleteFile(url, 'video').subscribe({
      next: () => {
        this.uploadedVideoUrls.splice(index, 1);
      },
      error: (error) => {
        console.error('Error deleting video:', error);
      }
    });
  }

  async uploadVideos(): Promise<string[]> {
    if (this.selectedVideos.length === 0) {
      console.log('⚠️ No videos to upload');
      return [];
    }

    console.log(`📤 Starting upload of ${this.selectedVideos.length} videos...`);
    this.isUploading = true;
    
    try {
      const response = await this.uploadService.uploadMultipleVideos(this.selectedVideos).toPromise();
      this.isUploading = false;
      
      if (response && response.files) {
        const urls = response.files.map((file: any) => file.url);
        console.log('✅ Videos uploaded:', urls);
        return urls;
      }
      
      return [];
    } catch (error: any) {
      this.isUploading = false;
      console.error('❌ Video upload error:', error);
      
      if (error.status === 401) {
        throw new Error('Authentication failed. Please log in again.');
      } else if (error.status === 400) {
        throw new Error(`Upload failed: ${error.error?.error || 'Invalid request'}`);
      } else if (error.status === 413) {
        throw new Error('Video too large. Maximum size is 100MB per video.');
      }
      
      throw new Error(error.error?.message || 'Failed to upload videos');
    }
  }

  // ============================================
  // AMENITIES HANDLING
  // ============================================
  
  toggleAmenity(amenity: string): void {
    const index = this.selectedAmenities.indexOf(amenity);
    if (index > -1) {
      this.selectedAmenities.splice(index, 1);
    } else {
      this.selectedAmenities.push(amenity);
    }
  }

  isAmenitySelected(amenity: string): boolean {
    return this.selectedAmenities.includes(amenity);
  }

  // ============================================
  // LOCATION HANDLING
  // ============================================
  
  onLocationChange(location: LocationData): void {
    this.locationData = location;
    console.log('Location updated:', location);
  }

  // ============================================
  // FORM SUBMISSION
  // ============================================
  
  async onSubmit(): Promise<void> {
    console.log('🚀 Form submission started');
    
    if (this.isLoading || this.isUploading) {
      console.log('Already processing...');
      return;
    }

    this.errorMessage = '';
    this.successMessage = '';
    this.isLoading = true;

    try {
      // Upload images first
      if (this.selectedImages.length > 0) {
        console.log('📤 Uploading images...');
        const imageUrls = await this.uploadImages();
        this.uploadedImageUrls = [...this.uploadedImageUrls, ...imageUrls];
        this.selectedImages = [];
        this.selectedImagePreviews = [];
      }

      // Upload videos
      if (this.selectedVideos.length > 0) {
        console.log('📤 Uploading videos...');
        const videoUrls = await this.uploadVideos();
        this.uploadedVideoUrls = [...this.uploadedVideoUrls, ...videoUrls];
        this.selectedVideos = [];
        this.videoPreviewUrls = [];
      }

      // Prepare property data
      const propertyData: Property = {
        ...this.property,
        images: this.uploadedImageUrls,
        videos: this.uploadedVideoUrls, // Include videos
        amenities: this.selectedAmenities,
        latitude: this.locationData.latitude || this.property.latitude || undefined,
        longitude: this.locationData.longitude || this.property.longitude || undefined,
        address: this.locationData.address || this.property.address,
        city: this.locationData.city || this.property.city,
        state: this.locationData.state || this.property.state,
        country: this.locationData.country || this.property.country,
      };

      console.log('Creating property with data:', propertyData);

      // // Create property
      // this.propertyService.createProperty(propertyData).subscribe({
      //   next: (response) => {
      //     console.log('✅ Property created:', response);
      //     this.isLoading = false;
      //     this.successMessage = 'Property created successfully!';
          
      //     // Redirect after 1.5 seconds
      //     setTimeout(() => {
      //       this.router.navigate(['/landlord-dashboard']).catch(() => {
      //         this.router.navigate(['/landlord/properties']).catch(() => {
      //           this.router.navigate(['/']);
      //         });
      //       });
      //     }, 1500);
      //   },
      //   error: (error) => {
      //     console.error('❌ Error creating property:', error);
      //     this.isLoading = false;
      //     this.errorMessage = error.error?.error || error.error?.message || 'Failed to create property';
      //   }
      // });
       this.propertyService.createProperty(propertyData).subscribe({
      next: (response: any) => {
        console.log('✅ Property created:', response);
        this.isLoading = false;
        
        // Handle moderation response
        const moderation = response.moderation;
        
        if (moderation.status === 'approved') {
          this.successMessage = '✅ Property approved and published successfully!';
        } else if (moderation.status === 'pending_review') {
          this.successMessage = '⏳ Property submitted for review. We\'ll notify you once it\'s approved.';
        } else {
          this.errorMessage = `⚠️ Property needs improvement: ${moderation.issues.slice(0, 3).join(', ')}`;
          return;  // Don't redirect if rejected
        }
        
        // Show issues if any (even for approved)
        if (moderation.issues && moderation.issues.length > 0) {
          console.log('⚠️ Moderation issues:', moderation.issues);
        }
        
        // Redirect after 2 seconds
        setTimeout(() => {
          this.router.navigate(['/landlord-dashboard']).catch(() => {
            this.router.navigate(['/landlord/properties']).catch(() => {
              this.router.navigate(['/']);
            });
          });
        }, 2000);
      },
      error: (error) => {
        console.error('❌ Error creating property:', error);
        this.isLoading = false;
        this.errorMessage = error.error?.error || error.error?.message || 'Failed to create property';
      }
    });

    } catch (error: any) {
      console.error('❌ Error in form submission:', error);
      this.isLoading = false;
      this.errorMessage = error.message || 'Failed to upload media';
    }
  }

  cancel(): void {
    if (confirm('Are you sure you want to cancel? All unsaved changes will be lost.')) {
      this.router.navigate(['/landlord-dashboard']).catch(() => {
        this.router.navigate(['/dashboard']).catch(() => {
          this.router.navigate(['/']);
        });
      });
    }
  }
}
