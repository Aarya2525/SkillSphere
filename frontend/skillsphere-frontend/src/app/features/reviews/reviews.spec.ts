import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { Router } from '@angular/router';

import { ReviewsComponent } from './reviews';
import { AuthService, User } from '../../core/services/auth.service';
import { ReviewService, Review } from '../../core/services/review';
import { EnrollmentService } from '../../core/services/enrollment';

describe('ReviewsComponent - Regression Tests', () => {
  let component: ReviewsComponent;
  let fixture: ComponentFixture<ReviewsComponent>;
  let mockAuthService: jasmine.SpyObj<AuthService>;
  let mockReviewService: jasmine.SpyObj<ReviewService>;
  let mockEnrollmentService: jasmine.SpyObj<EnrollmentService>;
  let mockRouter: jasmine.SpyObj<Router>;

  const mockUser: User = {
    id: 42,
    username: 'alice',
    email: 'alice@example.com',
    role: 'STUDENT'
  };

  beforeEach(async () => {
    mockAuthService = jasmine.createSpyObj('AuthService', [
      'getCurrentUserSnapshot',
      'getCurrentUser'
    ]);
    mockReviewService = jasmine.createSpyObj('ReviewService', [
      'getReviews',
      'createReview',
      'updateReview',
      'deleteReview'
    ]);
    mockEnrollmentService = jasmine.createSpyObj('EnrollmentService', [
      'getEnrollments'
    ]);
    mockRouter = jasmine.createSpyObj('Router', ['navigate']);

    mockAuthService.getCurrentUserSnapshot.and.returnValue(mockUser);
    mockAuthService.getCurrentUser.and.returnValue(of(mockUser));
    mockEnrollmentService.getEnrollments.and.returnValue(of([]));
    mockReviewService.getReviews.and.returnValue(of([]));

    await TestBed.configureTestingModule({
      imports: [ReviewsComponent],
      providers: [
        { provide: AuthService, useValue: mockAuthService },
        { provide: ReviewService, useValue: mockReviewService },
        { provide: EnrollmentService, useValue: mockEnrollmentService },
        { provide: Router, useValue: mockRouter }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ReviewsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should determine review ownership based on authenticated student identity, not hardcoded ID', () => {
    const ownReview: Review = {
      id: 1,
      student: 42,
      student_name: 'alice',
      course: 10,
      course_title: 'Angular Pro',
      rating: 5,
      comment: 'Loved it!',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    const otherReview: Review = {
      id: 2,
      student: 99,
      student_name: 'bob',
      course: 10,
      course_title: 'Angular Pro',
      rating: 4,
      comment: 'Good course.',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    expect(component.isOwnReview(ownReview)).toBeTrue();
    expect(component.isOwnReview(otherReview)).toBeFalse();
  });

  it('should determine review eligibility per authenticated student rather than globally across all learners', () => {
    component.reviews = [
      {
        id: 2,
        student: 99,
        student_name: 'bob',
        course: 10,
        course_title: 'Angular Pro',
        rating: 4,
        comment: 'Good course.',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
    ];

    // Current student (Alice, id: 42) has not reviewed course 10 yet
    expect(component.canReviewCourse(10)).toBeTrue();

    // After Alice submits a review for course 10
    component.reviews.push({
      id: 3,
      student: 42,
      student_name: 'alice',
      course: 10,
      course_title: 'Angular Pro',
      rating: 5,
      comment: 'Alice review.',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    });

    expect(component.canReviewCourse(10)).toBeFalse();
  });
});
