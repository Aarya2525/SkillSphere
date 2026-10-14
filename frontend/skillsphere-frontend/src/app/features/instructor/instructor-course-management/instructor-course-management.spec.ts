import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { ActivatedRoute, Router } from '@angular/router';

import { InstructorCourseManagementComponent } from './instructor-course-management';
import { CourseService, Course } from '../../../core/services/course';
import { QuizService } from '../../../core/services/quiz';

describe('InstructorCourseManagementComponent - Unauthorized Navigation & Error Handling', () => {
  let component: InstructorCourseManagementComponent;
  let fixture: ComponentFixture<InstructorCourseManagementComponent>;
  let mockCourseService: jasmine.SpyObj<CourseService>;
  let mockQuizService: jasmine.SpyObj<QuizService>;
  let mockRouter: jasmine.SpyObj<Router>;

  const mockCourse: Course = {
    id: 123,
    title: 'Advanced Angular Architecture',
    description: 'Master advanced frontend patterns and state management.',
    instructor: 2,
    instructor_name: 'Lead Instructor',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-02T00:00:00Z',
    is_published: true
  };

  const createTestingModule = async (routeId: string | null = '123') => {
    mockCourseService = jasmine.createSpyObj('CourseService', [
      'getCourse',
      'createCourse',
      'updateCourse',
      'getModules',
      'getLessons'
    ]);
    mockQuizService = jasmine.createSpyObj('QuizService', [
      'getQuizzesByCourse',
      'getQuizDetail'
    ]);
    mockRouter = jasmine.createSpyObj('Router', ['navigate']);

    mockCourseService.getModules.and.returnValue(of([]));
    mockCourseService.getLessons.and.returnValue(of([]));
    mockQuizService.getQuizzesByCourse.and.returnValue(of([]));

    await TestBed.configureTestingModule({
      imports: [InstructorCourseManagementComponent],
      providers: [
        { provide: CourseService, useValue: mockCourseService },
        { provide: QuizService, useValue: mockQuizService },
        { provide: Router, useValue: mockRouter },
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              paramMap: {
                get: (key: string) => (key === 'id' ? routeId : null)
              }
            }
          }
        }
      ]
    }).compileComponents();
  };

  describe('HTTP 403 Forbidden Course Load Behavior', () => {
    beforeEach(async () => {
      await createTestingModule('123');
    });

    it('should redirect to /instructor/dashboard with notification state on confirmed HTTP 403', () => {
      mockCourseService.getCourse.and.returnValue(
        throwError(() => ({ status: 403, statusText: 'Forbidden' }))
      );

      fixture = TestBed.createComponent(InstructorCourseManagementComponent);
      component = fixture.componentInstance;
      fixture.detectChanges();

      expect(mockCourseService.getCourse).toHaveBeenCalledWith(123);
      expect(component.isUnauthorized).toBeTrue();
      expect(mockRouter.navigate).toHaveBeenCalledWith(
        ['/instructor/dashboard'],
        {
          state: {
            notification: 'You do not have permission to manage this course.',
            notificationMessage: 'You do not have permission to manage this course.'
          }
        }
      );
    });

    it('should not display the invalid course editor during unauthorized redirect state', () => {
      mockCourseService.getCourse.and.returnValue(
        throwError(() => ({ status: 403, statusText: 'Forbidden' }))
      );

      fixture = TestBed.createComponent(InstructorCourseManagementComponent);
      component = fixture.componentInstance;
      fixture.detectChanges();

      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.querySelector('.course-form')).toBeNull();
      expect(compiled.querySelector('.content-management-card')).toBeNull();
      expect(compiled.querySelector('.quiz-section')).toBeNull();
      expect(compiled.textContent).toContain('Redirecting to instructor dashboard...');
    });
  });

  describe('Unrelated HTTP Error Handling (No Redirection)', () => {
    beforeEach(async () => {
      await createTestingModule('123');
    });

    it('should not redirect to /instructor/dashboard on HTTP 500 server error', () => {
      mockCourseService.getCourse.and.returnValue(
        throwError(() => ({ status: 500, statusText: 'Internal Server Error' }))
      );

      fixture = TestBed.createComponent(InstructorCourseManagementComponent);
      component = fixture.componentInstance;
      fixture.detectChanges();

      expect(mockRouter.navigate).not.toHaveBeenCalled();
      expect(component.isUnauthorized).toBeFalse();
      expect(component.errorMessage).toBe('Unable to load the course. Please try again.');

      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.querySelector('.course-form')).toBeNull();
      expect(compiled.querySelector('.alert-card.error-card')).not.toBeNull();
      expect(compiled.querySelector('.alert-content p')?.textContent).toContain(
        'Unable to load the course. Please try again.'
      );
    });

    it('should not redirect to /instructor/dashboard on network failure (status 0)', () => {
      mockCourseService.getCourse.and.returnValue(
        throwError(() => ({ status: 0, statusText: 'Unknown Error' }))
      );

      fixture = TestBed.createComponent(InstructorCourseManagementComponent);
      component = fixture.componentInstance;
      fixture.detectChanges();

      expect(mockRouter.navigate).not.toHaveBeenCalled();
      expect(component.isUnauthorized).toBeFalse();
      expect(component.errorMessage).toBe('Unable to load the course. Please try again.');
    });

    it('should not redirect to /instructor/dashboard on HTTP 404 not found error', () => {
      mockCourseService.getCourse.and.returnValue(
        throwError(() => ({ status: 404, statusText: 'Not Found' }))
      );

      fixture = TestBed.createComponent(InstructorCourseManagementComponent);
      component = fixture.componentInstance;
      fixture.detectChanges();

      expect(mockRouter.navigate).not.toHaveBeenCalled();
      expect(component.isUnauthorized).toBeFalse();
      expect(component.errorMessage).toBe('Course not found or you do not have access to it.');
      expect(fixture.nativeElement.querySelector('.course-form')).toBeNull();
    });

    it('should not redirect to /instructor/dashboard on HTTP 401 unauthorized session expiration', () => {
      mockCourseService.getCourse.and.returnValue(
        throwError(() => ({ status: 401, statusText: 'Unauthorized' }))
      );

      fixture = TestBed.createComponent(InstructorCourseManagementComponent);
      component = fixture.componentInstance;
      fixture.detectChanges();

      expect(mockRouter.navigate).not.toHaveBeenCalled();
      expect(component.isUnauthorized).toBeFalse();
      expect(component.errorMessage).toBe('Your session has expired. Please log in again.');
    });
  });

  describe('Valid Course Workflow', () => {
    beforeEach(async () => {
      await createTestingModule('123');
    });

    it('should successfully load valid course data and render the editor form without redirecting', fakeAsync(() => {
      mockCourseService.getCourse.and.returnValue(of(mockCourse));

      fixture = TestBed.createComponent(InstructorCourseManagementComponent);
      component = fixture.componentInstance;
      fixture.detectChanges();
      tick();
      fixture.detectChanges();

      expect(mockCourseService.getCourse).toHaveBeenCalledWith(123);
      expect(mockRouter.navigate).not.toHaveBeenCalled();
      expect(component.course).toEqual(mockCourse);
      expect(component.title).toBe('Advanced Angular Architecture');
      expect(component.description).toBe('Master advanced frontend patterns and state management.');
      expect(component.loading).toBeFalse();
      expect(component.isUnauthorized).toBeFalse();
      expect(component.errorMessage).toBe('');

      const compiled = fixture.nativeElement as HTMLElement;
      const titleInput = compiled.querySelector<HTMLInputElement>('#course-title');
      expect(titleInput).not.toBeNull();
      expect(titleInput?.value).toBe('Advanced Angular Architecture');
      expect(compiled.querySelector('.content-management-card')).not.toBeNull();
    }));

    it('should navigate to /instructor/dashboard without state when cancel is clicked', () => {
      mockCourseService.getCourse.and.returnValue(of(mockCourse));

      fixture = TestBed.createComponent(InstructorCourseManagementComponent);
      component = fixture.componentInstance;
      fixture.detectChanges();

      component.cancel();
      expect(mockRouter.navigate).toHaveBeenCalledWith(['/instructor/dashboard']);
    });
  });

  describe('Course Creation Workflow (No ID in Route)', () => {
    beforeEach(async () => {
      await createTestingModule(null);
    });

    it('should initialize empty create form and not attempt to fetch a course', () => {
      fixture = TestBed.createComponent(InstructorCourseManagementComponent);
      component = fixture.componentInstance;
      fixture.detectChanges();

      expect(component.isManageMode).toBeFalse();
      expect(mockCourseService.getCourse).not.toHaveBeenCalled();
      expect(mockRouter.navigate).not.toHaveBeenCalled();

      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.querySelector('.course-form')).not.toBeNull();
      expect(compiled.querySelector('.content-management-card')).toBeNull();
    });
  });
});
