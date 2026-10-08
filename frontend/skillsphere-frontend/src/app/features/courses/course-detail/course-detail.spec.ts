import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CourseDetailComponent } from './course-detail';
import { CourseService, Course, Module, Lesson } from '../../../core/services/course';
import { EnrollmentService, Enrollment } from '../../../core/services/enrollment';
import { QuizService } from '../../../core/services/quiz';
import { LearningService } from '../../../core/services/learning';
import { CertificateService } from '../../../core/services/certificate';
import { ReviewService, CourseRating } from '../../../core/services/review';
import { ActivatedRoute, Router } from '@angular/router';
import { of } from 'rxjs';

describe('CourseDetailComponent', () => {
  let component: CourseDetailComponent;
  let fixture: ComponentFixture<CourseDetailComponent>;
  let courseServiceMock: jasmine.SpyObj<CourseService>;
  let enrollmentServiceMock: jasmine.SpyObj<EnrollmentService>;
  let quizServiceMock: jasmine.SpyObj<QuizService>;
  let learningServiceMock: jasmine.SpyObj<LearningService>;
  let certificateServiceMock: jasmine.SpyObj<CertificateService>;
  let reviewServiceMock: jasmine.SpyObj<ReviewService>;
  let routerMock: jasmine.SpyObj<Router>;

  const mockCourse: Course = {
    id: 1,
    title: 'Python Essentials for Web',
    description: 'Learn modern Python programming from scratch.',
    instructor: 2,
    instructor_name: 'Dr. Jane Smith',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-02T00:00:00Z',
    is_published: true,
  };

  const mockModules: Module[] = [
    { id: 10, course: 1, title: 'Basics & Syntax', order: 1 },
    { id: 11, course: 1, title: 'OOP Fundamentals', order: 2 },
  ];

  const mockLessons: Lesson[] = [
    { id: 101, module: 10, title: 'Variables', content: 'Intro variables', order: 1 },
    { id: 102, module: 10, title: 'Loops', content: 'Intro loops', order: 2 },
    { id: 103, module: 11, title: 'Classes', content: 'Intro classes', order: 1 },
  ];

  const mockEnrollment: Enrollment = {
    id: 5,
    student: 99,
    student_name: 'teststudent',
    course: 1,
    course_title: 'Python Essentials for Web',
    enrolled_at: '2026-01-01T10:00:00Z',
  };

  const mockProgress = [
    {
      id: 201,
      student: 99,
      student_name: 'teststudent',
      lesson: 101,
      lesson_title: 'Variables',
      course_id: 1,
      is_completed: true,
      completed_at: '2026-01-02T10:00:00Z',
    },
  ];

  const mockRating: CourseRating = {
    course: 1,
    course_title: 'Python Essentials for Web',
    average_rating: 4.8,
    total_reviews: 12,
  };

  beforeEach(async () => {
    courseServiceMock = jasmine.createSpyObj('CourseService', ['getCourse', 'getModules', 'getLessons']);
    enrollmentServiceMock = jasmine.createSpyObj('EnrollmentService', ['getEnrollments', 'enroll']);
    quizServiceMock = jasmine.createSpyObj('QuizService', ['getQuizzesByCourse', 'getAttempts']);
    learningServiceMock = jasmine.createSpyObj('LearningService', ['getProgress']);
    certificateServiceMock = jasmine.createSpyObj('CertificateService', ['createCertificate']);
    reviewServiceMock = jasmine.createSpyObj('ReviewService', ['getReviews', 'getCourseRating']);
    routerMock = jasmine.createSpyObj('Router', ['navigate']);

    courseServiceMock.getCourse.and.returnValue(of(mockCourse));
    courseServiceMock.getModules.and.returnValue(of(mockModules));
    courseServiceMock.getLessons.and.returnValue(of(mockLessons));
    enrollmentServiceMock.getEnrollments.and.returnValue(of([mockEnrollment]));
    quizServiceMock.getQuizzesByCourse.and.returnValue(of([]));
    quizServiceMock.getAttempts.and.returnValue(of([]));
    learningServiceMock.getProgress.and.returnValue(of(mockProgress));
    reviewServiceMock.getReviews.and.returnValue(of([]));
    reviewServiceMock.getCourseRating.and.returnValue(of(mockRating));

    await TestBed.configureTestingModule({
      imports: [CourseDetailComponent],
      providers: [
        { provide: CourseService, useValue: courseServiceMock },
        { provide: EnrollmentService, useValue: enrollmentServiceMock },
        { provide: QuizService, useValue: quizServiceMock },
        { provide: LearningService, useValue: learningServiceMock },
        { provide: CertificateService, useValue: certificateServiceMock },
        { provide: ReviewService, useValue: reviewServiceMock },
        { provide: Router, useValue: routerMock },
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              paramMap: {
                get: (key: string) => (key === 'id' ? '1' : null),
              },
            },
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(CourseDetailComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create CourseDetailComponent', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with course details and default expand loaded modules', () => {
    expect(component.course?.title).toBe('Python Essentials for Web');
    expect(component.modules.length).toBe(2);
    expect(component.isModuleExpanded(10)).toBeTrue();
    expect(component.isModuleExpanded(11)).toBeTrue();
  });

  it('should toggle module expansion correctly', () => {
    component.toggleModule(10);
    expect(component.isModuleExpanded(10)).toBeFalse();

    component.toggleModule(10);
    expect(component.isModuleExpanded(10)).toBeTrue();
  });

  it('should track completed lessons from progress data', () => {
    expect(component.isLessonCompleted(101)).toBeTrue();
    expect(component.isLessonCompleted(102)).toBeFalse();
    expect(component.isLessonCompleted(103)).toBeFalse();
  });

  it('should format category and icon correctly', () => {
    const category = component.getCourseCategory(mockCourse);
    expect(category).toBe('Backend Development');

    const icon = component.getCourseIcon(mockCourse);
    expect(icon).toBe('⚡');
  });

  it('should navigate to lesson player when startLesson is called for enrolled student', () => {
    component.startLesson(101);
    expect(routerMock.navigate).toHaveBeenCalledWith(['/learning/lesson', 101]);
  });
});
