import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { ActivatedRoute, Router } from '@angular/router';

import { InstructorDashboardComponent } from './instructor-dashboard';
import { CourseService, Course } from '../../../core/services/course';

describe('InstructorDashboardComponent - Notifications & Course Management', () => {
  let component: InstructorDashboardComponent;
  let fixture: ComponentFixture<InstructorDashboardComponent>;
  let mockCourseService: jasmine.SpyObj<CourseService>;
  let mockRouter: jasmine.SpyObj<Router>;

  const mockCourses: Course[] = [
    {
      id: 1,
      title: 'Python for Beginners',
      description: 'Learn fundamental Python programming concepts.',
      instructor: 10,
      instructor_name: 'Test Instructor',
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-02T00:00:00Z',
      is_published: true
    },
    {
      id: 2,
      title: 'Django REST Framework Deep Dive',
      description: 'Build enterprise-grade REST APIs with DRF.',
      instructor: 10,
      instructor_name: 'Test Instructor',
      created_at: '2026-01-05T00:00:00Z',
      updated_at: '2026-01-06T00:00:00Z',
      is_published: false
    }
  ];

  const configureTestingModule = async (
    navState: Record<string, unknown> | null = null,
    coursesResponse: { data?: Course[]; error?: any } = { data: mockCourses }
  ) => {
    mockCourseService = jasmine.createSpyObj('CourseService', ['getCourses']);
    mockRouter = jasmine.createSpyObj('Router', [
      'getCurrentNavigation',
      'navigate',
      'createUrlTree',
      'serializeUrl'
    ]);

    if (coursesResponse.error) {
      mockCourseService.getCourses.and.returnValue(
        throwError(() => coursesResponse.error)
      );
    } else {
      mockCourseService.getCourses.and.returnValue(
        of(coursesResponse.data ?? [])
      );
    }

    mockRouter.createUrlTree.and.returnValue({} as any);
    mockRouter.serializeUrl.and.returnValue('/test-url');
    (mockRouter as any).events = of();
    mockRouter.getCurrentNavigation.and.returnValue(
      navState ? ({ extras: { state: navState } } as any) : null
    );

    await TestBed.configureTestingModule({
      imports: [InstructorDashboardComponent],
      providers: [
        { provide: CourseService, useValue: mockCourseService },
        { provide: Router, useValue: mockRouter },
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              queryParamMap: {
                get: () => null
              }
            }
          }
        }
      ]
    }).compileComponents();
  };

  afterEach(() => {
    // Clean up any history state modifications
    if (typeof history !== 'undefined' && history.replaceState) {
      history.replaceState({}, document.title);
    }
  });

  describe('Notification Banner Handling', () => {
    it('should extract and display accessible notification banner from navigation state', async () => {
      const message = 'You do not have permission to manage this course.';
      await configureTestingModule({ notificationMessage: message });

      fixture = TestBed.createComponent(InstructorDashboardComponent);
      component = fixture.componentInstance;
      fixture.detectChanges();

      expect(component.notificationMessage).toBe(message);

      const compiled = fixture.nativeElement as HTMLElement;
      const banner = compiled.querySelector('.alert-card.error-card.notification-banner');
      expect(banner).not.toBeNull();
      expect(banner?.getAttribute('role')).toBe('alert');
      expect(banner?.getAttribute('aria-live')).toBe('polite');
      expect(banner?.textContent).toContain(message);
      expect(banner?.textContent).toContain('Access Denied');
    });

    it('should dismiss notification banner when dismiss button is clicked', async () => {
      const message = 'You do not have permission to manage this course.';
      await configureTestingModule({ notification: message });

      fixture = TestBed.createComponent(InstructorDashboardComponent);
      component = fixture.componentInstance;
      fixture.detectChanges();

      const compiled = fixture.nativeElement as HTMLElement;
      const dismissBtn = compiled.querySelector<HTMLButtonElement>('.alert-dismiss');
      expect(dismissBtn).not.toBeNull();

      dismissBtn?.click();
      fixture.detectChanges();

      expect(component.notificationMessage).toBe('');
      expect(compiled.querySelector('.alert-card.error-card.notification-banner')).toBeNull();
    });

    it('should not display notification banner when no notification state is provided', async () => {
      await configureTestingModule(null);

      fixture = TestBed.createComponent(InstructorDashboardComponent);
      component = fixture.componentInstance;
      fixture.detectChanges();

      expect(component.notificationMessage).toBe('');
      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.querySelector('.alert-card.error-card.notification-banner')).toBeNull();
    });
  });

  describe('Course Data and Dashboard Functionality', () => {
    it('should load and render instructor courses even when a notification banner is active', async () => {
      await configureTestingModule({ notificationMessage: 'You do not have permission to manage this course.' });

      fixture = TestBed.createComponent(InstructorDashboardComponent);
      component = fixture.componentInstance;
      fixture.detectChanges();

      expect(mockCourseService.getCourses).toHaveBeenCalled();
      expect(component.courses.length).toBe(2);
      expect(component.publishedCourseCount).toBe(1);
      expect(component.draftCourseCount).toBe(1);
      expect(component.loading).toBeFalse();

      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.querySelector('.alert-card.error-card.notification-banner')).not.toBeNull();
      expect(compiled.querySelectorAll('.course-card').length).toBe(2);
    });

    it('should render empty state when instructor has zero courses and no error occurred', async () => {
      await configureTestingModule(null, { data: [] });

      fixture = TestBed.createComponent(InstructorDashboardComponent);
      component = fixture.componentInstance;
      fixture.detectChanges();

      expect(component.courses.length).toBe(0);
      expect(component.loading).toBeFalse();

      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.querySelector('.empty-card')).not.toBeNull();
    });

    it('should render error card when loading instructor courses fails', async () => {
      await configureTestingModule(null, {
        error: { status: 500, statusText: 'Server Error' }
      });

      fixture = TestBed.createComponent(InstructorDashboardComponent);
      component = fixture.componentInstance;
      fixture.detectChanges();

      expect(component.loading).toBeFalse();
      expect(component.errorMessage).toBe('Unable to load your courses. Please try again.');

      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.querySelector('.error-card h2')?.textContent).toContain('Something went wrong');
    });
  });
});
