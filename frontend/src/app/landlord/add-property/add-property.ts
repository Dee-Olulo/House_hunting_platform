
// import { Component } from '@angular/core';
// import { CommonModule } from '@angular/common';
// import { FormsModule } from '@angular/forms';
// import { Router } from '@angular/router';
// import { PropertyService, Property } from '../../services/property.service';
// import { UploadService } from '../../services/upload.service';

// @Component({
//   selector: 'app-add-property',
//   standalone: true,
//   imports: [CommonModule, FormsModule],
//   templateUrl: './add-property.html',
//   styleUrls: ['./add-property.css']
// })
// export class AddPropertyComponent {
//   property: Property = {
//     title: '',
//     description: '',
//     property_type: '',
//     address: '',
//     city: '',
//     state: '',
//     zip_code: '',
//     country: 'Kenya',
//     latitude: undefined,
//     longitude: undefined,
//     price: 0,
//     bedrooms: 0,
//     bathrooms: 0,
//     area_sqft: 0,
//     images: [],
//     videos: [],
//     amenities: []
//   };

//   selectedImages: File[] = [];
//   uploadedImageUrls: string[] = [];
//   selectedAmenities: string[] = [];
  
//   isLoading = false;
//   isUploading = false;
//   errorMessage = '';
//   successMessage = '';
  
//   propertyTypes = ['apartment', 'house', 'studio', 'condo', 'townhouse', 'villa'];
  
//   availableAmenities = [
//     'parking', 'wifi', 'security', 'gym', 'pool', 
//     'garden', 'backup_generator', 'water', 'elevator',
//     'balcony', 'furnished', 'pet_friendly'
//   ];

//   constructor(
//     private propertyService: PropertyService,
//     private uploadService: UploadService,
//     private router: Router
//   ) {}

//   onImageSelect(event: any): void {
//     const files = Array.from(event.target.files) as File[];
    
//     // Validate files
//     const validFiles = files.filter(file => {
//       if (!this.uploadService.validateImageType(file)) {
//         alert(`${file.name} is not a valid image type`);
//         return false;
//       }
//       if (!this.uploadService.validateFileSize(file, 5)) {
//         alert(`${file.name} exceeds 5MB limit`);
//         return false;
//       }
//       return true;
//     });

//     if (this.selectedImages.length + validFiles.length > 20) {
//       alert('Maximum 20 images allowed');
//       return;
//     }

//     this.selectedImages = [...this.selectedImages, ...validFiles];
//   }

//   removeImage(index: number): void {
//     this.selectedImages.splice(index, 1);
//   }

//   removeUploadedImage(index: number): void {
//     const url = this.uploadedImageUrls[index];
//     this.uploadService.deleteFile(url).subscribe({
//       next: () => {
//         this.uploadedImageUrls.splice(index, 1);
//       },
//       error: (error) => {
//         console.error('Error deleting image:', error);
//       }
//     });
//   }

//   toggleAmenity(amenity: string): void {
//     const index = this.selectedAmenities.indexOf(amenity);
//     if (index > -1) {
//       this.selectedAmenities.splice(index, 1);
//     } else {
//       this.selectedAmenities.push(amenity);
//     }
//   }

//   isAmenitySelected(amenity: string): boolean {
//     return this.selectedAmenities.includes(amenity);
//   }

//   async uploadImages(): Promise<string[]> {
//     if (this.selectedImages.length === 0) {
//       return [];
//     }

//     this.isUploading = true;
    
//     try {
//       const response = await this.uploadService.uploadMultipleImages(this.selectedImages).toPromise();
//       this.isUploading = false;
      
//       if (response && response.files) {
//         return response.files.map(file => file.url);
//       }
//       return [];
//     } catch (error) {
//       this.isUploading = false;
//       console.error('Error uploading images:', error);
//       throw error;
//     }
//   }

//   async onSubmit(): Promise<void> {
//     if (this.isLoading || this.isUploading) return;

//     this.errorMessage = '';
//     this.isLoading = true;

//     try {
//       // Upload images first
//       if (this.selectedImages.length > 0) {
//         const imageUrls = await this.uploadImages();
//         this.uploadedImageUrls = [...this.uploadedImageUrls, ...imageUrls];
//       }

//       // Prepare property data
//       const propertyData: Property = {
//         ...this.property,
//         images: this.uploadedImageUrls,
//         amenities: this.selectedAmenities,
//         latitude: this.property.latitude || undefined,
//         longitude: this.property.longitude || undefined
//       };

//       // Create property
//       this.propertyService.createProperty(propertyData).subscribe({
//         next: (response) => {
//           console.log('Property created:', response);
//           this.isLoading = false;
//           alert('Property created successfully!');
//           this.router.navigate(['/landlord/properties']);
//         },
//         error: (error) => {
//           console.error('Error creating property:', error);
//           this.isLoading = false;
//           this.errorMessage = error.error?.error || 'Failed to create property';
//         }
//       });

