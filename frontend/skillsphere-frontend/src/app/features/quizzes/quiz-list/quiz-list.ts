import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

import {
  QuizService,
  Quiz
} from '../../../core/services/quiz';

@Component({
  selector: 'app-quiz-list',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './quiz-list.html',
  styleUrl: './quiz-list.scss'
})
export class QuizListComponent implements OnInit {
  private readonly quizService = inject(QuizService);
  private readonly router = inject(Router);

  quizzes: Quiz[] = [];

  loading = true;
  errorMessage = '';

  ngOnInit(): void {
    this.loadQuizzes();
  }

  loadQuizzes(): void {
    this.loading = true;
    this.errorMessage = '';

    this.quizService.getQuizzes().subscribe({
      next: (quizzes) => {
        this.quizzes = quizzes;
        this.loading = false;
      },
      error: (error) => {
        console.error('Failed to load quizzes:', error);
        this.loading = false;
        this.errorMessage =
          'Unable to load quizzes. Please try again.';
      }
    });
  }

  startQuiz(quizId: number): void {
    this.router.navigate(['/quizzes', quizId]);
  }
} 
