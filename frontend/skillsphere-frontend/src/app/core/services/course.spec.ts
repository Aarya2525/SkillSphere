import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { CourseService, Course } from './course';
import { environment } from '../../../environments/environment';

describe('CourseService', () => {
  let service: CourseService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        CourseService,
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    });
    service = TestBed.inject(CourseService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('getCourses should fetch courses list', () => {
    const mockCourses: Course[] = [
      {
        id: 1,
        instructor: 1,
        instructor_name: 'Dr. Smith',
        title: 'Angular Basics',
        description: 'Learn Angular',
        is_published: true,
        created_at: '2026-01-01',
        updated_at: '2026-01-02'
      }
    ];

    service.getCourses().subscribe(courses => {
      expect(courses.length).toBe(1);
      expect(courses[0].title).toBe('Angular Basics');
    });

    const req = httpMock.expectOne(`${environment.apiUrl}/courses/`);
    expect(req.request.method).toBe('GET');
    req.flush(mockCourses);
  });

  it('createCourse should post new course data', () => {
    const newCourse = { title: 'New Course', description: 'Desc' };
    const mockCreatedCourse: Course = {
      id: 2,
      instructor: 1,
      instructor_name: 'Dr. Smith',
      title: 'New Course',
      description: 'Desc',
      is_published: false,
      created_at: '2026-01-01',
      updated_at: '2026-01-01'
    };

    service.createCourse(newCourse).subscribe(course => {
      expect(course.id).toBe(2);
      expect(course.title).toBe('New Course');
    });

    const req = httpMock.expectOne(`${environment.apiUrl}/courses/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(newCourse);
    req.flush(mockCreatedCourse);
  });

  it('deleteCourse should send DELETE request', () => {
    service.deleteCourse(1).subscribe();

    const req = httpMock.expectOne(`${environment.apiUrl}/courses/1/`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });
});
