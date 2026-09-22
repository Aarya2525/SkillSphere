import {
  Component,
  OnInit,
  inject
} from '@angular/core';

import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

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

  courses: Course[] = [];

  loading = true;
  errorMessage = '';

  ngOnInit(): void {
    this.loadCourses();
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