import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { Subscription } from 'rxjs';

import {
  CourseService,
  Course,
  Module,
  Lesson
} from '../../../core/services/course';

import {
  LearningService,
  LessonProgress
} from '../../../core/services/learning';

import {
  QuizService,
  Quiz
} from '../../../core/services/quiz';

import {
  AIAssistantService
} from '../../../core/services/ai-assistant.service';

export interface AIChatMessage {
  sender: 'user' | 'assistant';
  text: string;
  timestamp: Date;
}

@Component({
  selector: 'app-lesson-detail',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './lesson-detail.html',
  styleUrl: './lesson-detail.scss'
})
export class LessonDetailComponent implements OnInit, OnDestroy {
  private readonly courseService = inject(CourseService);
  private readonly learningService = inject(LearningService);
  private readonly quizService = inject(QuizService);
  private readonly aiAssistantService = inject(AIAssistantService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  lesson: Lesson | null = null;
  progress: LessonProgress | null = null;

  course: Course | null = null;
  courseModules: Module[] = [];
  courseLessons: Lesson[] = [];
  allProgress: LessonProgress[] = [];
  courseQuiz: Quiz | null = null;
  hasPassedQuiz = false;

  previousLesson: Lesson | null = null;
  nextLesson: Lesson | null = null;
  sidebarOpen = false;

  loading = true;
  completing = false;
  errorMessage = '';
  successMessage = '';

  // AI Learning Assistant state
  aiMessages: AIChatMessage[] = [];
  aiQuestion = '';
  aiLoading = false;
  aiErrorMessage = '';

  private routeSub: Subscription | null = null;

  ngOnInit(): void {
    this.routeSub = this.route.paramMap.subscribe(params => {
      const lessonId = Number(params.get('lessonId'));
      if (!lessonId) {
        this.loading = false;
        this.errorMessage = 'Invalid lesson.';
        return;
      }
      this.loadLesson(lessonId);
    });
  }

  ngOnDestroy(): void {
    if (this.routeSub) {
      this.routeSub.unsubscribe();
    }
  }

  loadLesson(lessonId: number): void {
    this.loading = true;
    this.errorMessage = '';
    this.successMessage = '';

    this.courseService.getLesson(lessonId).subscribe({
      next: (lesson) => {
        this.lesson = lesson;
        this.loadProgress(lessonId);
        this.loadCourseCurriculum(lesson);
      },
      error: (error) => {
        console.error('Failed to load lesson:', error);
        this.loading = false;
        this.errorMessage = 'Unable to load the lesson. Please try again.';
      }
    });
  }

  loadProgress(lessonId: number): void {
    this.learningService.getProgress().subscribe({
      next: (progressRecords) => {
        this.allProgress = progressRecords;
        this.progress =
          progressRecords.find((item) => item.lesson === lessonId) ?? null;
        this.loading = false;
      },
      error: (error) => {
        console.error('Failed to load lesson progress:', error);
        this.loading = false;
        this.errorMessage = 'Unable to load lesson progress.';
      }
    });
  }

  private loadCourseCurriculum(currentLesson: Lesson): void {
    this.courseService.getModule(currentLesson.module).subscribe({
      next: (module) => {
        const courseId = module.course;

        this.courseService.getCourse(courseId).subscribe({
          next: (c) => this.course = c,
          error: (err) => console.warn('Could not load course meta:', err)
        });

        this.courseService.getModules().subscribe({
          next: (allModules) => {
            this.courseModules = allModules
              .filter(m => m.course === courseId)
              .sort((a, b) => a.order - b.order);

            const moduleIds = this.courseModules.map(m => m.id);

            this.courseService.getLessons().subscribe({
              next: (allLessons) => {
                this.courseLessons = allLessons
                  .filter(l => moduleIds.includes(l.module))
                  .sort((a, b) => a.order - b.order);

                this.calculateAdjacentLessons(currentLesson);
              },
              error: (err) => console.warn('Could not load curriculum lessons:', err)
            });
          },
          error: (err) => console.warn('Could not load curriculum modules:', err)
        });

        this.quizService.getQuizzesByCourse(courseId).subscribe({
          next: (quizzes) => {
            this.courseQuiz = quizzes.find(q => q.is_published) ?? quizzes[0] ?? null;
            if (this.courseQuiz) {
              this.quizService.getAttempts().subscribe({
                next: (attempts) => {
                  this.hasPassedQuiz = attempts.some(
                    a => a.quiz === this.courseQuiz!.id && a.is_passed
                  );
                }
              });
            }
          },
          error: () => {}
        });
      },
      error: (err) => console.warn('Could not load module for curriculum:', err)
    });
  }

  private calculateAdjacentLessons(currentLesson: Lesson): void {
    if (!this.courseLessons || this.courseLessons.length === 0) return;

    const currentIndex = this.courseLessons.findIndex(l => l.id === currentLesson.id);
    if (currentIndex >= 0) {
      this.previousLesson = currentIndex > 0 ? this.courseLessons[currentIndex - 1] : null;
      this.nextLesson = currentIndex < this.courseLessons.length - 1 ? this.courseLessons[currentIndex + 1] : null;
    }
  }

  getLessonsForModule(moduleId: number): Lesson[] {
    return this.courseLessons
      .filter(l => l.module === moduleId)
      .sort((a, b) => a.order - b.order);
  }

  isLessonCompleted(lessonId: number): boolean {
    return this.allProgress.some(p => p.lesson === lessonId && p.is_completed);
  }

  get completedLessonsCount(): number {
    return this.courseLessons.filter(l => this.isLessonCompleted(l.id)).length;
  }

  get progressPercentage(): number {
    if (this.courseLessons.length === 0) return 0;
    return Math.round((this.completedLessonsCount / this.courseLessons.length) * 100);
  }

  get allLessonsCompleted(): boolean {
    return this.courseLessons.length > 0 && this.completedLessonsCount === this.courseLessons.length;
  }

  goToLesson(lessonId: number): void {
    this.sidebarOpen = false;
    this.router.navigate(['/learning/lesson', lessonId]);
  }

  goToPreviousLesson(): void {
    if (this.previousLesson) {
      this.goToLesson(this.previousLesson.id);
    }
  }

  goToNextLesson(): void {
    if (this.nextLesson) {
      this.goToLesson(this.nextLesson.id);
    }
  }

  goToQuiz(): void {
    if (this.courseQuiz) {
      this.router.navigate(['/quizzes', this.courseQuiz.id]);
    }
  }

  toggleSidebar(): void {
    this.sidebarOpen = !this.sidebarOpen;
  }

  markAsComplete(): void {
    if (!this.lesson || this.completing) {
      return;
    }

    this.completing = true;
    this.errorMessage = '';
    this.successMessage = '';

    if (this.progress) {
      this.learningService
        .updateProgress(this.progress.id, { is_completed: true })
        .subscribe({
          next: (progress) => {
            this.progress = progress;
            this.updateLocalProgress(progress);
            this.completing = false;
            this.successMessage = 'Lesson completed successfully.';
          },
          error: (error) => {
            console.error('Failed to update progress:', error);
            this.completing = false;
            if (error.status === 403) {
              this.errorMessage = 'You must be enrolled in this course before completing this lesson.';
            } else {
              this.errorMessage = 'Unable to mark the lesson as complete.';
            }
          }
        });
      return;
    }

    this.learningService
      .createProgress({ lesson: this.lesson.id, is_completed: true })
      .subscribe({
        next: (progress) => {
          this.progress = progress;
          this.updateLocalProgress(progress);
          this.completing = false;
          this.successMessage = 'Lesson completed successfully.';
        },
        error: (error) => {
          console.error('Failed to create progress:', error);
          this.completing = false;
          if (error.status === 403) {
            this.errorMessage = 'You must be enrolled in this course before completing this lesson.';
          } else if (error.status === 400) {
            this.errorMessage = 'Progress for this lesson already exists.';
          } else {
            this.errorMessage = 'Unable to mark the lesson as complete.';
          }
        }
      });
  }

  private updateLocalProgress(progress: LessonProgress): void {
    const idx = this.allProgress.findIndex(p => p.lesson === progress.lesson);
    if (idx >= 0) {
      this.allProgress[idx] = progress;
    } else {
      this.allProgress.push(progress);
    }
  }

  askAI(promptText?: string): void {
    const question = (promptText || this.aiQuestion).trim();
    if (!question || !this.lesson || this.aiLoading) {
      return;
    }

    this.aiErrorMessage = '';
    this.aiLoading = true;
    this.aiQuestion = '';

    this.aiMessages.push({
      sender: 'user',
      text: question,
      timestamp: new Date()
    });

    this.aiAssistantService
      .askQuestion(this.lesson.id, question)
      .subscribe({
        next: (response) => {
          this.aiMessages.push({
            sender: 'assistant',
            text: response.answer,
            timestamp: new Date()
          });
          this.aiLoading = false;
        },
        error: (error) => {
          console.error('Failed to get AI assistant response:', error);
          this.aiLoading = false;

          if (error.error && error.error.error) {
            this.aiErrorMessage = typeof error.error.error === 'string'
              ? error.error.error
              : (error.error.error.message || error.error.message || error.error.detail || 'Failed to get response.');
          } else if (error.status === 429) {
            this.aiErrorMessage =
              error.error?.detail ||
              'You are asking questions too quickly. Please wait a moment before trying again.';
          } else if (error.status === 400) {
            if (error.error?.message) {
              this.aiErrorMessage = Array.isArray(error.error.message)
                ? error.error.message.join(' ')
                : error.error.message;
            } else {
              this.aiErrorMessage =
                'Invalid question submitted. Please check your message.';
            }
          } else if (error.status === 403) {
            this.aiErrorMessage =
              'You must be enrolled in this course to consult the AI assistant.';
          } else if (error.status === 503) {
            this.aiErrorMessage =
              'The AI assistant service is temporarily unconfigured or unavailable.';
          } else if (error.status === 504) {
            this.aiErrorMessage =
              'The AI assistant timed out. Please try again.';
          } else {
            this.aiErrorMessage =
              'Unable to connect to the AI assistant. Please try again.';
          }
        }
      });
  }

  useSuggestedPrompt(prompt: string): void {
    this.askAI(prompt);
  }

  goBack(): void {
    if (this.course) {
      this.router.navigate(['/courses', this.course.id]);
    } else if (this.lesson) {
      this.courseService.getModule(this.lesson.module).subscribe({
        next: (module) => {
          this.router.navigate(['/courses', module.course]);
        },
        error: () => {
          this.router.navigate(['/courses']);
        }
      });
    } else {
      this.router.navigate(['/courses']);
    }
  }
}