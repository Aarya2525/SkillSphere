import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { ActivatedRoute, Router, convertToParamMap } from '@angular/router';

import { LessonDetailComponent } from './lesson-detail';
import { CourseService, Course, Module, Lesson } from '../../../core/services/course';
import { LearningService, LessonProgress } from '../../../core/services/learning';
import { QuizService } from '../../../core/services/quiz';
import { AIAssistantService } from '../../../core/services/ai-assistant.service';

describe('LessonDetailComponent - P1 UX & Safe Content Tests', () => {
  let component: LessonDetailComponent;
  let fixture: ComponentFixture<LessonDetailComponent>;

  let mockCourseService: jasmine.SpyObj<CourseService>;
  let mockLearningService: jasmine.SpyObj<LearningService>;
  let mockQuizService: jasmine.SpyObj<QuizService>;
  let mockAIAssistantService: jasmine.SpyObj<AIAssistantService>;
  let mockRouter: jasmine.SpyObj<Router>;

  const mockLesson: Lesson = {
    id: 1,
    title: 'Introduction to Angular Standalone',
    content: '### Core Architecture\n\nAngular standalone components eliminate NgModules.\n\n- Simplified setup\n- Direct tree shaking',
    module: 10,
    order: 1
  };

  const mockModule: Module = {
    id: 10,
    title: 'Getting Started',
    course: 100,
    order: 1
  };

  const mockCourse: Course = {
    id: 100,
    title: 'Angular Mastery Course',
    description: 'Master Angular 20.',
    instructor: 1,
    instructor_name: 'Lead Instructor',
    is_published: true,
    created_at: '2026-01-01',
    updated_at: '2026-01-01'
  };

  const mockProgress: LessonProgress[] = [
    {
      id: 50,
      student: 1,
      student_name: 'Test Student',
      lesson: 1,
      lesson_title: 'Introduction to Angular Standalone',
      course_id: 100,
      is_completed: false,
      completed_at: null
    }
  ];

  beforeEach(async () => {
    mockCourseService = jasmine.createSpyObj('CourseService', [
      'getLesson',
      'getModule',
      'getCourse',
      'getModules',
      'getLessons'
    ]);
    mockLearningService = jasmine.createSpyObj('LearningService', [
      'getProgress',
      'createProgress',
      'updateProgress'
    ]);
    mockQuizService = jasmine.createSpyObj('QuizService', [
      'getQuizzesByCourse',
      'getAttempts'
    ]);
    mockAIAssistantService = jasmine.createSpyObj('AIAssistantService', ['askQuestion']);
    mockRouter = jasmine.createSpyObj('Router', ['navigate']);

    mockCourseService.getLesson.and.returnValue(of(mockLesson));
    mockCourseService.getModule.and.returnValue(of(mockModule));
    mockCourseService.getCourse.and.returnValue(of(mockCourse));
    mockCourseService.getModules.and.returnValue(of([mockModule]));
    mockCourseService.getLessons.and.returnValue(of([mockLesson]));

    mockLearningService.getProgress.and.returnValue(of(mockProgress));
    mockQuizService.getQuizzesByCourse.and.returnValue(of([]));
    mockQuizService.getAttempts.and.returnValue(of([]));

    await TestBed.configureTestingModule({
      imports: [LessonDetailComponent],
      providers: [
        { provide: CourseService, useValue: mockCourseService },
        { provide: LearningService, useValue: mockLearningService },
        { provide: QuizService, useValue: mockQuizService },
        { provide: AIAssistantService, useValue: mockAIAssistantService },
        { provide: Router, useValue: mockRouter },
        {
          provide: ActivatedRoute,
          useValue: {
            paramMap: of(convertToParamMap({ lessonId: '1' }))
          }
        }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(LessonDetailComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create and load lesson data', () => {
    expect(component).toBeTruthy();
    expect(component.lesson).toEqual(mockLesson);
    expect(component.course).toEqual(mockCourse);
    expect(component.loading).toBeFalse();
  });

  it('should render safe formatted lesson content via SafeContentPipe', () => {
    const contentBody = fixture.nativeElement.querySelector('.lesson-content-body');
    expect(contentBody).toBeTruthy();
    expect(contentBody.innerHTML).toContain('<h3 class="lesson-subheading">Core Architecture</h3>');
    expect(contentBody.innerHTML).toContain('<ul class="lesson-bullet-list">');
    expect(contentBody.innerHTML).toContain('<li>Simplified setup</li>');
  });

  it('should toggle mobile curriculum drawer open and closed', () => {
    expect(component.sidebarOpen).toBeFalse();

    component.toggleSidebar();
    fixture.detectChanges();
    expect(component.sidebarOpen).toBeTrue();

    // Verify backdrop is rendered when drawer is open
    const backdrop = fixture.nativeElement.querySelector('.curriculum-backdrop');
    expect(backdrop).toBeTruthy();

    // Clicking backdrop should close drawer
    backdrop.click();
    fixture.detectChanges();
    expect(component.sidebarOpen).toBeFalse();
  });

  it('should close mobile curriculum drawer when Escape key is pressed', () => {
    component.sidebarOpen = true;
    fixture.detectChanges();

    // Trigger window:keydown.escape
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
    fixture.detectChanges();

    expect(component.sidebarOpen).toBeFalse();
  });

  it('should allow marking lesson as complete and update progress', () => {
    const updatedProgress: LessonProgress = {
      id: 50,
      student: 1,
      student_name: 'Test Student',
      lesson: 1,
      lesson_title: 'Introduction to Angular Standalone',
      course_id: 100,
      is_completed: true,
      completed_at: '2026-01-01'
    };
    mockLearningService.updateProgress.and.returnValue(of(updatedProgress));

    component.markAsComplete();
    fixture.detectChanges();

    expect(mockLearningService.updateProgress).toHaveBeenCalledWith(50, { is_completed: true });
    expect(component.progress?.is_completed).toBeTrue();
  });
});
