import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Course {
  id: number;
  instructor: number;
  instructor_name: string;
  title: string;
  description: string;
  is_published: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateCourseRequest {
  title: string;
  description: string;
}

export interface Module {
  id: number;
  course: number;
  title: string;
  order: number;
}

export interface CreateModuleRequest {
  course: number;
  title: string;
  order: number;
}

export interface Lesson {
  id: number;
  module: number;
  title: string;
  content: string;
  order: number;
}

export interface CreateLessonRequest {
  module: number;
  title: string;
  content: string;
  order: number;
}

@Injectable({
  providedIn: 'root'
})
export class CourseService {
  private readonly http = inject(HttpClient);

  private readonly apiUrl =
    'http://127.0.0.1:8000/api/courses';

  // --------------------------------------------------
  // COURSES
  // --------------------------------------------------

  getCourses(): Observable<Course[]> {
    return this.http.get<Course[]>(
      `${this.apiUrl}/`
    );
  }

  getCourse(id: number): Observable<Course> {
    return this.http.get<Course>(
      `${this.apiUrl}/${id}/`
    );
  }

  createCourse(
    data: CreateCourseRequest
  ): Observable<Course> {
    return this.http.post<Course>(
      `${this.apiUrl}/`,
      data
    );
  }

  updateCourse(
    id: number,
    data: Partial<CreateCourseRequest>
  ): Observable<Course> {
    return this.http.patch<Course>(
      `${this.apiUrl}/${id}/`,
      data
    );
  }

  deleteCourse(
    id: number
  ): Observable<void> {
    return this.http.delete<void>(
      `${this.apiUrl}/${id}/`
    );
  }

  // --------------------------------------------------
  // MODULES
  // --------------------------------------------------

  getModules(): Observable<Module[]> {
    return this.http.get<Module[]>(
      `${this.apiUrl}/modules/`
    );
  }

  getModule(id: number): Observable<Module> {
    return this.http.get<Module>(
      `${this.apiUrl}/modules/${id}/`
    );
  }

  createModule(
    data: CreateModuleRequest
  ): Observable<Module> {
    return this.http.post<Module>(
      `${this.apiUrl}/modules/`,
      data
    );
  }

  updateModule(
    id: number,
    data: Partial<CreateModuleRequest>
  ): Observable<Module> {
    return this.http.patch<Module>(
      `${this.apiUrl}/modules/${id}/`,
      data
    );
  }

  deleteModule(
    id: number
  ): Observable<void> {
    return this.http.delete<void>(
      `${this.apiUrl}/modules/${id}/`
    );
  }

  // --------------------------------------------------
  // LESSONS
  // --------------------------------------------------

  getLessons(): Observable<Lesson[]> {
    return this.http.get<Lesson[]>(
      `${this.apiUrl}/lessons/`
    );
  }

  getLesson(id: number): Observable<Lesson> {
    return this.http.get<Lesson>(
      `${this.apiUrl}/lessons/${id}/`
    );
  }

  createLesson(
    data: CreateLessonRequest
  ): Observable<Lesson> {
    return this.http.post<Lesson>(
      `${this.apiUrl}/lessons/`,
      data
    );
  }

  updateLesson(
    id: number,
    data: Partial<CreateLessonRequest>
  ): Observable<Lesson> {
    return this.http.patch<Lesson>(
      `${this.apiUrl}/lessons/${id}/`,
      data
    );
  }

  deleteLesson(
    id: number
  ): Observable<void> {
    return this.http.delete<void>(
      `${this.apiUrl}/lessons/${id}/`
    );
  }
} 