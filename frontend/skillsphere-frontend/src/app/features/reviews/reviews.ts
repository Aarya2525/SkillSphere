import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import {
  ReviewService,
  Review,
  CreateReviewRequest
} from '../../core/services/review';

import {
  EnrollmentService,
  Enrollment
} from '../../core/services/enrollment';

@Component({
  selector: 'app-reviews',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './reviews.html',
  styleUrl: './reviews.scss'
})
export class ReviewsComponent implements OnInit {
  private readonly reviewService = inject(ReviewService);
  private readonly enrollmentService = inject(EnrollmentService);
  private readonly router = inject(Router);

  reviews: Review[] = [];
  enrollments: Enrollment[] = [];

  loading = true;
  submitting = false;

  errorMessage = '';
  successMessage = '';

  selectedCourseId: number | null = null;

  rating = 5;
  comment = '';

  editingReviewId: number | null = null;
  editRating = 5;
  editComment = '';

  ngOnInit(): void {
    this.loadData();
  }

  loadData(): void {
    this.loading = true;
    this.errorMessage = '';

    this.enrollmentService.getEnrollments().subscribe({
      next: enrollments => {
        this.enrollments = enrollments;
        this.loadReviews();
      },

      error: error => {
        console.error('Failed to load enrollments:', error);
        this.loading = false;
        this.errorMessage =
          'Unable to load your enrolled courses. Please try again.';
      }
    });
  }

  loadReviews(): void {
    this.reviewService.getReviews().subscribe({
      next: reviews => {
        this.reviews = reviews;
        this.loading = false;
      },

      error: error => {
        console.error('Failed to load reviews:', error);
        this.loading = false;
        this.errorMessage =
          'Unable to load reviews. Please try again.';
      }
    });
  }

  selectCourse(courseId: number): void {
    this.selectedCourseId = courseId;
    this.rating = 5;
    this.comment = '';
    this.successMessage = '';
    this.errorMessage = '';
  }

  cancelReview(): void {
    this.selectedCourseId = null;
    this.rating = 5;
    this.comment = '';
    this.successMessage = '';
    this.errorMessage = '';
  }

  setRating(value: number): void {
    this.rating = value;
  }

  submitReview(): void {
    if (!this.selectedCourseId) {
      this.errorMessage = 'Please select a course.';
      return;
    }

    if (!this.comment.trim()) {
      this.errorMessage = 'Please enter a comment.';
      return;
    }

    if (this.rating < 1 || this.rating > 5) {
      this.errorMessage = 'Please select a rating between 1 and 5.';
      return;
    }

    const data: CreateReviewRequest = {
      course: this.selectedCourseId,
      rating: this.rating,
      comment: this.comment.trim()
    };

    this.submitting = true;
    this.errorMessage = '';
    this.successMessage = '';

    this.reviewService.createReview(data).subscribe({
      next: review => {
        this.reviews = [
          review,
          ...this.reviews
        ];

        this.submitting = false;
        this.successMessage =
          'Your review has been submitted successfully.';

        this.selectedCourseId = null;
        this.rating = 5;
        this.comment = '';
      },

      error: error => {
        console.error('Failed to create review:', error);

        this.submitting = false;

        if (error.status === 400) {
          this.errorMessage =
            'Please check your rating and comment.';
        } else if (error.status === 403) {
          this.errorMessage =
            error.error?.detail ||
            'You are not allowed to review this course.';
        } else if (error.status === 401) {
          this.errorMessage =
            'Your session has expired. Please log in again.';
        } else {
          this.errorMessage =
            'Unable to submit your review. Please try again.';
        }
      }
    });
  }

  canReviewCourse(courseId: number): boolean {
    return !this.reviews.some(
      review => review.course === courseId
    );
  }

  getReviewedCourseIds(): number[] {
    return this.reviews.map(
      review => review.course
    );
  }

  getCourseReviews(courseId: number): Review[] {
    return this.reviews.filter(
      review => review.course === courseId
    );
  }

  getAverageRating(): number {
    if (this.reviews.length === 0) {
      return 0;
    }

    const total = this.reviews.reduce(
      (sum, review) => sum + review.rating,
      0
    );

    return total / this.reviews.length;
  }

  getStars(rating: number): string {
    return '★'.repeat(rating) +
      '☆'.repeat(5 - rating);
  }

  formatDate(date: string): string {
    return new Date(date).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    });
  }

  startEdit(review: Review): void {
    this.editingReviewId = review.id;
    this.editRating = review.rating;
    this.editComment = review.comment;
    this.errorMessage = '';
    this.successMessage = '';
  }

  cancelEdit(): void {
    this.editingReviewId = null;
    this.editRating = 5;
    this.editComment = '';
  }

  setEditRating(value: number): void {
    this.editRating = value;
  }

  saveEdit(review: Review): void {
    if (!this.editComment.trim()) {
      this.errorMessage = 'Please enter a comment.';
      return;
    }

    if (this.editRating < 1 || this.editRating > 5) {
      this.errorMessage = 'Please select a rating between 1 and 5.';
      return;
    }

    this.reviewService.updateReview(
      review.id,
      {
        rating: this.editRating,
        comment: this.editComment.trim()
      }
    ).subscribe({
      next: updatedReview => {
        this.reviews = this.reviews.map(
          item =>
            item.id === updatedReview.id
              ? updatedReview
              : item
        );

        this.editingReviewId = null;
        this.successMessage =
          'Your review has been updated successfully.';
        this.errorMessage = '';
      },

      error: error => {
        console.error('Failed to update review:', error);

        if (error.status === 403) {
          this.errorMessage =
            'You are not allowed to edit this review.';
        } else if (error.status === 401) {
          this.errorMessage =
            'Your session has expired. Please log in again.';
        } else {
          this.errorMessage =
            'Unable to update your review. Please try again.';
        }
      }
    });
  }

  deleteReview(review: Review): void {
    const confirmed = window.confirm(
      'Are you sure you want to delete this review?'
    );

    if (!confirmed) {
      return;
    }

    this.reviewService.deleteReview(review.id).subscribe({
      next: () => {
        this.reviews = this.reviews.filter(
          item => item.id !== review.id
        );

        this.successMessage =
          'Your review has been deleted successfully.';
        this.errorMessage = '';
      },

      error: error => {
        console.error('Failed to delete review:', error);

        if (error.status === 403) {
          this.errorMessage =
            'You are not allowed to delete this review.';
        } else if (error.status === 401) {
          this.errorMessage =
            'Your session has expired. Please log in again.';
        } else {
          this.errorMessage =
            'Unable to delete your review. Please try again.';
        }
      }
    });
  }

  goToCourses(): void {
    this.router.navigate(['/courses']);
  }

  goToDashboard(): void {
    this.router.navigate(['/dashboard']);
  }
} 