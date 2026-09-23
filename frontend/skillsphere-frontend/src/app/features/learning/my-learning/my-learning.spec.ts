import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { Router } from '@angular/router';

import { MyLearningComponent } from './my-learning';
import { EnrollmentService } from '../../../core/services/enrollment';
import { CourseService } from '../../../core/services/course';
import { LearningService } from '../../../core/services/learning';
import { QuizService } from '../../../core/services/quiz';
import { CertificateService } from '../../../core/services/certificate';

describe('MyLearningComponent - Regression Tests', () => {
  let component: MyLearningComponent;
  let fixture: ComponentFixture<MyLearningComponent>;
  let mockEnrollmentService: jasmine.SpyObj<EnrollmentService>;
  let mockCourseService: jasmine.SpyObj<CourseService>;
  let mockLearningService: jasmine.SpyObj<LearningService>;
  let mockQuizService: jasmine.SpyObj<QuizService>;
  let mockCertificateService: jasmine.SpyObj<CertificateService>;
  let mockRouter: jasmine.SpyObj<Router>;

  beforeEach(async () => {
    mockEnrollmentService = jasmine.createSpyObj('EnrollmentService', [
      'getEnrollments'
    ]);
    mockCourseService = jasmine.createSpyObj('CourseService', [
      'getCourse'
    ]);
    mockLearningService = jasmine.createSpyObj('LearningService', [
      'getProgress'
    ]);
    mockQuizService = jasmine.createSpyObj('QuizService', [
      'getQuizzesByCourse',
      'getAttempts'
    ]);
    mockCertificateService = jasmine.createSpyObj('CertificateService', [
      'getCertificates'
    ]);
    mockRouter = jasmine.createSpyObj('Router', ['navigate']);

    mockEnrollmentService.getEnrollments.and.returnValue(of([]));
    mockQuizService.getAttempts.and.returnValue(of([]));
    mockCertificateService.getCertificates.and.returnValue(of([]));

    await TestBed.configureTestingModule({
      imports: [MyLearningComponent],
      providers: [
        { provide: EnrollmentService, useValue: mockEnrollmentService },
        { provide: CourseService, useValue: mockCourseService },
        { provide: LearningService, useValue: mockLearningService },
        { provide: QuizService, useValue: mockQuizService },
        { provide: CertificateService, useValue: mockCertificateService },
        { provide: Router, useValue: mockRouter }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(MyLearningComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should navigate to /courses when empty-state Explore Courses action is triggered', () => {
    component.goToCourses();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/courses']);
  });
});
