import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { Router } from '@angular/router';

import { CourseListComponent } from './course-list';
import { CourseService, Course } from '../../../core/services/course';
import { EnrollmentService, Enrollment } from '../../../core/services/enrollment';

describe('CourseListComponent', () => {
  let component: CourseListComponent;
  let fixture: ComponentFixture<CourseListComponent>;
  let mockCourseService: jasmine.SpyObj<CourseService>;
  let mockEnrollmentService: jasmine.SpyObj<EnrollmentService>;
  let mockRouter: jasmine.SpyObj<Router>;

  const mockCourses: Course[] = [
    {
      id: 1,
      title: 'Python & Django API Mastery',
      description: 'Build production REST APIs with Django and PostgreSQL.',
      instructor: 10,
      instructor_name: 'Guido Dev',
      is_published: true,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z'
    },
    {
      id: 2,
      title: 'Modern Angular Frontend Architecture',
      description: 'State management and responsive web applications.',
      instructor: 11,
      instructor_name: 'Misko Smith',
      is_published: true,
      created_at: '2026-01-02T00:00:00Z',
      updated_at: '2026-01-02T00:00:00Z'
    },
    {
      id: 3,
      title: 'Advanced Machine Learning & AI',
      description: 'Neural networks, embeddings, and intelligent agents.',
      instructor: 12,
      instructor_name: 'Ada Lovelace',
      is_published: true,
      created_at: '2026-01-03T00:00:00Z',
      updated_at: '2026-01-03T00:00:00Z'
    }
  ];

  const mockEnrollments: Enrollment[] = [
    {
      id: 101,
      student: 1,
      student_name: 'Student One',
      course: 1,
      course_title: 'Python & Django API Mastery',
      enrolled_at: '2026-01-05T00:00:00Z'
    }
  ];

  beforeEach(async () => {
    mockCourseService = jasmine.createSpyObj('CourseService', ['getCourses']);
    mockEnrollmentService = jasmine.createSpyObj('EnrollmentService', ['getEnrollments']);
    mockRouter = jasmine.createSpyObj('Router', ['navigate']);

    mockCourseService.getCourses.and.returnValue(of(mockCourses));
    mockEnrollmentService.getEnrollments.and.returnValue(of(mockEnrollments));

    await TestBed.configureTestingModule({
      imports: [CourseListComponent],
      providers: [
        { provide: CourseService, useValue: mockCourseService },
        { provide: EnrollmentService, useValue: mockEnrollmentService },
        { provide: Router, useValue: mockRouter }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(CourseListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create and load catalog data', () => {
    expect(component).toBeTruthy();
    expect(component.courses.length).toBe(3);
    expect(component.enrollments.length).toBe(1);
    expect(component.loading).toBeFalse();
  });

  it('should render course cards with gradient thumbnails and metadata chips', () => {
    const cards = fixture.nativeElement.querySelectorAll('.course-card');
    expect(cards.length).toBe(3);

    const firstCard = cards[0];
    expect(firstCard.querySelector('.course-thumbnail')).toBeTruthy();
    expect(firstCard.querySelector('.category-pill').textContent).toContain('Backend Development');
    expect(firstCard.querySelector('.enrolled-badge')).toBeTruthy();
    expect(firstCard.querySelector('.difficulty-chip')).toBeTruthy();
  });

  it('should filter courses by search term', () => {
    component.searchTerm = 'Angular';
    fixture.detectChanges();

    expect(component.filteredCourses.length).toBe(1);
    expect(component.filteredCourses[0].title).toContain('Modern Angular');
  });

  it('should filter courses by tab (ALL, ENROLLED, AVAILABLE)', () => {
    component.setActiveTab('ENROLLED');
    expect(component.filteredCourses.length).toBe(1);
    expect(component.filteredCourses[0].id).toBe(1);

    component.setActiveTab('AVAILABLE');
    expect(component.filteredCourses.length).toBe(2);

    component.setActiveTab('ALL');
    expect(component.filteredCourses.length).toBe(3);
  });

  it('should clear search term when clearSearch is called', () => {
    component.searchTerm = 'Python';
    component.clearSearch();
    expect(component.searchTerm).toBe('');
    expect(component.filteredCourses.length).toBe(3);
  });

  it('should correctly infer course categories and icons', () => {
    expect(component.getCourseCategory(mockCourses[0])).toBe('Backend Development');
    expect(component.getCourseIcon(mockCourses[0])).toBe('⚡');

    expect(component.getCourseCategory(mockCourses[1])).toBe('Web Development');
    expect(component.getCourseIcon(mockCourses[1])).toBe('🌐');

    expect(component.getCourseCategory(mockCourses[2])).toBe('Data & AI');
    expect(component.getCourseIcon(mockCourses[2])).toBe('🧠');
  });

  it('should navigate to course detail when viewCourse is invoked', () => {
    component.viewCourse(2);
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/courses', 2]);
  });
});
