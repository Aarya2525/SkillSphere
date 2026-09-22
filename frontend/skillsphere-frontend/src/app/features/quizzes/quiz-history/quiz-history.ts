import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

import {
  QuizService,
  QuizAttempt
} from '../../../core/services/quiz';

@Component({
  selector: 'app-quiz-history',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './quiz-history.html',
  styleUrl: './quiz-history.scss'
})
export class QuizHistoryComponent implements OnInit {
  private readonly quizService = inject(QuizService);

  readonly router = inject(Router);

  attempts: QuizAttempt[] = [];

  loading = true;

  errorMessage = '';

  ngOnInit(): void {
    this.loadAttempts();
  }

  loadAttempts(): void {
    this.loading = true;
    this.errorMessage = '';

    this.quizService.getAttempts().subscribe({
      next: attempts => {
        this.attempts = attempts;
        this.loading = false;
      },

      error: error => {
        console.error(
          'Failed to load quiz attempts:',
          error
        );

        this.loading = false;

        this.errorMessage =
          'Unable to load your quiz history. Please try again.';
      }
    });
  }

  getPercentage(attempt: QuizAttempt): number {
    if (attempt.percentage !== undefined && attempt.percentage !== null) {
      return attempt.percentage;
    }

    const totalQuestions =
      attempt.total_questions || attempt.answers?.length || 0;

    if (totalQuestions === 0) {
      return 0;
    }

    return Math.round(
      (attempt.score / totalQuestions) * 100
    );
  }

  isAttemptPassed(attempt: QuizAttempt): boolean {
    if (attempt.is_passed !== undefined && attempt.is_passed !== null) {
      return attempt.is_passed;
    }

    const passing = attempt.passing_score ?? 70;
    return this.getPercentage(attempt) >= passing;
  }

  getScoreClass(attempt: QuizAttempt): string {
    const passed = this.isAttemptPassed(attempt);

    if (passed) {
      return 'excellent';
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

  viewAttempt(attemptId: number): void {
    this.router.navigate([
      '/quizzes/attempts',
      attemptId
    ]);
  }

  retryQuiz(quizId: number): void {
    this.router.navigate([
      '/quizzes',
      quizId
    ]);
  }
} 