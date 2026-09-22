import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface QuizOption {
  id: number;
  question: number;
  text: string;
  is_correct: boolean;
}

export interface QuizQuestion {
  id: number;
  quiz: number;
  text: string;
  order: number;
  options: QuizOption[];
}

export interface Quiz {
  id: number;
  course: number;
  course_title?: string;
  title: string;
  description: string;
  passing_score: number;
  is_published: boolean;
  questions: QuizQuestion[];
}

export interface QuizAnswerRequest {
  question: number;
  selected_option: number;
}

export interface QuizSubmitRequest {
  quiz: number;
  answers: QuizAnswerRequest[];
}

export interface QuizSubmitResponse {
  message: string;
  attempt_id: number;
  quiz: number;
  score: number;
  total_questions: number;
  percentage: number;
  passing_score: number;
  is_passed: boolean;
}

export interface QuizAttemptAnswer {
  id: number;
  attempt: number;
  question: number;
  question_text: string;
  selected_option: number;
  selected_option_text: string;
  is_correct: boolean;
  correct_option_text: string | null;
}

export interface QuizAttempt {
  id: number;
  student: number;
  student_name: string;
  quiz: number;
  quiz_title: string;
  score: number;
  total_questions: number;
  percentage: number;
  is_passed: boolean;
  passing_score?: number;
  submitted_at: string;
  answers: QuizAttemptAnswer[];
}

@Injectable({
  providedIn: 'root'
})
export class QuizService {
  private readonly http = inject(HttpClient);

  private readonly apiUrl =
    'http://127.0.0.1:8000/api/quizzes';

  // --------------------------------------------------
  // STUDENT ENDPOINTS
  // --------------------------------------------------

  getQuizzes(): Observable<Quiz[]> {
    return this.http.get<Quiz[]>(
      `${this.apiUrl}/`
    );
  }

  getQuizzesByCourse(courseId: number): Observable<Quiz[]> {
    return this.http.get<Quiz[]>(
      `${this.apiUrl}/?course=${courseId}`
    );
  }

  getQuiz(id: number): Observable<Quiz> {
    return this.http.get<Quiz>(
      `${this.apiUrl}/student/${id}/`
    );
  }

  submitQuiz(
    quizId: number,
    data: QuizSubmitRequest
  ): Observable<QuizSubmitResponse> {
    return this.http.post<QuizSubmitResponse>(
      `${this.apiUrl}/student/${quizId}/submit/`,
      data
    );
  }

  getAttempts(): Observable<QuizAttempt[]> {
    return this.http.get<QuizAttempt[]>(
      `${this.apiUrl}/attempts/`
    );
  }

  getAttempt(id: number): Observable<QuizAttempt> {
    return this.http.get<QuizAttempt>(
      `${this.apiUrl}/attempts/${id}/`
    );
  }

  // --------------------------------------------------
  // INSTRUCTOR & ADMIN MANAGEMENT ENDPOINTS
  // --------------------------------------------------

  getQuizDetail(id: number): Observable<Quiz> {
    return this.http.get<Quiz>(
      `${this.apiUrl}/${id}/`
    );
  }

  createQuiz(data: Partial<Quiz>): Observable<Quiz> {
    return this.http.post<Quiz>(
      `${this.apiUrl}/`,
      data
    );
  }

  updateQuiz(id: number, data: Partial<Quiz>): Observable<Quiz> {
    return this.http.patch<Quiz>(
      `${this.apiUrl}/${id}/`,
      data
    );
  }

  deleteQuiz(id: number): Observable<void> {
    return this.http.delete<void>(
      `${this.apiUrl}/${id}/`
    );
  }

  createQuestion(data: Partial<QuizQuestion>): Observable<QuizQuestion> {
    return this.http.post<QuizQuestion>(
      `${this.apiUrl}/questions/`,
      data
    );
  }

  updateQuestion(
    id: number,
    data: Partial<QuizQuestion>
  ): Observable<QuizQuestion> {
    return this.http.patch<QuizQuestion>(
      `${this.apiUrl}/questions/${id}/`,
      data
    );
  }

  deleteQuestion(id: number): Observable<void> {
    return this.http.delete<void>(
      `${this.apiUrl}/questions/${id}/`
    );
  }

  createOption(data: Partial<QuizOption>): Observable<QuizOption> {
    return this.http.post<QuizOption>(
      `${this.apiUrl}/options/`,
      data
    );
  }

  updateOption(
    id: number,
    data: Partial<QuizOption>
  ): Observable<QuizOption> {
    return this.http.patch<QuizOption>(
      `${this.apiUrl}/options/${id}/`,
      data
    );
  }

  deleteOption(id: number): Observable<void> {
    return this.http.delete<void>(
      `${this.apiUrl}/options/${id}/`
    );
  }

  getInstructorAttempts(): Observable<QuizAttempt[]> {
    return this.http.get<QuizAttempt[]>(
      `${this.apiUrl}/instructor/attempts/`
    );
  }
}