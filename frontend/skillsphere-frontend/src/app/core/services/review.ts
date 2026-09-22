import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Review {
  id: number;
  student: number;
  student_name: string;
  course: number;
  course_title: string;
  rating: number;
  comment: string;
  created_at: string;
  updated_at: string;
}

export interface CreateReviewRequest {
  course: number;
  rating: number;
  comment: string;
}

export interface UpdateReviewRequest {
  rating?: number;
  comment?: string;
}

export interface CourseRating {
  course: number;
  course_title: string;
  average_rating: number;
  total_reviews: number;
}

@Injectable({
  providedIn: 'root'
})
export class ReviewService {
  private readonly http = inject(HttpClient);

  private readonly apiUrl =
    'http://127.0.0.1:8000/api/reviews';

  getReviews(courseId?: number): Observable<Review[]> {
    if (courseId) {
      return this.http.get<Review[]>(
        `${this.apiUrl}/?course=${courseId}`
      );
    }

    return this.http.get<Review[]>(
      `${this.apiUrl}/`
    );
  }

  getReview(id: number): Observable<Review> {
    return this.http.get<Review>(
      `${this.apiUrl}/${id}/`
    );
  }

  createReview(
    data: CreateReviewRequest
  ): Observable<Review> {
    return this.http.post<Review>(
      `${this.apiUrl}/`,
      data
    );
  }

  updateReview(
    id: number,
    data: UpdateReviewRequest
  ): Observable<Review> {
    return this.http.patch<Review>(
      `${this.apiUrl}/${id}/`,
      data
    );
  }

  deleteReview(id: number): Observable<void> {
    return this.http.delete<void>(
      `${this.apiUrl}/${id}/`
    );
  }

  getCourseRating(
    courseId: number
  ): Observable<CourseRating> {
    return this.http.get<CourseRating>(
      `${this.apiUrl}/course/${courseId}/rating/`
    );
  }
} 