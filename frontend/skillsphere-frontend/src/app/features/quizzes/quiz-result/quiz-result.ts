import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';

import { QuizService, QuizSubmitResponse } from '../../../core/services/quiz';
import { CertificateService } from '../../../core/services/certificate';

@Component({
  selector: 'app-quiz-result',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './quiz-result.html',
  styleUrl: './quiz-result.scss'
})
export class QuizResultComponent implements OnInit {
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly quizService = inject(QuizService);
  private readonly certificateService = inject(CertificateService);

  result: QuizSubmitResponse | null = null;
  courseId: number | null = null;
  courseTitle = '';
  claimingCertificate = false;
  certificateErrorMessage = '';
  certificateSuccessMessage = '';

  ngOnInit(): void {
    const storedResult =
      sessionStorage.getItem('skillsphere_quiz_result');

    if (storedResult) {
      try {
        this.result = JSON.parse(
          storedResult
        ) as QuizSubmitResponse;
      } catch (error) {
        console.error(
          'Failed to read quiz result:',
          error
        );

        sessionStorage.removeItem(
          'skillsphere_quiz_result'
        );
      }
    }

    if (!this.result) {
      console.error(
        'No quiz result found.'
      );

      this.router.navigate(['/quizzes']);
      return;
    }

    this.quizService.getQuiz(this.result.quiz).subscribe({
      next: (quiz) => {
        this.courseId = quiz.course;
        this.courseTitle = quiz.course_title || '';
      },
      error: () => {}
    });
  }

  get percentage(): number {
    if (!this.result) return 0;
    if (this.result.percentage !== undefined && this.result.percentage !== null) {
      return this.result.percentage;
    }
    if (this.result.total_questions === 0) return 0;
    return Math.round((this.result.score / this.result.total_questions) * 100);
  }

  get isPassed(): boolean {
    if (!this.result) return false;
    if (this.result.is_passed !== undefined && this.result.is_passed !== null) {
      return this.result.is_passed;
    }
    return this.percentage >= this.passingScore;
  }

  get passingScore(): number {
    return this.result?.passing_score ?? 70;
  }

  claimCertificate(): void {
    if (!this.courseId || this.claimingCertificate) return;
    this.claimingCertificate = true;
    this.certificateErrorMessage = '';
    this.certificateSuccessMessage = '';

    this.certificateService.createCertificate({
      course: this.courseId
    }).subscribe({
      next: (res) => {
        this.claimingCertificate = false;
        this.certificateSuccessMessage = 'Certificate earned! Navigating to your certificate...';
        setTimeout(() => {
          this.router.navigate(['/certificates', res.certificate.id]);
        }, 1200);
      },
      error: (err) => {
        this.claimingCertificate = false;
        if (err.error?.error) {
          this.certificateErrorMessage = err.error.error;
        } else {
          this.certificateErrorMessage =
            'You passed the quiz, but you must complete all lessons (100%) before claiming your certificate.';
        }
      }
    });
  }

  goToQuizzes(): void {
    sessionStorage.removeItem(
      'skillsphere_quiz_result'
    );

    this.router.navigate(['/quizzes']);
  }

  goToCourse(): void {
    if (!this.courseId) {
      this.goToQuizzes();
      return;
    }
    sessionStorage.removeItem('skillsphere_quiz_result');
    this.router.navigate(['/courses', this.courseId]);
  }

  retryQuiz(): void {
    if (!this.result) {
      return;
    }

    const quizId = this.result.quiz;

    sessionStorage.removeItem(
      'skillsphere_quiz_result'
    );

    this.router.navigate([
      '/quizzes',
      quizId
    ]);
  }
}