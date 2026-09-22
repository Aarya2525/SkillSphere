import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

import {
  CourseService,
  Course
} from '../../../core/services/course';

@Component({
  selector: 'app-course-list',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './course-list.html',
  styleUrl: './course-list.scss'
})
export class CourseListComponent implements OnInit {

  private readonly courseService = inject(CourseService);
  private readonly router = inject(Router);

  courses: Course[] = [];
  loading = true;
  errorMessage = '';

  ngOnInit(): void {
    this.loadCourses();
  }

  loadCourses(): void {
    this.loading = true;
    this.errorMessage = '';

    this.courseService.getCourses().subscribe({
      next: (courses) => {
        this.courses = courses;
        this.loading = false;
      },

      error: (error) => {
        console.error('Failed to load courses:', error);

        this.loading = false;
        this.errorMessage =
          'Unable to load courses. Please try again.';
      }
    });
  }

  viewCourse(courseId: number): void {
    this.router.navigate(['/courses', courseId]);
  }
} 