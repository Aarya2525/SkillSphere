import { Component, inject, OnInit } from '@angular/core';

import {
  Router,
  RouterLink,
  RouterLinkActive,
  RouterOutlet
} from '@angular/router';

import { AuthService } from '../../services/auth.service';

import { NotificationService } from '../../services/notification';

@Component({
  selector: 'app-main-layout',
  standalone: true,
  imports: [
    RouterOutlet,
    RouterLink,
    RouterLinkActive
  ],
  templateUrl: './main-layout.html',
  styleUrl: './main-layout.scss'
})
export class MainLayoutComponent implements OnInit {

  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly notificationService =
    inject(NotificationService);

  unreadNotificationCount = 0;

  ngOnInit(): void {
    this.authService.getCurrentUser().subscribe({
      error: () => {}
    });

    this.notificationService
      .unreadCount$
      .subscribe(count => {
        this.unreadNotificationCount = count;
      });

    this.loadUnreadNotifications();
  }

  loadUnreadNotifications(): void {
    this.notificationService
      .getNotifications()
      .subscribe({
        error: error => {
          console.error(
            'Failed to load notification count:',
            error
          );

          this.unreadNotificationCount = 0;
        }
      });
  }

  get currentUser() {
    return this.authService.getCurrentUserSnapshot();
  }

  get userRole(): string {
    return this.currentUser?.role ?? 'STUDENT';
  }

  get isInstructor(): boolean {
    return this.userRole === 'INSTRUCTOR';
  }

  get isAdmin(): boolean {
    return this.userRole === 'ADMIN';
  }

  get isStudent(): boolean {
    return this.userRole === 'STUDENT';
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
} 