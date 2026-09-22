import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

import {
  AuthService,
  User
} from '../../core/services/auth.service';

import {
  EnrollmentService,
  Enrollment
} from '../../core/services/enrollment';

import {
  LearningService,
  LessonProgress
} from '../../core/services/learning';

import {
  QuizService,
  QuizAttempt
} from '../../core/services/quiz';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss'
})
export class DashboardComponent implements OnInit {
  private readonly authService = inject(AuthService);
  private readonly enrollmentService = inject(EnrollmentService);
  private readonly learningService = inject(LearningService);
  private readonly quizService = inject(QuizService);
  private readonly router = inject(Router);

  user: User | null = null;

  enrollments: Enrollment[] = [];
  progress: LessonProgress[] = [];
  attempts: QuizAttempt[] = [];

  loading = true;
  errorMessage = '';

  private completedRequests = 0;

  ngOnInit(): void {
    this.loadDashboard();
  }

  loadDashboard(): void {
    this.loading = true;
    this.errorMessage = '';
    this.completedRequests = 0;

    this.authService.getCurrentUser().subscribe({
      next: user => {
        this.user = user;

        this.loadEnrollments();
        this.loadProgress();
        this.loadAttempts();
      },

      error: error => {
        console.error(
          'Failed to load current user:',
          error
        );

        this.loading = false;

        if (error.status === 401) {
          this.authService.logout();
          this.router.navigate(['/login']);
          return;
        }

        this.errorMessage =
          'Unable to load your dashboard.';
      }
    });
  }

  private loadEnrollments(): void {
    this.enrollmentService.getEnrollments().subscribe({
      next: enrollments => {
        this.enrollments = enrollments;
        this.checkLoadingComplete();
      },

      error: error => {
        console.error(
          'Failed to load enrollments:',
          error
        );

        this.checkLoadingComplete();
      }
    });
  }

  private loadProgress(): void {
    this.learningService.getProgress().subscribe({
      next: progress => {
        this.progress = progress;
        this.checkLoadingComplete();
      },

      error: error => {
        console.error(
          'Failed to load learning progress:',
          error
        );

        this.checkLoadingComplete();
      }
    });
  }

  private loadAttempts(): void {
    this.quizService.getAttempts().subscribe({
      next: attempts => {
        this.attempts = attempts;
        this.checkLoadingComplete();
      },

      error: error => {
        console.error(
          'Failed to load quiz attempts:',
          error
        );

        this.checkLoadingComplete();
      }
    });
  }

  private checkLoadingComplete(): void {
    this.completedRequests++;

    if (this.completedRequests >= 3) {
      this.loading = false;
    }
  }

  get enrolledCourseCount(): number {
    return this.enrollments.length;
  }

  get completedLessonCount(): number {
    return this.progress.filter(
      item => item.is_completed
    ).length;
  }

  get quizAttemptCount(): number {
    return this.attempts.length;
  }

  get latestAttempt(): QuizAttempt | null {
    return this.attempts.length > 0
      ? this.attempts[0]
      : null;
  }

  getLatestPercentage(): number {
    const attempt = this.latestAttempt;

    if (!attempt || attempt.answers.length === 0) {
      return 0;
    }

    return Math.round(
      (attempt.score / attempt.answers.length) * 100
    );
  }

  getScoreClass(attempt: QuizAttempt): string {
    const percentage =
      attempt.answers.length > 0
        ? Math.round(
            (attempt.score / attempt.answers.length) * 100
          )
        : 0;

    if (percentage >= 80) {
      return 'excellent';
    }

    if (percentage >= 60) {
      return 'good';
    }

    return 'needs-practice';
  }

  formatDate(date: string): string {
    return new Date(date).toLocaleDateString(
      'en-IN',
      {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
      }
    );
  }

  goToCourses(): void {
    this.router.navigate(['/courses']);
  }

  goToLearning(): void {
    this.router.navigate(['/learning']);
  }

  goToQuizzes(): void {
    this.router.navigate(['/quizzes']);
  }

  goToQuizHistory(): void {
    this.router.navigate(['/quizzes/history']);
  }

  viewAttempt(attemptId: number): void {
    this.router.navigate([
      '/quizzes/attempts',
      attemptId
    ]);
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
} 