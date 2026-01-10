## Functional Requirements

1. The system shall allow users to register and log in based on roles.
2. The system shall allow tenants to search rental houses by location, price, and distance.
3. The system shall allow landlords and agents to add, edit, and remove property listings.
4. The system shall support map-based location sharing and navigation to properties.
5. The system shall allow tenants to book house viewing appointments.
6. The system shall automatically prompt landlords to confirm listings every 30 days.
7. The system shall support uploading of images and video advertisements.
8. The system shall support in-app payments for bookings and promotions.
9. The system shall notify users of bookings, payments, and listing expiry.

Great! Let's continue building on your successful authentication. I can see you have 8 more functional requirements to implement. Let me help you tackle them systematically.

## **Recommended Implementation Order:**

Based on dependencies and complexity, here's a logical order:

### **Phase 1: Property Management (Requirements 3 & 7)**
**Priority: HIGH** - Core functionality
- Landlord can add/edit/delete properties
- Image and video upload for properties
- Property listing management

### **Phase 2: Search & Discovery (Requirement 2)**
**Priority: HIGH** - Core tenant feature
- Search properties by location, price, no of bedrooms,
- Filter and sort functionality
- Property listing display

### **Phase 3: Location Services (Requirement 4)**
**Priority: MEDIUM** - Enhances user experience
- Map integration (Google Maps/Mapbox)
- Property locations on map
- Navigation to properties

### **Phase 4: Booking System (Requirement 5)**
**Priority: MEDIUM** - Key interaction
- Tenant booking requests
- Landlord booking management
- Calendar/scheduling

### **Phase 5: Notifications (Requirement 9)**
**Priority: MEDIUM** - User engagement
- Email/SMS notifications
- In-app notifications
- Real-time updates

### **Phase 6: Payment Integration (Requirement 8)**
**Priority: MEDIUM-LOW** - Can use test mode initially
- Payment gateway integration
- Transaction management
- Payment history

### **Phase 7: Automated Maintenance (Requirement 6)**
**Priority: LOW** - Background task
- Scheduled tasks
- Listing expiry reminders
- Auto-deactivation

---

## **Which would you like to start with?**

I recommend starting with **Phase 1: Property Management** since:
- ✅ You already have authentication working
- 🏠 Properties are the core of your app
- 📸 Image/video upload is essential
- 🔗 Other features depend on having properties in the system

**I can create for you:**

1. **Backend (Flask):**
   - Property model
   - Property routes (CRUD operations)
   - Image/video upload handling
   - File storage configuration

2. **Frontend (Angular):**
   - Landlord properties dashboard
   - Add/Edit property forms
   - Image/video upload component
   - Property list with actions

Should I proceed with **Property Management** or would you prefer to start with a different requirement? Let me know and I'll create all the necessary files!