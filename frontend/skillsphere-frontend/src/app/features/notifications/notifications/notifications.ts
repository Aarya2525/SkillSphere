import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

import {
  NotificationService,
  Notification
} from '../../../core/services/notification';

@Component({
  selector: 'app-notifications',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './notifications.html',
  styleUrl: './notifications.scss'
})
export class NotificationsComponent implements OnInit {
  private readonly notificationService = inject(NotificationService);
  private readonly router = inject(Router);

  notifications: Notification[] = [];

  loading = true;
  errorMessage = '';
  markingAllRead = false;

  ngOnInit(): void {
    this.loadNotifications();
  }

  loadNotifications(): void {
    this.loading = true;
    this.errorMessage = '';

    this.notificationService.getNotifications().subscribe({
      next: notifications => {
        this.notifications = notifications;
        this.loading = false;
      },

      error: error => {
        console.error(
          'Failed to load notifications:',
          error
        );

        this.loading = false;

        if (error.status === 401) {
          this.errorMessage =
            'Your session has expired. Please log in again.';
        } else {
          this.errorMessage =
            'Unable to load notifications. Please try again.';
        }
      }
    });
  }

  get unreadCount(): number {
    return this.notifications.filter(
      notification => !notification.is_read
    ).length;
  }

  markAsRead(notification: Notification): void {
    if (notification.is_read) {
      return;
    }

    this.notificationService
      .markAsRead(notification.id)
      .subscribe({
        next: updatedNotification => {
          this.notifications = this.notifications.map(
            item =>
              item.id === updatedNotification.id
                ? updatedNotification
                : item
          );
        },

        error: error => {
          console.error(
            'Failed to mark notification as read:',
            error
          );

          this.errorMessage =
            'Unable to mark the notification as read.';
        }
      });
  }

  markAllAsRead(): void {
    if (this.unreadCount === 0) {
      return;
    }

    this.markingAllRead = true;
    this.errorMessage = '';

    this.notificationService.markAllAsRead().subscribe({
      next: () => {
        this.notifications = this.notifications.map(
          notification => ({
            ...notification,
            is_read: true
          })
        );

        this.markingAllRead = false;
      },

      error: error => {
        console.error(
          'Failed to mark all notifications as read:',
          error
        );

        this.markingAllRead = false;
        this.errorMessage =
          'Unable to mark all notifications as read.';
      }
    });
  }

  getNotificationIcon(
    notificationType: string
  ): string {
    switch (notificationType) {
      case 'REVIEW':
        return '⭐';

      case 'CERTIFICATE':
        return '🏆';

      case 'COURSE':
        return '📚';

      case 'QUIZ':
        return '📝';

      case 'ENROLLMENT':
        return '🎓';

      default:
        return '🔔';
    }
  }

  formatDate(date: string): string {
    return new Date(date).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    });
  }

  formatTime(date: string): string {
    return new Date(date).toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  goToDashboard(): void {
    this.router.navigate(['/dashboard']);
  }
} 
