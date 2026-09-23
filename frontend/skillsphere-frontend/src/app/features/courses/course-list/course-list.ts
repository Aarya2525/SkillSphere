import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import {
  CourseService,
  Course
} from '../../../core/services/course';

import {
  EnrollmentService,
  Enrollment
} from '../../../core/services/enrollment';

@Component({
  selector: 'app-course-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './course-list.html',
  styleUrl: './course-list.scss'
})
export class CourseListComponent implements OnInit {
  private readonly courseService = inject(CourseService);
  private readonly enrollmentService = inject(EnrollmentService);
  private readonly router = inject(Router);

  courses: Course[] = [];
  enrollments: Enrollment[] = [];
  loading = true;
  errorMessage = '';

  searchTerm = '';
  activeTab: 'ALL' | 'ENROLLED' | 'AVAILABLE' = 'ALL';

  ngOnInit(): void {
    this.loadData();
  }

  loadData(): void {
    this.loading = true;
    this.errorMessage = '';

    this.courseService.getCourses().subscribe({
      next: (courses) => {
        this.courses = courses;
        this.loadEnrollments();
      },
      error: (error) => {
        console.error('Failed to load courses:', error);
        this.loading = false;
        this.errorMessage = 'Unable to load courses. Please try again.';
      }
    });
  }

  loadCourses(): void {
    this.loadData();
  }

  private loadEnrollments(): void {
    this.enrollmentService.getEnrollments().subscribe({
      next: (enrollments) => {
        this.enrollments = enrollments;
        this.loading = false;
      },
      error: () => {
        this.enrollments = [];
        this.loading = false;
      }
    });
  }

  isEnrolled(courseId: number): boolean {
    return this.enrollments.some(e => e.course === courseId);
  }

  get filteredCourses(): Course[] {
    let result = this.courses;

    if (this.activeTab === 'ENROLLED') {
      result = result.filter(c => this.isEnrolled(c.id));
    } else if (this.activeTab === 'AVAILABLE') {
      result = result.filter(c => !this.isEnrolled(c.id));
    }

    if (this.searchTerm.trim()) {
      const q = this.searchTerm.toLowerCase().trim();
      result = result.filter(c =>
        c.title.toLowerCase().includes(q) ||
        c.description.toLowerCase().includes(q) ||
        (c.instructor_name && c.instructor_name.toLowerCase().includes(q))
      );
    }

    return result;
  }

  setActiveTab(tab: 'ALL' | 'ENROLLED' | 'AVAILABLE'): void {
    this.activeTab = tab;
  }

  clearSearch(): void {
    this.searchTerm = '';
  }

  viewCourse(courseId: number): void {
    this.router.navigate(['/courses', courseId]);
  }
}