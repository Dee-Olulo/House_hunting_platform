import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { PropertyService, Property } from '../../services/property.service';
import { UploadService } from '../../services/upload.service';

// ✅ NEW: Interface for image preview
interface ImagePreview {
  file: File;
  previewUrl: string;
}

@Component({
  selector: 'app-add-property',
  standalone: true,
  imports: [CommonModule, FormsModule],
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
    latitude: 0,
    longitude: 0,
    price: 0,
    bedrooms: 0,
    bathrooms: 0,
    area_sqft: 0,
    images: [],
    videos: [],
    amenities: []
  };

  // ✅ FIXED: Store ImagePreview instead of just File
  selectedImages: ImagePreview[] = [];
  uploadedImageUrls: string[] = [];
  selectedAmenities: string[] = [];
  
  isLoading = false;
  isUploading = false;
  errorMessage = '';
  
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

  // ✅ FIXED: Generate preview URLs for images
  onImageSelect(event: any): void {
    const files = Array.from(event.target.files) as File[];
    
    // Validate files
    const validFiles = files.filter(file => {
      if (!this.uploadService.validateImageType(file)) {
        alert(`${file.name} is not a valid image type`);
        return false;
      }
      if (!this.uploadService.validateFileSize(file, 5)) {
        alert(`${file.name} exceeds 5MB limit`);
        return false;
      }
      return true;
    });

    if (this.selectedImages.length + validFiles.length > 20) {
      alert('Maximum 20 images allowed');
      return;
    }

    // ✅ FIXED: Create preview URLs using FileReader
    validFiles.forEach(file => {
      const reader = new FileReader();
      reader.onload = (e: any) => {
        this.selectedImages.push({
          file: file,
          previewUrl: e.target.result
        });
      };
      reader.readAsDataURL(file);
    });
  }

  // ✅ FIXED: Remove image from preview array
  removeImage(index: number): void {
    this.selectedImages.splice(index, 1);
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

  // ✅ FIXED: Extract actual File objects from ImagePreview array
  async uploadImages(): Promise<string[]> {
    if (this.selectedImages.length === 0) {
      return [];
    }

    this.isUploading = true;
    
    try {
      // Extract File objects from ImagePreview array
      const files = this.selectedImages.map(img => img.file);
      
      const response = await this.uploadService.uploadMultipleImages(files).toPromise();
      this.isUploading = false;
      
      if (response && response.files) {
        return response.files.map(file => file.url);
      }
      return [];
    } catch (error) {
      this.isUploading = false;
      console.error('Error uploading images:', error);
      throw error;
    }
  }

  async onSubmit(): Promise<void> {
    if (this.isLoading || this.isUploading) return;

    this.errorMessage = '';
    this.isLoading = true;

    try {
      // Upload images first
      if (this.selectedImages.length > 0) {
        const imageUrls = await this.uploadImages();
        this.uploadedImageUrls = [...this.uploadedImageUrls, ...imageUrls];
        // Clear selected images after successful upload
        this.selectedImages = [];
      }

      // Prepare property data
      const propertyData: Property = {
        ...this.property,
        images: this.uploadedImageUrls,
        amenities: this.selectedAmenities,
        latitude: this.property.latitude || undefined,
        longitude: this.property.longitude || undefined
      };

      // Create property
      this.propertyService.createProperty(propertyData).subscribe({
        next: (response) => {
          console.log('Property created:', response);
          this.isLoading = false;
          alert('Property created successfully!');
          this.router.navigate(['/landlord/properties']);
        },
        error: (error) => {
          console.error('Error creating property:', error);
          this.isLoading = false;
          this.errorMessage = error.error?.error || 'Failed to create property';
        }
      });

    } catch (error) {
      console.error('Error in form submission:', error);
      this.isLoading = false;
      this.errorMessage = 'Failed to upload images';
    }
  }

  cancel(): void {
    if (confirm('Are you sure you want to cancel? All unsaved changes will be lost.')) {
      this.router.navigate(['/landlord/properties']);
    }
  }
}