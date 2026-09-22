import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import {
  AuthService,
  RegisterRequest
} from '../../../core/services/auth.service';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './register.html',
  styleUrl: './register.scss'
})
export class RegisterComponent {

  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  username = '';
  email = '';
  password = '';
  confirmPassword = '';
  role: 'STUDENT' | 'INSTRUCTOR' = 'STUDENT';

  loading = false;
  errorMessage = '';
  successMessage = '';

  onSubmit(): void {
    this.errorMessage = '';
    this.successMessage = '';

    if (
      !this.username.trim() ||
      !this.email.trim() ||
      !this.password ||
      !this.confirmPassword
    ) {
      this.errorMessage = 'All fields are required.';
      return;
    }

    if (this.password !== this.confirmPassword) {
      this.errorMessage = 'Passwords do not match.';
      return;
    }

    if (this.password.length < 8) {
      this.errorMessage = 'Password must be at least 8 characters.';
      return;
    }

    const data: RegisterRequest = {
      username: this.username.trim(),
      email: this.email.trim(),
      password: this.password,
      role: this.role
    };

    this.loading = true;

    this.authService.register(data).subscribe({
      next: () => {
        this.loading = false;
        this.successMessage =
          'Registration successful. Redirecting to login...';

        setTimeout(() => {
          this.router.navigate(['/login']);
        }, 1000);
      },

      error: (error) => {
        this.loading = false;

        if (error.status === 400) {
          if (error.error?.username) {
            this.errorMessage = error.error.username[0];
          } else if (error.error?.email) {
            this.errorMessage = error.error.email[0];
          } else {
            this.errorMessage =
              'Registration failed. Please check your information.';
          }
        } else {
          this.errorMessage =
            'Unable to connect to the server. Please try again.';
        }
      }
    });
  }

  goToLogin(): void {
    this.router.navigate(['/login']);
  }
} 