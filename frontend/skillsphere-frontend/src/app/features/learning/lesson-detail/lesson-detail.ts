import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';

import {
  CourseService,
  Lesson
} from '../../../core/services/course';

import {
  LearningService,
  LessonProgress
} from '../../../core/services/learning';

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
export class LessonDetailComponent implements OnInit {

  private readonly courseService = inject(CourseService);
  private readonly learningService = inject(LearningService);
  private readonly aiAssistantService = inject(AIAssistantService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  lesson: Lesson | null = null;
  progress: LessonProgress | null = null;

  loading = true;
  completing = false;
  errorMessage = '';
  successMessage = '';

  // AI Learning Assistant state
  aiMessages: AIChatMessage[] = [];
  aiQuestion = '';
  aiLoading = false;
  aiErrorMessage = '';

  ngOnInit(): void {
    const lessonId = Number(
      this.route.snapshot.paramMap.get('lessonId')
    );

    if (!lessonId) {
      this.loading = false;
      this.errorMessage = 'Invalid lesson.';
      return;
    }

    this.loadLesson(lessonId);
  }

  loadLesson(lessonId: number): void {
    this.courseService.getLesson(lessonId).subscribe({
      next: (lesson) => {
        this.lesson = lesson;

        this.loadProgress(lessonId);
      },

      error: (error) => {
        console.error('Failed to load lesson:', error);

        this.loading = false;
        this.errorMessage =
          'Unable to load the lesson. Please try again.';
      }
    });
  }

  loadProgress(lessonId: number): void {
    this.learningService.getProgress().subscribe({
      next: (progressRecords) => {

        this.progress =
          progressRecords.find(
            (item) => item.lesson === lessonId
          ) ?? null;

        this.loading = false;
      },

      error: (error) => {
        console.error(
          'Failed to load lesson progress:',
          error
        );

        this.loading = false;
        this.errorMessage =
          'Unable to load lesson progress.';
      }
    });
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
        .updateProgress(
          this.progress.id,
          {
            is_completed: true
          }
        )
        .subscribe({

          next: (progress) => {
            this.progress = progress;
            this.completing = false;

            this.successMessage =
              'Lesson completed successfully.';
          },

          error: (error) => {
            console.error(
              'Failed to update progress:',
              error
            );

            this.completing = false;

            if (error.status === 403) {
              this.errorMessage =
                'You must be enrolled in this course before completing this lesson.';
            } else {
              this.errorMessage =
                'Unable to mark the lesson as complete.';
            }
          }

        });

      return;
    }

    this.learningService
      .createProgress({
        lesson: this.lesson.id,
        is_completed: true
      })
      .subscribe({

        next: (progress) => {
          this.progress = progress;
          this.completing = false;

          this.successMessage =
            'Lesson completed successfully.';
        },

        error: (error) => {
          console.error(
            'Failed to create progress:',
            error
          );

          this.completing = false;

          if (error.status === 403) {
            this.errorMessage =
              'You must be enrolled in this course before completing this lesson.';
          } else if (error.status === 400) {
            this.errorMessage =
              'Progress for this lesson already exists.';
          } else {
            this.errorMessage =
              'Unable to mark the lesson as complete.';
          }
        }

      });
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
          console.error(
            'Failed to get AI assistant response:',
            error
          );

          this.aiLoading = false;

          if (error.error && error.error.error) {
            this.aiErrorMessage = error.error.error;
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
    if (this.lesson) {
      this.courseService
        .getModule(this.lesson.module)
        .subscribe({
          next: (module) => {
            this.router.navigate([
              '/courses',
              module.course
            ]);
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