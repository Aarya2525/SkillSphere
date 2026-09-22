import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';

import {
  CourseService,
  Lesson
} from '../../../core/services/course';

import {
  LearningService,
  LessonProgress
} from '../../../core/services/learning';

@Component({
  selector: 'app-lesson-detail',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './lesson-detail.html',
  styleUrl: './lesson-detail.scss'
})
export class LessonDetailComponent implements OnInit {

  private readonly courseService = inject(CourseService);
  private readonly learningService = inject(LearningService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  lesson: Lesson | null = null;
  progress: LessonProgress | null = null;

  loading = true;
  completing = false;
  errorMessage = '';
  successMessage = '';

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