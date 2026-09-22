import {
  Component,
  OnInit,
  inject
} from '@angular/core';

import { CommonModule } from '@angular/common';

import {
  ActivatedRoute,
  Router
} from '@angular/router';

import {
  CourseService,
  Course,
  Module,
  Lesson
} from '../../../core/services/course';

import {
  EnrollmentService,
  Enrollment
} from '../../../core/services/enrollment';

import {
  QuizService,
  Quiz,
  QuizAttempt
} from '../../../core/services/quiz';

import {
  LearningService
} from '../../../core/services/learning';

import {
  CertificateService
} from '../../../core/services/certificate';

@Component({
  selector: 'app-course-detail',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './course-detail.html',
  styleUrl: './course-detail.scss'
})
export class CourseDetailComponent
  implements OnInit {

  private readonly courseService =
    inject(CourseService);

  private readonly enrollmentService =
    inject(EnrollmentService);

  private readonly quizService =
    inject(QuizService);

  private readonly learningService =
    inject(LearningService);

  private readonly certificateService =
    inject(CertificateService);

  private readonly route =
    inject(ActivatedRoute);

  private readonly router =
    inject(Router);

  course: Course | null = null;

  modules: Module[] = [];

  lessons: Lesson[] = [];

  enrollment: Enrollment | null = null;

  quiz: Quiz | null = null;
  quizLoading = false;
  hasPassedQuiz = false;
  latestAttempt: QuizAttempt | null = null;
  completedLessons = 0;
  claimingCertificate = false;

  loading = true;

  enrolling = false;

  errorMessage = '';

  successMessage = '';

  private courseId: number | null = null;

  ngOnInit(): void {

    const courseId =
      Number(
        this.route.snapshot.paramMap.get('id')
      );

    if (!courseId) {

      this.loading = false;

      this.errorMessage =
        'Invalid course.';

      return;
    }

    this.courseId = courseId;

    this.loadCourse(courseId);

    this.loadModules(courseId);

    this.loadLessons();

    this.loadEnrollment();

    this.loadCourseQuiz(courseId);

    this.loadLessonProgress();
  }

  loadCourse(courseId: number): void {

    this.courseService
      .getCourse(courseId)
      .subscribe({

        next: (course: Course) => {

          this.course = course;

          this.checkLoadingComplete();
        },

        error: (error) => {

          console.error(
            'Failed to load course:',
            error
          );

          this.loading = false;

          this.errorMessage =
            'Unable to load the course. Please try again.';
        }
      });
  }

  loadModules(courseId: number): void {

    this.courseService
      .getModules()
      .subscribe({

        next: (modules: Module[]) => {

          this.modules =
            modules.filter(
              module =>
                module.course === courseId
            );

          this.checkLoadingComplete();
        },

        error: (error) => {

          console.error(
            'Failed to load modules:',
            error
          );

          this.loading = false;

          this.errorMessage =
            'Unable to load course modules.';
        }
      });
  }

  loadLessons(): void {

    this.courseService
      .getLessons()
      .subscribe({

        next: (lessons: Lesson[]) => {

          this.lessons = lessons;

          this.checkLoadingComplete();
        },

        error: (error) => {

          console.error(
            'Failed to load lessons:',
            error
          );

          this.loading = false;

          this.errorMessage =
            'Unable to load course lessons.';
        }
      });
  }

  loadEnrollment(): void {

    this.enrollmentService
      .getEnrollments()
      .subscribe({

        next: (enrollments: Enrollment[]) => {

          if (this.courseId === null) {
            return;
          }

          this.enrollment =
            enrollments.find(
              enrollment =>
                enrollment.course === this.courseId
            ) ?? null;
        },

        error: (error) => {

          console.error(
            'Failed to load enrollments:',
            error
          );

          /*
           * Enrollment lookup should not prevent
           * the course itself from loading.
           */
        }
      });
  }

  checkLoadingComplete(): void {

    if (
      this.course !== null &&
      this.modules !== undefined &&
      this.lessons !== undefined
    ) {

      this.loading = false;
    }
  }

  getLessonsForModule(
    moduleId: number
  ): Lesson[] {

    return this.lessons
      .filter(
        lesson =>
          lesson.module === moduleId
      )
      .sort(
        (a, b) =>
          a.order - b.order
      );
  }

  get isEnrolled(): boolean {
    return this.enrollment !== null;
  }

  enroll(): void {

    if (
      this.enrolling ||
      this.courseId === null ||
      this.isEnrolled
    ) {
      return;
    }

    this.enrolling = true;

    this.errorMessage = '';

    this.successMessage = '';

    this.enrollmentService
      .createEnrollment({
        course: this.courseId
      })
      .subscribe({

        next: (enrollment: Enrollment) => {

          this.enrollment =
            enrollment;

          this.enrolling = false;

          this.successMessage =
            'You are now enrolled in this course.';

          if (this.courseId !== null) {
            this.loadCourseQuiz(this.courseId);
            this.loadLessonProgress();
          }
        },

        error: (error) => {

          console.error(
            'Failed to enroll in course:',
            error
          );

          this.enrolling = false;

          if (error.status === 400) {

            this.errorMessage =
              'You are already enrolled in this course.';

            this.loadEnrollment();

          } else if (error.status === 403) {

            this.errorMessage =
              'You cannot enroll in this course.';

          } else if (error.status === 401) {

            this.errorMessage =
              'Your session has expired. Please log in again.';

          } else {

            this.errorMessage =
              'Unable to enroll in this course. Please try again.';
          }
        }
      });
  }

  startLesson(lessonId: number): void {

    if (!this.isEnrolled) {

      this.errorMessage =
        'Please enroll in this course before starting a lesson.';

      return;
    }

    this.router.navigate([
      '/learning/lesson',
      lessonId
    ]);
  }

  goToLearning(): void {

    this.router.navigate([
      '/learning'
    ]);
  }

  goBack(): void {

    this.router.navigate([
      '/courses'
    ]);
  }

  // --------------------------------------------------
  // QUIZ & CERTIFICATE INTEGRATION
  // --------------------------------------------------

  loadCourseQuiz(courseId: number): void {
    this.quizLoading = true;
    this.quizService.getQuizzesByCourse(courseId).subscribe({
      next: (quizzes) => {
        const published = quizzes.find(q => q.is_published);
        this.quiz = published ?? null;
        this.quizLoading = false;

        if (this.quiz) {
          this.loadQuizAttempts(this.quiz.id);
        }
      },
      error: () => {
        this.quiz = null;
        this.quizLoading = false;
      }
    });
  }

  loadQuizAttempts(quizId: number): void {
    this.quizService.getAttempts().subscribe({
      next: (attempts) => {
        const quizAttempts = attempts.filter(a => a.quiz === quizId);
        if (quizAttempts.length > 0) {
          this.latestAttempt = quizAttempts[0];
          this.hasPassedQuiz = quizAttempts.some(a => a.is_passed);
        }
      }
    });
  }

  loadLessonProgress(): void {
    this.learningService.getProgress().subscribe({
      next: (progressList) => {
        const courseLessonIds = this.lessons.map(l => l.id);
        this.completedLessons = progressList.filter(
          p => courseLessonIds.includes(p.lesson) && p.is_completed
        ).length;
      }
    });
  }

  get allLessonsCompleted(): boolean {
    return this.lessons.length > 0 && this.completedLessons >= this.lessons.length;
  }

  takeQuiz(): void {
    if (!this.quiz) return;
    this.router.navigate(['/quizzes', this.quiz.id]);
  }

  claimCertificate(): void {
    if (!this.courseId || this.claimingCertificate) return;
    this.claimingCertificate = true;
    this.errorMessage = '';
    this.successMessage = '';

    this.certificateService.createCertificate({
      course: this.courseId
    }).subscribe({
      next: (res) => {
        this.claimingCertificate = false;
        this.successMessage = 'Certificate earned! Navigating to your certificate...';
        setTimeout(() => {
          this.router.navigate(['/certificates', res.certificate.id]);
        }, 1000);
      },
      error: (err) => {
        this.claimingCertificate = false;
        if (err.error?.error) {
          this.errorMessage = err.error.error;
        } else {
          this.errorMessage = 'Unable to claim certificate. Please ensure all lessons are completed and the quiz is passed.';
        }
      }
    });
  }
} 