//     } catch (error) {
//       console.error('Error in form submission:', error);
//       this.isLoading = false;
//       this.errorMessage = 'Failed to upload images';
//     }
//   }

//   cancel(): void {
//     if (confirm('Are you sure you want to cancel? All unsaved changes will be lost.')) {
//       this.router.navigate(['/landlord/properties']);
//     }
//   }
// }


import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { PropertyService, Property } from '../../services/property.service';
import { UploadService } from '../../services/upload.service';

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

  selectedImages: File[] = [];
  uploadedImageUrls: string[] = [];
  selectedAmenities: string[] = [];
  
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

  onImageSelect(event: any): void {
    console.log('📸 onImageSelect triggered');
    console.log('Event:', event);
    console.log('Event target:', event.target);
    console.log('Files from event:', event.target.files);
    
    const files = Array.from(event.target.files) as File[];
    
    console.log('Files array after conversion:', files);
    console.log('Files length:', files.length);
    
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
      console.log(`✅ File ${file.name} is valid`);
      return true;
    });

    console.log('Valid files count:', validFiles.length);

    if (this.selectedImages.length + validFiles.length > 20) {
      this.errorMessage = 'Maximum 20 images allowed';
      setTimeout(() => this.errorMessage = '', 3000);
      return;
    }

    this.selectedImages = [...this.selectedImages, ...validFiles];
    console.log(`✅ Total selected images: ${this.selectedImages.length}`);
    console.log('Selected images array:', this.selectedImages);
    
    // Reset the input so the same file can be selected again if needed
    event.target.value = '';
  }

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

  async uploadImages(): Promise<string[]> {
    if (this.selectedImages.length === 0) {
      console.log('⚠️ No images to upload');
      return [];
    }

    console.log(`📤 Starting upload of ${this.selectedImages.length} images...`);
    console.log('Images to upload:', this.selectedImages.map(f => ({
      name: f.name,
      size: f.size,
      type: f.type
    })));
    
    this.isUploading = true;
    
    try {
      console.log('Calling uploadService.uploadMultipleImages...');
      const response = await this.uploadService.uploadMultipleImages(this.selectedImages).toPromise();
      
      this.isUploading = false;
      console.log('✅ Upload response received:', response);
      
      if (response && response.files) {
        const urls = response.files.map(file => file.url);
        console.log('✅ Extracted URLs:', urls);
        return urls;
      }
      
      console.warn('⚠️ Response has no files array');
      return [];
    } catch (error: any) {
      this.isUploading = false;
      console.error('❌ Upload error details:');
      console.error('  Full error object:', error);
      console.error('  Status:', error.status);
      console.error('  Status Text:', error.statusText);
      console.error('  Error body:', error.error);
      console.error('  Message:', error.message);
      
      // Detailed error messages
      if (error.status === 401) {
        throw new Error('Authentication failed. Please log in again.');
      } else if (error.status === 400) {
        const errorMsg = error.error?.error || error.error?.message || 'Invalid request format';
        console.error('  Backend said:', errorMsg);
        throw new Error(`Upload failed: ${errorMsg}`);
      } else if (error.status === 413) {
        throw new Error('Files too large. Maximum size is 5MB per image.');
      } else if (error.status === 0) {
        throw new Error('Cannot connect to server. Check your connection.');
      }
      
      throw new Error(error.error?.message || error.message || 'Failed to upload images');
    }
  }

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
        console.log('Uploading images...');
        const imageUrls = await this.uploadImages();
        this.uploadedImageUrls = [...this.uploadedImageUrls, ...imageUrls];
        this.selectedImages = []; // Clear selected images after upload
      }

      // Prepare property data
      const propertyData: Property = {
        ...this.property,
        images: this.uploadedImageUrls,
        amenities: this.selectedAmenities,
        latitude: this.property.latitude || undefined,
        longitude: this.property.longitude || undefined
      };

      console.log('Creating property:', propertyData);

      // Create property
      this.propertyService.createProperty(propertyData).subscribe({
        next: (response) => {
          console.log('✅ Property created:', response);
          this.isLoading = false;
          this.successMessage = 'Property created successfully!';
          
          // Redirect after 1.5 seconds
          setTimeout(() => {
            // Try multiple navigation options
            this.router.navigate(['/landlord-dashboard']).catch(() => {
              this.router.navigate(['/dashboard']).catch(() => {
                this.router.navigate(['/']);
              });
            });
          }, 1500);
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
      this.errorMessage = error.message || 'Failed to upload images';
    }
  }

  cancel(): void {
    if (confirm('Are you sure you want to cancel? All unsaved changes will be lost.')) {
      // Try multiple navigation options
      this.router.navigate(['/landlord-dashboard']).catch(() => {
        this.router.navigate(['/dashboard']).catch(() => {
          this.router.navigate(['/']);
        });
      });
    }
  }
}