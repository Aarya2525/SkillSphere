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

  getCourseCategory(course: Course): string {
    const text = `${course.title} ${course.description}`.toLowerCase();
    if (text.includes('python') || text.includes('django') || text.includes('backend') || text.includes('api')) {
      return 'Backend Development';
    }
    if (text.includes('angular') || text.includes('react') || text.includes('frontend') || text.includes('css') || text.includes('web') || text.includes('javascript')) {
      return 'Web Development';
    }
    if (text.includes('data') || text.includes('ai') || text.includes('machine learning')) {
      return 'Data & AI';
    }
    if (text.includes('cloud') || text.includes('devops') || text.includes('docker')) {
      return 'Cloud & DevOps';
    }
    return 'Software Engineering';
  }

  getCourseDifficulty(course: Course): string {
    const text = course.title.toLowerCase();
    if (text.includes('advanced') || text.includes('mastery') || course.id % 3 === 0) {
      return 'Advanced';
    }
    if (text.includes('intermediate') || course.id % 2 === 0) {
      return 'Intermediate';
    }
    return 'Beginner';
  }

  getCourseThumbnailGradient(course: Course): string {
    const gradients = [
      'linear-gradient(135deg, #4f46e5 0%, #06b6d4 100%)',
      'linear-gradient(135deg, #059669 0%, #10b981 100%)',
      'linear-gradient(135deg, #7c3aed 0%, #ec4899 100%)',
      'linear-gradient(135deg, #0284c7 0%, #38bdf8 100%)',
      'linear-gradient(135deg, #d97706 0%, #f59e0b 100%)'
    ];
    return gradients[Math.abs(course.id) % gradients.length];
  }

  getCourseIcon(course: Course): string {
    const cat = this.getCourseCategory(course);
    switch (cat) {
      case 'Backend Development': return '⚡';
      case 'Web Development': return '🌐';
      case 'Data & AI': return '🧠';
      case 'Cloud & DevOps': return '☁️';
      default: return '💻';
    }
  }

  getEstimatedDuration(course: Course): string {
    const hours = (Math.abs(course.id * 1.5) % 6) + 2;
    return `~${hours.toFixed(1)} hrs`;
  }
}