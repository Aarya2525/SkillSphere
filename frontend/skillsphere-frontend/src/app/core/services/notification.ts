import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, tap } from 'rxjs';

export interface Notification {
  id: number;
  recipient: number;
  recipient_name: string;
  notification_type: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export interface MarkAllReadResponse {
  message: string;
  updated_count: number;
}

@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  private readonly http = inject(HttpClient);

  private readonly apiUrl =
    'http://127.0.0.1:8000/api/notifications';

  private readonly unreadCountSubject =
    new BehaviorSubject<number>(0);

  readonly unreadCount$ =
    this.unreadCountSubject.asObservable();

  getNotifications(): Observable<Notification[]> {
    return this.http.get<Notification[]>(
      `${this.apiUrl}/`
    ).pipe(
      tap(notifications => {
        this.updateUnreadCount(notifications);
      })
    );
  }

  getNotification(id: number): Observable<Notification> {
    return this.http.get<Notification>(
      `${this.apiUrl}/${id}/`
    );
  }

  markAsRead(id: number): Observable<Notification> {
    return this.http.patch<Notification>(
      `${this.apiUrl}/${id}/read/`,
      {}
    ).pipe(
      tap(notification => {
        if (notification.is_read) {
          this.unreadCountSubject.next(
            Math.max(
              0,
              this.unreadCountSubject.value - 1
            )
          );
        }
      })
    );
  }

  markAllAsRead(): Observable<MarkAllReadResponse> {
    return this.http.patch<MarkAllReadResponse>(
      `${this.apiUrl}/read-all/`,
      {}
    ).pipe(
      tap(() => {
        this.unreadCountSubject.next(0);
      })
    );
  }

  private updateUnreadCount(
    notifications: Notification[]
  ): void {
    const unreadCount = notifications.filter(
      notification => !notification.is_read
    ).length;

    this.unreadCountSubject.next(unreadCount);
  }
} 