import { Component, OnInit, ViewChild, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, NgForm } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { PropertyService, Property } from '../../services/property.service';
import { UploadService } from '../../services/upload.service';

interface ImagePreview {
  file: File;
  previewUrl: string;
}

@Component({
  selector: 'app-edit-property',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './edit-property.html',
  styleUrls: ['./edit-property.css']
})
export class EditPropertyComponent implements OnInit {
  @ViewChild('propertyForm') form!: NgForm;
  
  propertyId: string = '';
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

  selectedImages: ImagePreview[] = [];
  existingImages: string[] = [];
  uploadedImageUrls: string[] = [];
  selectedAmenities: string[] = [];
  
  isLoading = false;
  isUploading = false;
  isFetching = true;
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
    private router: Router,
    private route: ActivatedRoute,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.propertyId = this.route.snapshot.params['id'];
    console.log('✅ Editing property ID:', this.propertyId);
    this.loadProperty();
  }

  ngAfterViewInit(): void {
    // Only debug form after it's fully initialized and property is loaded
    if (!this.isFetching) {
      setTimeout(() => {
        this.debugFormValidity();
      }, 500);
    }
  }

  debugFormValidity(): void {
    if (!this.form) {
      console.log('⚠️ Form not yet initialized');
      return;
    }

    console.log('=== FORM DEBUG INFO ===');
    console.log('Form valid:', this.form.valid);
    console.log('Form pristine:', this.form.pristine);
    console.log('Form touched:', this.form.touched);
    console.log('Form errors:', this.form.form.errors);

    // Check each control
    Object.keys(this.form.form.controls).forEach(key => {
      const control = this.form.form.get(key);
      if (control?.invalid) {
        console.log(`❌ ${key} is INVALID:`, control.errors);
      } else {
        console.log(`✅ ${key} is valid`);
      }
    });
    console.log('======================');
  }

  loadProperty(): void {
    this.isFetching = true;
    this.errorMessage = '';
    
    this.propertyService.getProperty(this.propertyId).subscribe({
      next: (property) => {
        console.log('✅ Property loaded:', property);
        this.property = property;
        this.existingImages = property.images || [];
        this.selectedAmenities = property.amenities || [];
        this.isFetching = false;
        
        // Trigger change detection
        this.cdr.detectChanges();
        
        // Debug form after property loads and view updates
        setTimeout(() => {
          if (this.form) {
            this.debugFormValidity();
          }
        }, 1000);
      },
      error: (error) => {
        console.error('❌ Error loading property:', error);
        this.errorMessage = 'Failed to load property';
        this.isFetching = false;
      }
    });
  }

  getImageUrl(imagePath: string): string {
    return this.propertyService.getImageUrl(imagePath);
  }

  onImageSelect(event: any): void {
    const files = Array.from(event.target.files) as File[];
    
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

    const totalImages = this.existingImages.length + this.selectedImages.length + validFiles.length;
    if (totalImages > 20) {
      alert('Maximum 20 images allowed');
      return;
    }

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

  removeNewImage(index: number): void {
    this.selectedImages.splice(index, 1);
  }

  removeExistingImage(index: number): void {
    const url = this.existingImages[index];
    if (confirm('Delete this image?')) {
      this.uploadService.deleteFile(url).subscribe({
        next: () => {
          this.existingImages.splice(index, 1);
        },
        error: (error) => {
          console.error('Error deleting image:', error);
          alert('Failed to delete image');
        }
      });
    }
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
      return [];
    }

    this.isUploading = true;
    
    try {
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

  onSubmit(): void {
    console.log('🔵 onSubmit called');
    
    // Check if form exists and is valid
    if (!this.form) {
      console.log('❌ Form not initialized');
      return;
    }

    console.log('Form valid:', this.form.valid);
    console.log('Is loading:', this.isLoading);

    // Check form validity
    if (!this.form.valid) {
      console.log('❌ Form is invalid, marking all fields as touched');
      this.form.form.markAllAsTouched();
      this.debugFormValidity();
      this.errorMessage = 'Please fill in all required fields correctly';
      
      // Scroll to top to show error
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }

    if (this.isLoading) {
      console.log('⚠️ Already updating, please wait...');
      return;
    }

    this.errorMessage = '';
    this.isLoading = true;

    console.log('✅ Starting property update for ID:', this.propertyId);

    // Prepare update data
    const updateData: Partial<Property> = {
      title: this.property.title,
      description: this.property.description,
      property_type: this.property.property_type,
      address: this.property.address,
      city: this.property.city,
      state: this.property.state,
      zip_code: this.property.zip_code,
      country: this.property.country,
      latitude: this.property.latitude || undefined,
      longitude: this.property.longitude || undefined,
      price: this.property.price,
      bedrooms: this.property.bedrooms,
      bathrooms: this.property.bathrooms,
      area_sqft: this.property.area_sqft,
      images: this.existingImages,
      amenities: this.selectedAmenities
    };

    console.log('📦 Update data:', updateData);

    // Update property
    this.propertyService.updateProperty(this.propertyId, updateData).subscribe({
      next: (response) => {
        console.log('✅ Property updated successfully:', response);
        this.isLoading = false;
        alert('Property updated successfully!');
        
        // Navigate back to properties list
        this.router.navigate(['/landlord/properties']);
      },
      error: (error) => {
        console.error('❌ Error updating property:', error);
        this.isLoading = false;
        this.errorMessage = error.error?.error || 'Failed to update property';
        
        // Scroll to top to show error
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    });
  }

  goBack(): void {
    this.router.navigate(['/landlord/properties']);
  }

  cancel(): void {
    if (confirm('Are you sure you want to cancel? All unsaved changes will be lost.')) {
      this.router.navigate(['/landlord/properties']);
    }
  }
}