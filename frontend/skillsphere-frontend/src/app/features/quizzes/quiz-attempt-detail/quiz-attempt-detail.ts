import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';

import {
  QuizService,
  QuizAttempt
} from '../../../core/services/quiz';

@Component({
  selector: 'app-quiz-attempt-detail',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './quiz-attempt-detail.html',
  styleUrl: './quiz-attempt-detail.scss'
})
export class QuizAttemptDetailComponent implements OnInit {
  private readonly quizService = inject(QuizService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  attempt: QuizAttempt | null = null;

  loading = true;
  errorMessage = '';

  ngOnInit(): void {
    const attemptId = Number(
      this.route.snapshot.paramMap.get('id')
    );

    if (!attemptId) {
      this.loading = false;
      this.errorMessage = 'Invalid quiz attempt.';
      return;
    }

    this.loadAttempt(attemptId);
  }

  loadAttempt(attemptId: number): void {
    this.loading = true;
    this.errorMessage = '';

    this.quizService.getAttempt(attemptId).subscribe({
      next: attempt => {
        this.attempt = attempt;
        this.loading = false;
      },

      error: error => {
        console.error(
          'Failed to load quiz attempt:',
          error
        );

        this.loading = false;

        if (error.status === 404) {
          this.errorMessage =
            'Quiz attempt not found.';
        } else if (error.status === 403) {
          this.errorMessage =
            'You are not allowed to view this quiz attempt.';
        } else {
          this.errorMessage =
            'Unable to load this quiz attempt. Please try again.';
        }
      }
    });
  }

  get percentage(): number {
    if (
      !this.attempt ||
      this.attempt.answers.length === 0
    ) {
      return 0;
    }

    return Math.round(
      (this.attempt.score /
        this.attempt.answers.length) *
        100
    );
  }

  getScoreClass(): string {
    if (this.percentage >= 80) {
      return 'excellent';
    }

    if (this.percentage >= 60) {
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

  formatTime(date: string): string {
    return new Date(date).toLocaleTimeString(
      'en-IN',
      {
        hour: '2-digit',
        minute: '2-digit'
      }
    );
  }

  retryQuiz(): void {
    if (!this.attempt) {
      return;
    }

    this.router.navigate([
      '/quizzes',
      this.attempt.quiz
    ]);
  }

  goBack(): void {
    this.router.navigate([
      '/quizzes/history'
    ]);
  }
} 