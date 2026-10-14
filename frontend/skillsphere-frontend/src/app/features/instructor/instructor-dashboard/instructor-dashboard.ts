import {
  Component,
  OnInit,
  inject
} from '@angular/core';

import { CommonModule } from '@angular/common';
import { RouterLink, Router, ActivatedRoute } from '@angular/router';

import {
  CourseService,
  Course
} from '../../../core/services/course';

@Component({
  selector: 'app-instructor-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink
  ],
  templateUrl: './instructor-dashboard.html',
  styleUrl: './instructor-dashboard.scss'
})
export class InstructorDashboardComponent
  implements OnInit {

  private readonly courseService =
    inject(CourseService);

  private readonly router =
    inject(Router, { optional: true });

  private readonly route =
    inject(ActivatedRoute, { optional: true });

  courses: Course[] = [];

  loading = true;
  errorMessage = '';
  notificationMessage = '';

  ngOnInit(): void {
    this.extractNavigationNotification();
    this.loadCourses();
  }

  extractNavigationNotification(): void {
    const nav = this.router?.getCurrentNavigation?.();
    const state = (nav?.extras?.state ?? (typeof history !== 'undefined' ? history.state : null)) as Record<string, unknown> | null;

    if (state) {
      const msg = state['notification'] ?? state['notificationMessage'] ?? state['message'] ?? state['alert'] ?? state['error'];
      if (typeof msg === 'string' && msg.trim()) {
        this.notificationMessage = msg.trim();
      }
    }

    const queryParamMsg = this.route?.snapshot?.queryParamMap?.get('message') || this.route?.snapshot?.queryParamMap?.get('notification');
    if (queryParamMsg && !this.notificationMessage) {
      this.notificationMessage = queryParamMsg;
    }

    if (this.notificationMessage && typeof window !== 'undefined' && window.history?.replaceState && state) {
      const { notification, notificationMessage, message, alert, error, ...rest } = state;
      window.history.replaceState(rest, document.title);
    }
  }

  dismissNotification(): void {
    this.notificationMessage = '';
  }

  loadCourses(): void {

    this.loading = true;
    this.errorMessage = '';

    this.courseService
      .getCourses()
      .subscribe({

        next: (courses: Course[]) => {

          this.courses = courses;

          this.loading = false;
        },

        error: (error) => {

          console.error(
            'Failed to load instructor courses:',
            error
          );

          this.loading = false;

          if (error.status === 401) {

            this.errorMessage =
              'Your session has expired. Please log in again.';

          } else if (error.status === 403) {

            this.errorMessage =
              'You do not have permission to access instructor courses.';

          } else {

            this.errorMessage =
              'Unable to load your courses. Please try again.';
          }
        }
      });
  }

  get publishedCourseCount(): number {

    return this.courses.filter(
      course => course.is_published
    ).length;
  }

  get draftCourseCount(): number {

    return this.courses.filter(
      course => !course.is_published
    ).length;
  }
} 