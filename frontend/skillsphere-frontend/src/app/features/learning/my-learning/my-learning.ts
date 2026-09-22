import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

import {
  EnrollmentService,
  Enrollment
} from '../../../core/services/enrollment';

import {
  CourseService,
  Module,
  Lesson
} from '../../../core/services/course';

import {
  LearningService,
  LessonProgress
} from '../../../core/services/learning';

import {
  QuizService,
  Quiz,
  QuizAttempt
} from '../../../core/services/quiz';

import {
  CertificateService
} from '../../../core/services/certificate';

interface LearningCourse {
  enrollment: Enrollment;
  modules: Module[];
  lessons: Lesson[];
  completedLessons: number;
  totalLessons: number;
  progressPercentage: number;
  nextLesson: Lesson | null;
  quiz?: Quiz | null;
  hasPassedQuiz?: boolean;
}

@Component({
  selector: 'app-my-learning',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './my-learning.html',
  styleUrl: './my-learning.scss'
})
export class MyLearningComponent implements OnInit {
  private readonly enrollmentService = inject(EnrollmentService);
  private readonly courseService = inject(CourseService);
  private readonly learningService = inject(LearningService);
  private readonly quizService = inject(QuizService);
  private readonly certificateService = inject(CertificateService);
  private readonly router = inject(Router);

  learningCourses: LearningCourse[] = [];

  loading = true;
  errorMessage = '';

  private enrollments: Enrollment[] = [];
  private modules: Module[] = [];
  private lessons: Lesson[] = [];
  private progressRecords: LessonProgress[] = [];
  private quizzes: Quiz[] = [];
  private attempts: QuizAttempt[] = [];

  ngOnInit(): void {
    this.loadMyLearning();
  }

  loadMyLearning(): void {
    this.loading = true;
    this.errorMessage = '';

    this.enrollmentService.getEnrollments().subscribe({
      next: (enrollments) => {
        this.enrollments = enrollments;

        if (enrollments.length === 0) {
          this.learningCourses = [];
          this.loading = false;
          return;
        }

        this.loadCourseData();
      },
      error: (error) => {
        console.error('Failed to load enrollments:', error);
        this.loading = false;
        this.errorMessage =
          'Unable to load your learning data. Please try again.';
      }
    });
  }

  private loadCourseData(): void {
    this.courseService.getModules().subscribe({
      next: (modules) => {
        this.modules = modules;
        this.loadLessons();
      },
      error: (error) => {
        console.error('Failed to load modules:', error);
        this.loading = false;
        this.errorMessage =
          'Unable to load course content. Please try again.';
      }
    });
  }

  private loadLessons(): void {
    this.courseService.getLessons().subscribe({
      next: (lessons) => {
        this.lessons = lessons;
        this.loadProgress();
      },
      error: (error) => {
        console.error('Failed to load lessons:', error);
        this.loading = false;
        this.errorMessage =
          'Unable to load lessons. Please try again.';
      }
    });
  }

  private loadProgress(): void {
    this.learningService.getProgress().subscribe({
      next: (progressRecords) => {
        this.progressRecords = progressRecords;
        this.loadQuizzesAndAttempts();
      },
      error: (error) => {
        console.error('Failed to load progress:', error);
        this.loading = false;
        this.errorMessage =
          'Unable to load your progress. Please try again.';
      }
    });
  }

  private loadQuizzesAndAttempts(): void {
    this.quizService.getQuizzes().subscribe({
      next: (quizzes) => {
        this.quizzes = quizzes;
        this.quizService.getAttempts().subscribe({
          next: (attempts) => {
            this.attempts = attempts;
            this.buildLearningCourses();
            this.loading = false;
          },
          error: () => {
            this.buildLearningCourses();
            this.loading = false;
          }
        });
      },
      error: () => {
        this.buildLearningCourses();
        this.loading = false;
      }
    });
  }

  private buildLearningCourses(): void {
    this.learningCourses = this.enrollments.map((enrollment) => {
      const courseModules = this.modules
        .filter((module) => module.course === enrollment.course)
        .sort((a, b) => a.order - b.order);

      const moduleIds = courseModules.map((module) => module.id);

      const courseLessons = this.lessons
        .filter((lesson) => moduleIds.includes(lesson.module))
        .sort((a, b) => a.order - b.order);

      const courseProgress = this.progressRecords.filter(
        (progress) => progress.course_id === enrollment.course
      );

      const completedLessons = courseLessons.filter((lesson) =>
        courseProgress.some(
          (progress) =>
            progress.lesson === lesson.id &&
            progress.is_completed
        )
      ).length;

      const totalLessons = courseLessons.length;

      const progressPercentage =
        totalLessons > 0
          ? Math.round((completedLessons / totalLessons) * 100)
          : 0;

      const nextLesson =
        courseLessons.find((lesson) =>
          !courseProgress.some(
            (progress) =>
              progress.lesson === lesson.id &&
              progress.is_completed
          )
        ) ?? null;

      const courseQuiz =
        this.quizzes.find((q) => q.course === enrollment.course) ?? null;

      const hasPassedQuiz = courseQuiz
        ? this.attempts.some(
            (a) => a.quiz === courseQuiz.id && a.is_passed
          )
        : false;

      return {
        enrollment,
        modules: courseModules,
        lessons: courseLessons,
        completedLessons,
        totalLessons,
        progressPercentage,
        nextLesson,
        quiz: courseQuiz,
        hasPassedQuiz
      };
    });
  }

  takeQuiz(quizId: number): void {
    this.router.navigate(['/quizzes', quizId]);
  }

  viewCertificates(): void {
    this.router.navigate(['/certificates']);
  }

  continueLearning(course: LearningCourse): void {
    if (course.nextLesson) {
      this.router.navigate([
        '/learning/lesson',
        course.nextLesson.id
      ]);
      return;
    }

    this.router.navigate([
      '/courses',
      course.enrollment.course
    ]);
  }

  viewCourse(courseId: number): void {
    this.router.navigate(['/courses', courseId]);
  }

  getProgressLabel(course: LearningCourse): string {
    if (course.totalLessons === 0) {
      return 'No lessons available';
    }

    if (course.progressPercentage === 100) {
      return 'Course completed';
    }

    return `${course.completedLessons} of ${course.totalLessons} lessons completed`;
  }
} 