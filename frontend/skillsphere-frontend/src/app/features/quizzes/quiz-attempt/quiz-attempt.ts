import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';

import {
  QuizService,
  Quiz,
  QuizSubmitResponse
} from '../../../core/services/quiz';

@Component({
  selector: 'app-quiz-attempt',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './quiz-attempt.html',
  styleUrl: './quiz-attempt.scss'
})
export class QuizAttemptComponent implements OnInit {
  private readonly quizService = inject(QuizService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  quiz: Quiz | null = null;
  selectedAnswers: Record<number, number> = {};

  loading = true;
  submitting = false;
  errorMessage = '';

  ngOnInit(): void {
    const quizId = Number(
      this.route.snapshot.paramMap.get('id')
    );

    if (!quizId) {
      this.loading = false;
      this.errorMessage = 'Invalid quiz.';
      return;
    }

    this.loadQuiz(quizId);
  }

  loadQuiz(quizId: number): void {
    this.loading = true;
    this.errorMessage = '';

    this.quizService.getQuiz(quizId).subscribe({
      next: quiz => {
        this.quiz = quiz;
        this.loading = false;
      },

      error: error => {
        console.error('Failed to load quiz:', error);

        this.loading = false;
        this.errorMessage =
          'Unable to load the quiz. Please try again.';
      }
    });
  }

  selectAnswer(
    questionId: number,
    optionId: number
  ): void {
    this.selectedAnswers[questionId] = optionId;
  }

  isSelected(
    questionId: number,
    optionId: number
  ): boolean {
    return this.selectedAnswers[questionId] === optionId;
  }

  get answeredCount(): number {
    return Object.keys(this.selectedAnswers).length;
  }

  get totalQuestions(): number {
    return this.quiz?.questions.length ?? 0;
  }

  submitQuiz(): void {
    if (!this.quiz || this.submitting) {
      return;
    }

    if (this.answeredCount !== this.totalQuestions) {
      this.errorMessage =
        'Please answer all questions before submitting the quiz.';
      return;
    }

    this.submitting = true;
    this.errorMessage = '';

    const answers = this.quiz.questions.map(question => ({
      question: question.id,
      selected_option: this.selectedAnswers[question.id]
    }));

    const request = {
      quiz: this.quiz.id,
      answers
    };

    this.quizService.submitQuiz(
      this.quiz.id,
      request
    ).subscribe({

      next: (response: QuizSubmitResponse) => {
        console.log('Quiz submitted successfully:', response);

        this.submitting = false;

        sessionStorage.setItem(
          'skillsphere_quiz_result',
          JSON.stringify(response)
        );

        this.router.navigate([
          '/quizzes',
          this.quiz!.id,
          'result'
        ]);
      },

      error: error => {
        console.error(
          'Failed to submit quiz:',
          error
        );

        this.submitting = false;

        if (error.status === 400) {
          this.errorMessage =
            'Unable to submit the quiz. Please check all answers and try again.';
        } else if (error.status === 403) {
          this.errorMessage =
            'You are not allowed to submit this quiz.';
        } else {
          this.errorMessage =
            'Unable to submit the quiz. Please try again.';
        }
      }
    });
  }

  goBack(): void {
    this.router.navigate(['/quizzes']);
  }
} 