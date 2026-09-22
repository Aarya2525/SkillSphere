import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Enrollment {
  id: number;
  student: number;
  student_name: string;
  course: number;
  course_title: string;
  enrolled_at: string;
}

export interface CreateEnrollmentRequest {
  course: number;
}

@Injectable({
  providedIn: 'root'
})
export class EnrollmentService {

  private readonly http = inject(HttpClient);

  private readonly apiUrl =
    'http://127.0.0.1:8000/api/enrollments';

  getEnrollments(): Observable<Enrollment[]> {
    return this.http.get<Enrollment[]>(
      `${this.apiUrl}/`
    );
  }

  getEnrollment(id: number): Observable<Enrollment> {
    return this.http.get<Enrollment>(
      `${this.apiUrl}/${id}/`
    );
  }

  createEnrollment(
    data: CreateEnrollmentRequest
  ): Observable<Enrollment> {
    return this.http.post<Enrollment>(
      `${this.apiUrl}/`,
      data
    );
  }
} 