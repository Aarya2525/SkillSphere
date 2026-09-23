import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { Router } from '@angular/router';

import { DashboardComponent } from './dashboard';
import { AuthService, User } from '../../core/services/auth.service';
import { EnrollmentService } from '../../core/services/enrollment';
import { LearningService } from '../../core/services/learning';
import { QuizService } from '../../core/services/quiz';
import { CourseService } from '../../core/services/course';
import { CertificateService } from '../../core/services/certificate';
import { ReviewService } from '../../core/services/review';

describe('DashboardComponent - Regression Tests', () => {
  let component: DashboardComponent;
  let fixture: ComponentFixture<DashboardComponent>;
  let mockAuthService: jasmine.SpyObj<AuthService>;
  let mockEnrollmentService: jasmine.SpyObj<EnrollmentService>;
  let mockLearningService: jasmine.SpyObj<LearningService>;
  let mockQuizService: jasmine.SpyObj<QuizService>;
  let mockCourseService: jasmine.SpyObj<CourseService>;
  let mockCertificateService: jasmine.SpyObj<CertificateService>;
  let mockReviewService: jasmine.SpyObj<ReviewService>;
  let mockRouter: jasmine.SpyObj<Router>;

  const adminUser: User = {
    id: 1,
    username: 'admin',
    email: 'admin@example.com',
    role: 'ADMIN'
  };

  const studentUser: User = {
    id: 2,
    username: 'student',
    email: 'student@example.com',
    role: 'STUDENT'
  };

  beforeEach(async () => {
    mockAuthService = jasmine.createSpyObj('AuthService', [
      'getCurrentUserSnapshot',
      'getCurrentUser'
    ]);
    mockEnrollmentService = jasmine.createSpyObj('EnrollmentService', [
      'getEnrollments'
    ]);
    mockLearningService = jasmine.createSpyObj('LearningService', [
      'getProgress'
    ]);
    mockQuizService = jasmine.createSpyObj('QuizService', [
      'getAttempts'
    ]);
    mockCourseService = jasmine.createSpyObj('CourseService', [
      'getCourses'
    ]);
    mockCertificateService = jasmine.createSpyObj('CertificateService', [
      'getCertificates'
    ]);
    mockReviewService = jasmine.createSpyObj('ReviewService', [
      'getReviews'
    ]);
    mockRouter = jasmine.createSpyObj('Router', ['navigate']);

    mockEnrollmentService.getEnrollments.and.returnValue(of([]));
    mockLearningService.getProgress.and.returnValue(of([]));
    mockQuizService.getAttempts.and.returnValue(of([]));
    mockCourseService.getCourses.and.returnValue(of([]));
    mockCertificateService.getCertificates.and.returnValue(of([]));
    mockReviewService.getReviews.and.returnValue(of([]));

    await TestBed.configureTestingModule({
      imports: [DashboardComponent],
      providers: [
        { provide: AuthService, useValue: mockAuthService },
        { provide: EnrollmentService, useValue: mockEnrollmentService },
        { provide: LearningService, useValue: mockLearningService },
        { provide: QuizService, useValue: mockQuizService },
        { provide: CourseService, useValue: mockCourseService },
        { provide: CertificateService, useValue: mockCertificateService },
        { provide: ReviewService, useValue: mockReviewService },
        { provide: Router, useValue: mockRouter }
      ]
    }).compileComponents();
  });

  it('should identify ADMIN role and activate platform management data loading', () => {
    mockAuthService.getCurrentUserSnapshot.and.returnValue(adminUser);
    mockAuthService.getCurrentUser.and.returnValue(of(adminUser));

    fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();

    expect(component.isAdmin).toBeTrue();
    expect(mockCourseService.getCourses).toHaveBeenCalled();
    expect(mockCertificateService.getCertificates).toHaveBeenCalled();
    expect(mockReviewService.getReviews).toHaveBeenCalled();
    expect(mockLearningService.getProgress).not.toHaveBeenCalled();
  });

  it('should identify STUDENT role and not activate admin console data loading', () => {
    mockAuthService.getCurrentUserSnapshot.and.returnValue(studentUser);
    mockAuthService.getCurrentUser.and.returnValue(of(studentUser));

    fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();

    expect(component.isAdmin).toBeFalse();
    expect(mockLearningService.getProgress).toHaveBeenCalled();
    expect(mockCourseService.getCourses).not.toHaveBeenCalled();
    expect(mockCertificateService.getCertificates).not.toHaveBeenCalled();
  });
});
