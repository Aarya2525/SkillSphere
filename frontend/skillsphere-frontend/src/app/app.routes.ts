import { Routes } from '@angular/router';

import { LoginComponent } from './features/auth/login/login';
import { RegisterComponent } from './features/auth/register/register';
import { DashboardComponent } from './features/dashboard/dashboard';

import { CourseListComponent } from './features/courses/course-list/course-list';
import { CourseDetailComponent } from './features/courses/course-detail/course-detail';

import { LessonDetailComponent } from './features/learning/lesson-detail/lesson-detail';
import { MyLearningComponent } from './features/learning/my-learning/my-learning';

import { QuizListComponent } from './features/quizzes/quiz-list/quiz-list';
import { QuizAttemptComponent } from './features/quizzes/quiz-attempt/quiz-attempt';
import { QuizResultComponent } from './features/quizzes/quiz-result/quiz-result';
import { QuizHistoryComponent } from './features/quizzes/quiz-history/quiz-history';
import { QuizAttemptDetailComponent } from './features/quizzes/quiz-attempt-detail/quiz-attempt-detail';

import { CertificateListComponent } from './features/certificates/certificate-list/certificate-list';
import { CertificateDetailComponent } from './features/certificates/certificate-detail/certificate-detail';
import { CertificateVerifyComponent } from './features/certificates/certificate-verify/certificate-verify';

import { ReviewsComponent } from './features/reviews/reviews';

import { NotificationsComponent } from './features/notifications/notifications/notifications';

import { InstructorDashboardComponent } from './features/instructor/instructor-dashboard/instructor-dashboard';
import { InstructorCourseManagementComponent } from './features/instructor/instructor-course-management/instructor-course-management';

import { MainLayoutComponent } from './core/layout/main-layout/main-layout';
import { authGuard, roleGuard } from './core/guards/auth-guard';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'login',
    pathMatch: 'full'
  },

  {
    path: 'login',
    component: LoginComponent
  },

  {
    path: 'register',
    component: RegisterComponent
  },

  /*
   * Public certificate verification.
   */
  {
    path: 'certificates/verify/:certificateId',
    component: CertificateVerifyComponent
  },

  /*
   * Authenticated application.
   */
  {
    path: '',
    component: MainLayoutComponent,
    canActivate: [authGuard],
    children: [

      /*
       * Student dashboard.
       */
      {
        path: 'dashboard',
        component: DashboardComponent
      },

      /*
       * Admin dashboard redirect.
       */
      {
        path: 'admin/dashboard',
        redirectTo: 'dashboard',
        pathMatch: 'full'
      },

      /*
       * Instructor dashboard.
       */
      {
        path: 'instructor/dashboard',
        component: InstructorDashboardComponent,
        canActivate: [
          roleGuard(['INSTRUCTOR'])
        ]
      },

      /*
       * Instructor courses alias.
       */
      {
        path: 'instructor/courses',
        component: InstructorDashboardComponent,
        canActivate: [
          roleGuard(['INSTRUCTOR'])
        ]
      },

      /*
       * Instructor create course.
       */
      {
        path: 'instructor/courses/create',
        component: InstructorCourseManagementComponent,
        canActivate: [
          roleGuard(['INSTRUCTOR'])
        ]
      },

      /*
       * Instructor manage course.
       */
      {
        path: 'instructor/courses/:id',
        component: InstructorCourseManagementComponent,
        canActivate: [
          roleGuard(['INSTRUCTOR'])
        ]
      },

      {
        path: 'courses',
        component: CourseListComponent
      },

      {
        path: 'courses/:id',
        component: CourseDetailComponent
      },

      {
        path: 'learning',
        component: MyLearningComponent,
        canActivate: [
          roleGuard(['STUDENT', 'ADMIN'])
        ]
      },

      {
        path: 'learning/lesson/:lessonId',
        component: LessonDetailComponent,
        canActivate: [
          roleGuard(['STUDENT', 'ADMIN'])
        ]
      },

      {
        path: 'quizzes',
        component: QuizListComponent
      },

      {
        path: 'quizzes/history',
        component: QuizHistoryComponent,
        canActivate: [
          roleGuard(['STUDENT', 'ADMIN'])
        ]
      },

      {
        path: 'quizzes/attempts/:id',
        component: QuizAttemptDetailComponent,
        canActivate: [
          roleGuard(['STUDENT', 'ADMIN'])
        ]
      },

      {
        path: 'quizzes/:id/result',
        component: QuizResultComponent,
        canActivate: [
          roleGuard(['STUDENT', 'ADMIN'])
        ]
      },

      {
        path: 'quizzes/:id',
        component: QuizAttemptComponent,
        canActivate: [
          roleGuard(['STUDENT', 'ADMIN'])
        ]
      },

      {
        path: 'certificates',
        component: CertificateListComponent
      },

      {
        path: 'certificates/:id',
        component: CertificateDetailComponent
      },

      {
        path: 'reviews',
        component: ReviewsComponent
      },

      {
        path: 'notifications',
        component: NotificationsComponent
      }

    ]
  }
]; 