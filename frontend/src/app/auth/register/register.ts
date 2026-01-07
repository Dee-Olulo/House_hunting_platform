// import { Component } from '@angular/core';
// import { FormsModule } from '@angular/forms';
// import { Router, RouterLink } from '@angular/router';
// import { AuthService } from '../../services/auth';

// @Component({
//   selector: 'app-register',
//   standalone: true,
//   imports: [FormsModule],
//   templateUrl: './register.html',
//   styleUrls: ['./register.css']
// })
// export class Register {
//   email = '';
//   password = '';
//   role = '';

//   constructor(private authService: AuthService) {}

//   register() {
//     this.authService.register({
//       email: this.email,
//       password: this.password,
//       role: this.role
//     }).subscribe();
//   }
// }

import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [FormsModule, RouterLink],  // ✅ Added RouterLink
  templateUrl: './register.html',
  styleUrls: ['./register.css']
})
export class Register {
  email = '';
  password = '';
  role = '';
  private router = inject(Router);  // ✅ Added Router

  constructor(private authService: AuthService) {}

  register() {
    this.authService.register({
      email: this.email,
      password: this.password,
      role: this.role
    }).subscribe({
      next: (response) => {
        console.log('Registration successful', response);
        this.router.navigate(['/login']);  // ✅ Navigate to login after registration
      },
      error: (error) => {
        console.error('Registration failed', error);
      }
    });
  }
}