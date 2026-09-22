import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface LessonProgress {
  id: number;
  student: number;
  student_name: string;
  lesson: number;
  lesson_title: string;
  course_id: number;
  is_completed: boolean;
  completed_at: string | null;
}

export interface CreateLessonProgressRequest {
  lesson: number;
  is_completed: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class LearningService {

  private readonly http = inject(HttpClient);

  private readonly apiUrl =
    `${environment.apiUrl}/learning`;

  getProgress(): Observable<LessonProgress[]> {
    return this.http.get<LessonProgress[]>(
      `${this.apiUrl}/progress/`
    );
  }

  createProgress(
    data: CreateLessonProgressRequest
  ): Observable<LessonProgress> {
    return this.http.post<LessonProgress>(
      `${this.apiUrl}/progress/`,
      data
    );
  }

  getProgressById(
    id: number
  ): Observable<LessonProgress> {
    return this.http.get<LessonProgress>(
      `${this.apiUrl}/progress/${id}/`
    );
  }

  updateProgress(
    id: number,
    data: Partial<CreateLessonProgressRequest>
  ): Observable<LessonProgress> {
    return this.http.patch<LessonProgress>(
      `${this.apiUrl}/progress/${id}/`,
      data
    );
  }
} 