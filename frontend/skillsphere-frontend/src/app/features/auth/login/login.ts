import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.html',
  styleUrl: './login.scss'
})
export class LoginComponent {

  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  username = '';
  password = '';

  loading = false;
  errorMessage = '';

  onSubmit(): void {

    this.errorMessage = '';

    if (
      !this.username.trim() ||
      !this.password
    ) {
      this.errorMessage =
        'Username and password are required.';

      return;
    }

    this.loading = true;

    this.authService
      .login({
        username: this.username.trim(),
        password: this.password
      })
      .subscribe({

        next: () => {

          this.authService
            .getCurrentUser()
            .subscribe({

              next: user => {

                this.loading = false;

                switch (user.role) {

                  case 'INSTRUCTOR':
                    this.router.navigate([
                      '/instructor/dashboard'
                    ]);
                    break;

                  case 'ADMIN':
                    this.router.navigate([
                      '/admin/dashboard'
                    ]);
                    break;

                  case 'STUDENT':
                  default:
                    this.router.navigate([
                      '/dashboard'
                    ]);
                    break;

                }
              },

              error: error => {

                console.error(
                  'Failed to load current user:',
                  error
                );

                this.loading = false;

                this.errorMessage =
                  'Unable to load your account information. Please try again.';

                this.authService.logout();
              }

            });

        },

        error: error => {

          this.loading = false;

          if (error.status === 401) {

            this.errorMessage =
              'Invalid username or password.';

          } else {

            this.errorMessage =
              'Unable to connect to the server. Please try again.';

          }

        }

      });
  }
} 