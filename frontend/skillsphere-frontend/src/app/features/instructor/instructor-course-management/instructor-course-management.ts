import {
  Component,
  OnInit,
  inject
} from '@angular/core';

import { CommonModule } from '@angular/common';

import {
  FormsModule
} from '@angular/forms';

import {
  Router,
  ActivatedRoute
} from '@angular/router';

import {
  CourseService,
  Course,
  Module,
  Lesson
} from '../../../core/services/course';

import {
  QuizService,
  Quiz,
  QuizQuestion,
  QuizOption
} from '../../../core/services/quiz';

@Component({
  selector: 'app-instructor-course-management',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule
  ],
  templateUrl: './instructor-course-management.html',
  styleUrl: './instructor-course-management.scss'
})
export class InstructorCourseManagementComponent
  implements OnInit {

  private readonly courseService =
    inject(CourseService);

  private readonly quizService =
    inject(QuizService);

  private readonly router =
    inject(Router);

  private readonly route =
    inject(ActivatedRoute);

  // --------------------------------------------------
  // COURSE
  // --------------------------------------------------

  title = '';

  description = '';

  courseId: number | null = null;

  course: Course | null = null;

  // --------------------------------------------------
  // COURSE CONTENT
  // --------------------------------------------------

  modules: Module[] = [];

  lessons: Lesson[] = [];

  // --------------------------------------------------
  // MODULE FORM
  // --------------------------------------------------

  moduleTitle = '';

  editingModuleId: number | null = null;

  showModuleForm = false;

  // --------------------------------------------------
  // LESSON FORM
  // --------------------------------------------------

  lessonTitle = '';

  lessonContent = '';

  selectedModuleId: number | null = null;

  editingLessonId: number | null = null;

  showLessonForm = false;

  // --------------------------------------------------
  // UI STATE
  // --------------------------------------------------

  loading = false;

  contentLoading = false;

  savingModule = false;

  savingLesson = false;

  deletingModuleId: number | null = null;

  deletingLessonId: number | null = null;

  publishing = false;

  errorMessage = '';

  contentErrorMessage = '';

  successMessage = '';

  // --------------------------------------------------
  // QUIZ / ASSESSMENT STATE
  // --------------------------------------------------

  courseQuiz: Quiz | null = null;
  quizLoading = false;
  quizErrorMessage = '';
  quizSuccessMessage = '';

  showQuizForm = false;
  quizTitle = '';
  quizDescription = '';
  quizPassingScore = 70;
  savingQuiz = false;
  deletingQuiz = false;

  showQuestionForm = false;
  editingQuestionId: number | null = null;
  questionText = '';
  questionOrder = 1;
  savingQuestion = false;
  deletingQuestionId: number | null = null;

  showOptionFormForQuestionId: number | null = null;
  editingOptionId: number | null = null;
  optionText = '';
  optionIsCorrect = false;
  savingOption = false;
  deletingOptionId: number | null = null;

  publishingQuiz = false;
  quizValidationErrors: string[] = [];

  // --------------------------------------------------
  // INIT
  // --------------------------------------------------

  ngOnInit(): void {

    const id =
      this.route.snapshot.paramMap.get('id');

    /*
     * /instructor/courses/create
     */
    if (!id) {
      this.courseId = null;
      return;
    }

    const parsedId = Number(id);

    if (Number.isNaN(parsedId)) {

      this.errorMessage =
        'Invalid course ID.';

      return;
    }

    this.courseId = parsedId;

    this.loadCourse(parsedId);

    this.loadCourseContent(parsedId);

    this.loadCourseQuiz(parsedId);
  }

  // --------------------------------------------------
  // GETTERS
  // --------------------------------------------------

  get isManageMode(): boolean {
    return this.courseId !== null;
  }

  get sortedModules(): Module[] {

    return [...this.modules].sort(
      (a, b) =>
        a.order - b.order
    );
  }

  getLessonsForModule(
    moduleId: number
  ): Lesson[] {

    return this.lessons
      .filter(
        lesson =>
          lesson.module === moduleId
      )
      .sort(
        (a, b) =>
          a.order - b.order
      );
  }

  // --------------------------------------------------
  // COURSE
  // --------------------------------------------------

  loadCourse(id: number): void {

    this.loading = true;

    this.errorMessage = '';

    this.courseService
      .getCourse(id)
      .subscribe({

        next: (course: Course) => {

          this.course = course;

          this.title =
            course.title;

          this.description =
            course.description;

          this.loading = false;
        },

        error: (error) => {

          console.error(
            'Failed to load course:',
            error
          );

          this.loading = false;

          if (error.status === 401) {

            this.errorMessage =
              'Your session has expired. Please log in again.';

          } else if (error.status === 403) {

            this.errorMessage =
              'You do not have permission to manage this course.';

          } else if (error.status === 404) {

            this.errorMessage =
              'Course not found or you do not have access to it.';

          } else {

            this.errorMessage =
              'Unable to load the course. Please try again.';
          }
        }
      });
  }

  onSubmit(): void {

    this.errorMessage = '';

    this.successMessage = '';

    const trimmedTitle =
      this.title.trim();

    const trimmedDescription =
      this.description.trim();

    if (!trimmedTitle) {

      this.errorMessage =
        'Course title is required.';

      return;
    }

    if (!trimmedDescription) {

      this.errorMessage =
        'Course description is required.';

      return;
    }

    this.loading = true;

    const courseData = {
      title: trimmedTitle,
      description: trimmedDescription
    };

    if (this.courseId !== null) {

      this.updateCourse(
        this.courseId,
        courseData
      );

      return;
    }

    this.createCourse(courseData);
  }

  private createCourse(
    courseData: {
      title: string;
      description: string;
    }
  ): void {

    this.courseService
      .createCourse(courseData)
      .subscribe({

        next: (course: Course) => {

          this.loading = false;

          this.course = course;

          this.courseId =
            course.id;

          this.title =
            course.title;

          this.description =
            course.description;

          this.successMessage =
            'Course created successfully.';

          this.router.navigate([
            '/instructor/courses',
            course.id
          ]);
        },

        error: (error) => {

          console.error(
            'Failed to create course:',
            error
          );

          this.loading = false;

          if (error.status === 401) {

            this.errorMessage =
              'Your session has expired. Please log in again.';

          } else if (error.status === 403) {

            this.errorMessage =
              'You do not have permission to create courses.';

          } else if (error.status === 400) {

            this.errorMessage =
              'Please check the course information and try again.';

          } else {

            this.errorMessage =
              'Unable to create the course. Please try again.';
          }
        }
      });
  }

  private updateCourse(
    id: number,
    courseData: {
      title: string;
      description: string;
    }
  ): void {

    this.courseService
      .updateCourse(
        id,
        courseData
      )
      .subscribe({

        next: (course: Course) => {

          this.loading = false;

          this.course = course;

          this.title =
            course.title;

          this.description =
            course.description;

          this.successMessage =
            'Course updated successfully.';
        },

        error: (error) => {

          console.error(
            'Failed to update course:',
            error
          );

          this.loading = false;

          if (error.status === 401) {

            this.errorMessage =
              'Your session has expired. Please log in again.';

          } else if (error.status === 403) {

            this.errorMessage =
              'You do not have permission to update this course.';

          } else if (error.status === 404) {

            this.errorMessage =
              'Course not found or you do not have access to it.';

          } else {

            this.errorMessage =
              'Unable to update the course. Please try again.';
          }
        }
      });
  }

  // --------------------------------------------------
  // LOAD MODULES + LESSONS
  // --------------------------------------------------

  loadCourseContent(
    courseId: number
  ): void {

    this.contentLoading = true;

    this.contentErrorMessage = '';

    this.courseService
      .getModules()
      .subscribe({

        next: (modules: Module[]) => {

          this.modules =
            modules
              .filter(
                module =>
                  module.course === courseId
              )
              .sort(
                (a, b) =>
                  a.order - b.order
              );

          this.loadLessons();
        },

        error: (error) => {

          console.error(
            'Failed to load modules:',
            error
          );

          this.contentLoading = false;

          this.contentErrorMessage =
            this.getContentErrorMessage(
              error,
              'Unable to load course modules.'
            );
        }
      });
  }

  private loadLessons(): void {

    this.courseService
      .getLessons()
      .subscribe({

        next: (lessons: Lesson[]) => {

          this.lessons =
            lessons;

          this.contentLoading = false;
        },

        error: (error) => {

          console.error(
            'Failed to load lessons:',
            error
          );

          this.contentLoading = false;

          this.contentErrorMessage =
            this.getContentErrorMessage(
              error,
              'Unable to load course lessons.'
            );
        }
      });
  }

  // --------------------------------------------------
  // MODULE FORM
  // --------------------------------------------------

  openCreateModule(): void {

    this.editingModuleId = null;

    this.moduleTitle = '';

    this.showModuleForm = true;

    this.errorMessage = '';

    this.contentErrorMessage = '';

    this.successMessage = '';
  }

  openEditModule(
    module: Module
  ): void {

    this.editingModuleId =
      module.id;

    this.moduleTitle =
      module.title;

    this.showModuleForm = true;

    this.errorMessage = '';

    this.contentErrorMessage = '';

    this.successMessage = '';
  }

  cancelModuleForm(): void {

    this.showModuleForm = false;

    this.editingModuleId = null;

    this.moduleTitle = '';
  }

  saveModule(): void {

    if (this.savingModule) {
      return;
    }

    if (this.courseId === null) {

      this.errorMessage =
        'Course must be created before adding modules.';

      return;
    }

    const trimmedTitle =
      this.moduleTitle.trim();

    if (!trimmedTitle) {

      this.errorMessage =
        'Module title is required.';

      return;
    }

    this.savingModule = true;

    this.errorMessage = '';

    this.contentErrorMessage = '';

    this.successMessage = '';

    if (this.editingModuleId !== null) {

      this.courseService
        .updateModule(
          this.editingModuleId,
          {
            title: trimmedTitle
          }
        )
        .subscribe({

          next: (updatedModule) => {

            this.modules =
              this.modules.map(
                module =>
                  module.id === updatedModule.id
                    ? updatedModule
                    : module
              );

            this.savingModule = false;

            this.showModuleForm = false;

            this.editingModuleId = null;

            this.moduleTitle = '';

            this.successMessage =
              'Module updated successfully.';
          },

          error: (error) => {

            console.error(
              'Failed to update module:',
              error
            );

            this.savingModule = false;

            this.handleContentError(
              error,
              'Unable to update the module.'
            );
          }
        });

      return;
    }

    const nextOrder =
      this.modules.length > 0
        ? Math.max(
            ...this.modules.map(
              module => module.order
            )
          ) + 1
        : 1;

    this.courseService
      .createModule({
        course: this.courseId,
        title: trimmedTitle,
        order: nextOrder
      })
      .subscribe({

        next: (module) => {

          this.modules = [
            ...this.modules,
            module
          ].sort(
            (a, b) =>
              a.order - b.order
          );

          this.savingModule = false;

          this.showModuleForm = false;

          this.moduleTitle = '';

          this.successMessage =
            'Module created successfully.';
        },

        error: (error) => {

          console.error(
            'Failed to create module:',
            error
          );

          this.savingModule = false;

          this.handleContentError(
            error,
            'Unable to create the module.'
          );
        }
      });
  }

  deleteModule(
    module: Module
  ): void {

    if (
      this.deletingModuleId !== null
    ) {
      return;
    }

    const confirmed =
      window.confirm(
        `Delete "${module.title}"? This may also remove its lessons.`
      );

    if (!confirmed) {
      return;
    }

    this.deletingModuleId =
      module.id;

    this.errorMessage = '';

    this.contentErrorMessage = '';

    this.successMessage = '';

    this.courseService
      .deleteModule(module.id)
      .subscribe({

        next: () => {

          this.modules =
            this.modules.filter(
              item =>
                item.id !== module.id
            );

          this.lessons =
            this.lessons.filter(
              lesson =>
                lesson.module !== module.id
            );

          this.deletingModuleId =
            null;

          this.successMessage =
            'Module deleted successfully.';
        },

        error: (error) => {

          console.error(
            'Failed to delete module:',
            error
          );

          this.deletingModuleId =
            null;

          this.handleContentError(
            error,
            'Unable to delete the module.'
          );
        }
      });
  }

  // --------------------------------------------------
  // LESSON FORM
  // --------------------------------------------------

  openCreateLesson(
    moduleId: number
  ): void {

    this.editingLessonId = null;

    this.selectedModuleId =
      moduleId;

    this.lessonTitle = '';

    this.lessonContent = '';

    this.showLessonForm = true;

    this.errorMessage = '';

    this.contentErrorMessage = '';

    this.successMessage = '';
  }

  openEditLesson(
    lesson: Lesson
  ): void {

    this.editingLessonId =
      lesson.id;

    this.selectedModuleId =
      lesson.module;

    this.lessonTitle =
      lesson.title;

    this.lessonContent =
      lesson.content;

    this.showLessonForm = true;

    this.errorMessage = '';

    this.contentErrorMessage = '';

    this.successMessage = '';
  }

  cancelLessonForm(): void {

    this.showLessonForm = false;

    this.editingLessonId = null;

    this.selectedModuleId = null;

    this.lessonTitle = '';

    this.lessonContent = '';
  }

  saveLesson(): void {

    if (this.savingLesson) {
      return;
    }

    if (
      this.selectedModuleId === null
    ) {

      this.errorMessage =
        'Please select a module for this lesson.';

      return;
    }

    const trimmedTitle =
      this.lessonTitle.trim();

    const trimmedContent =
      this.lessonContent.trim();

    if (!trimmedTitle) {

      this.errorMessage =
        'Lesson title is required.';

      return;
    }

    if (!trimmedContent) {

      this.errorMessage =
        'Lesson content is required.';

      return;
    }

    this.savingLesson = true;

    this.errorMessage = '';

    this.contentErrorMessage = '';

    this.successMessage = '';

    if (this.editingLessonId !== null) {

      this.courseService
        .updateLesson(
          this.editingLessonId,
          {
            module:
              this.selectedModuleId,
            title:
              trimmedTitle,
            content:
              trimmedContent
          }
        )
        .subscribe({

          next: (updatedLesson) => {

            this.lessons =
              this.lessons.map(
                lesson =>
                  lesson.id === updatedLesson.id
                    ? updatedLesson
                    : lesson
              );

            this.savingLesson = false;

            this.showLessonForm = false;

            this.editingLessonId = null;

            this.selectedModuleId = null;

            this.lessonTitle = '';

            this.lessonContent = '';

            this.successMessage =
              'Lesson updated successfully.';
          },

          error: (error) => {

            console.error(
              'Failed to update lesson:',
              error
            );

            this.savingLesson = false;

            this.handleContentError(
              error,
              'Unable to update the lesson.'
            );
          }
        });

      return;
    }

    const moduleLessons =
      this.getLessonsForModule(
        this.selectedModuleId
      );

    const nextOrder =
      moduleLessons.length > 0
        ? Math.max(
            ...moduleLessons.map(
              lesson => lesson.order
            )
          ) + 1
        : 1;

    this.courseService
      .createLesson({
        module:
          this.selectedModuleId,
        title:
          trimmedTitle,
        content:
          trimmedContent,
        order:
          nextOrder
      })
      .subscribe({

        next: (lesson) => {

          this.lessons = [
            ...this.lessons,
            lesson
          ];

          this.savingLesson = false;

          this.showLessonForm = false;

          this.selectedModuleId = null;

          this.lessonTitle = '';

          this.lessonContent = '';

          this.successMessage =
            'Lesson created successfully.';
        },

        error: (error) => {

          console.error(
            'Failed to create lesson:',
            error
          );

          this.savingLesson = false;

          this.handleContentError(
            error,
            'Unable to create the lesson.'
          );
        }
      });
  }

  deleteLesson(
    lesson: Lesson
  ): void {

    if (
      this.deletingLessonId !== null
    ) {
      return;
    }

    const confirmed =
      window.confirm(
        `Delete "${lesson.title}"?`
      );

    if (!confirmed) {
      return;
    }

    this.deletingLessonId =
      lesson.id;

    this.errorMessage = '';

    this.contentErrorMessage = '';

    this.successMessage = '';

    this.courseService
      .deleteLesson(lesson.id)
      .subscribe({

        next: () => {

          this.lessons =
            this.lessons.filter(
              item =>
                item.id !== lesson.id
            );

          this.deletingLessonId =
            null;

          this.successMessage =
            'Lesson deleted successfully.';
        },

        error: (error) => {

          console.error(
            'Failed to delete lesson:',
            error
          );

          this.deletingLessonId =
            null;

          this.handleContentError(
            error,
            'Unable to delete the lesson.'
          );
        }
      });
  }

  // --------------------------------------------------
  // PUBLISHING
  // --------------------------------------------------

  togglePublish(): void {

    if (
      this.courseId === null ||
      !this.course ||
      this.publishing
    ) {
      return;
    }

    this.publishing = true;

    this.errorMessage = '';

    this.successMessage = '';

    const newStatus =
      !this.course.is_published;

    this.courseService
      .updateCourse(
        this.courseId,
        {}
      )
      .subscribe({

        next: () => {

          this.publishing = false;

          this.successMessage =
            newStatus
              ? 'Publish action is ready for backend integration.'
              : 'Unpublish action is ready for backend integration.';
        },

        error: (error) => {

          console.error(
            'Failed to update publish status:',
            error
          );

          this.publishing = false;

          this.handleContentError(
            error,
            'Unable to update the course status.'
          );
        }
      });
  }

  // --------------------------------------------------
  // ERROR HANDLING
  // --------------------------------------------------

  private getContentErrorMessage(
    error: any,
    fallbackMessage: string
  ): string {

    if (error?.status === 401) {

      return 'Your session has expired. Please log in again.';

    }

    if (error?.status === 403) {

      return 'You do not have permission to view this course content.';

    }

    if (error?.status === 404) {

      return 'Course content was not found.';

    }

    if (error?.status === 400) {

      return 'The course content request was invalid.';
    }

    return fallbackMessage;
  }

  private handleContentError(
    error: any,
    fallbackMessage: string
  ): void {

    if (error?.status === 401) {

      this.errorMessage =
        'Your session has expired. Please log in again.';

    } else if (error?.status === 403) {

      this.errorMessage =
        'You do not have permission to modify this content.';

    } else if (error?.status === 404) {

      this.errorMessage =
        'The requested course content was not found.';

    } else if (error?.status === 400) {

      this.errorMessage =
        'Please check the information and try again.';

    } else {

      this.errorMessage =
        fallbackMessage;
    }
  }

  // --------------------------------------------------
  // QUIZ / ASSESSMENT METHODS
  // --------------------------------------------------

  loadCourseQuiz(courseId: number): void {
    this.quizLoading = true;
    this.quizErrorMessage = '';
    this.quizValidationErrors = [];

    this.quizService.getQuizzesByCourse(courseId).subscribe({
      next: (quizzes) => {
        if (quizzes.length > 0) {
          this.quizService.getQuizDetail(quizzes[0].id).subscribe({
            next: (fullQuiz) => {
              this.courseQuiz = fullQuiz;
              this.quizTitle = fullQuiz.title;
              this.quizDescription = fullQuiz.description;
              this.quizPassingScore = fullQuiz.passing_score;
              this.quizLoading = false;
            },
            error: (err) => {
              console.error('Failed to load quiz details:', err);
              this.courseQuiz = quizzes[0];
              this.quizTitle = quizzes[0].title;
              this.quizDescription = quizzes[0].description;
              this.quizPassingScore = quizzes[0].passing_score;
              this.quizLoading = false;
            }
          });
        } else {
          this.courseQuiz = null;
          this.quizLoading = false;
        }
      },
      error: (error) => {
        console.error('Failed to load course quiz:', error);
        this.quizLoading = false;
        this.quizErrorMessage = 'Unable to load course assessment.';
      }
    });
  }

  openCreateQuiz(): void {
    this.quizTitle = this.course ? `${this.course.title} Assessment` : 'Course Quiz';
    this.quizDescription = 'Test your knowledge on course concepts.';
    this.quizPassingScore = 70;
    this.showQuizForm = true;
    this.quizErrorMessage = '';
    this.quizSuccessMessage = '';
    this.quizValidationErrors = [];
  }

  openEditQuiz(): void {
    if (!this.courseQuiz) return;
    this.quizTitle = this.courseQuiz.title;
    this.quizDescription = this.courseQuiz.description;
    this.quizPassingScore = this.courseQuiz.passing_score;
    this.showQuizForm = true;
    this.quizErrorMessage = '';
    this.quizSuccessMessage = '';
    this.quizValidationErrors = [];
  }

  cancelQuizForm(): void {
    this.showQuizForm = false;
  }

  saveQuiz(): void {
    if (!this.courseId) return;
    const title = this.quizTitle.trim();
    if (!title) {
      this.quizErrorMessage = 'Quiz title is required.';
      return;
    }
    const score = Number(this.quizPassingScore);
    if (isNaN(score) || score < 1 || score > 100) {
      this.quizErrorMessage = 'Passing score must be between 1 and 100.';
      return;
    }

    this.savingQuiz = true;
    this.quizErrorMessage = '';
    this.quizSuccessMessage = '';

    if (this.courseQuiz) {
      this.quizService.updateQuiz(this.courseQuiz.id, {
        title,
        description: this.quizDescription.trim(),
        passing_score: score
      }).subscribe({
        next: (updated) => {
          this.savingQuiz = false;
          this.showQuizForm = false;
          this.courseQuiz = { ...this.courseQuiz!, ...updated, questions: this.courseQuiz!.questions };
          this.quizSuccessMessage = 'Quiz details updated successfully.';
        },
        error: (err) => {
          console.error('Failed to update quiz:', err);
          this.savingQuiz = false;
          this.quizErrorMessage = 'Unable to update quiz details.';
        }
      });
    } else {
      this.quizService.createQuiz({
        course: this.courseId,
        title,
        description: this.quizDescription.trim(),
        passing_score: score,
        is_published: false
      }).subscribe({
        next: (created) => {
          this.savingQuiz = false;
          this.showQuizForm = false;
          this.courseQuiz = { ...created, questions: [] };
          this.quizSuccessMessage = 'Quiz created! Now add questions and options.';
        },
        error: (err) => {
          console.error('Failed to create quiz:', err);
          this.savingQuiz = false;
          this.quizErrorMessage = 'Unable to create quiz.';
        }
      });
    }
  }

  deleteQuiz(): void {
    if (!this.courseQuiz) return;
    if (!confirm('Are you sure you want to delete this quiz?')) return;

    this.deletingQuiz = true;
    this.quizService.deleteQuiz(this.courseQuiz.id).subscribe({
      next: () => {
        this.deletingQuiz = false;
        this.courseQuiz = null;
        this.quizSuccessMessage = 'Quiz deleted successfully.';
      },
      error: (err) => {
        console.error('Failed to delete quiz:', err);
        this.deletingQuiz = false;
        this.quizErrorMessage = 'Unable to delete quiz.';
      }
    });
  }

  openAddQuestion(): void {
    this.editingQuestionId = null;
    this.questionText = '';
    this.questionOrder = (this.courseQuiz?.questions?.length || 0) + 1;
    this.showQuestionForm = true;
    this.quizErrorMessage = '';
  }

  openEditQuestion(q: QuizQuestion): void {
    this.editingQuestionId = q.id;
    this.questionText = q.text;
    this.questionOrder = q.order;
    this.showQuestionForm = true;
    this.quizErrorMessage = '';
  }

  cancelQuestionForm(): void {
    this.showQuestionForm = false;
    this.editingQuestionId = null;
  }

  saveQuestion(): void {
    if (!this.courseQuiz) return;
    const text = this.questionText.trim();
    if (!text) {
      this.quizErrorMessage = 'Question text cannot be empty.';
      return;
    }

    this.savingQuestion = true;
    this.quizErrorMessage = '';

    if (this.editingQuestionId) {
      this.quizService.updateQuestion(this.editingQuestionId, {
        text,
        order: this.questionOrder
      }).subscribe({
        next: (updated) => {
          this.savingQuestion = false;
          this.showQuestionForm = false;
          if (this.courseQuiz?.questions) {
            this.courseQuiz.questions = this.courseQuiz.questions.map(q =>
              q.id === updated.id ? { ...q, text: updated.text, order: updated.order } : q
            ).sort((a, b) => a.order - b.order);
          }
          this.quizSuccessMessage = 'Question updated successfully.';
        },
        error: (err) => {
          console.error('Failed to update question:', err);
          this.savingQuestion = false;
          this.quizErrorMessage = 'Unable to update question.';
        }
      });
    } else {
      this.quizService.createQuestion({
        quiz: this.courseQuiz.id,
        text,
        order: this.questionOrder
      }).subscribe({
        next: (created) => {
          this.savingQuestion = false;
          this.showQuestionForm = false;
          if (this.courseQuiz) {
            const questions = this.courseQuiz.questions || [];
            this.courseQuiz.questions = [...questions, { ...created, options: [] }].sort((a, b) => a.order - b.order);
          }
          this.quizSuccessMessage = 'Question added! Now add options.';
        },
        error: (err) => {
          console.error('Failed to create question:', err);
          this.savingQuestion = false;
          this.quizErrorMessage = 'Unable to add question.';
        }
      });
    }
  }

  deleteQuestion(questionId: number): void {
    if (!confirm('Are you sure you want to delete this question?')) return;
    this.deletingQuestionId = questionId;

    this.quizService.deleteQuestion(questionId).subscribe({
      next: () => {
        this.deletingQuestionId = null;
        if (this.courseQuiz?.questions) {
          this.courseQuiz.questions = this.courseQuiz.questions.filter(q => q.id !== questionId);
        }
        this.quizSuccessMessage = 'Question deleted.';
      },
      error: (err) => {
        console.error('Failed to delete question:', err);
        this.deletingQuestionId = null;
        this.quizErrorMessage = 'Unable to delete question.';
      }
    });
  }

  openAddOption(questionId: number): void {
    this.showOptionFormForQuestionId = questionId;
    this.editingOptionId = null;
    this.optionText = '';
    const q = this.courseQuiz?.questions?.find(item => item.id === questionId);
    const hasCorrect = q?.options?.some(o => o.is_correct);
    this.optionIsCorrect = !hasCorrect;
    this.quizErrorMessage = '';
  }

  openEditOption(opt: QuizOption, questionId: number): void {
    this.showOptionFormForQuestionId = questionId;
    this.editingOptionId = opt.id;
    this.optionText = opt.text;
    this.optionIsCorrect = opt.is_correct;
    this.quizErrorMessage = '';
  }

  cancelOptionForm(): void {
    this.showOptionFormForQuestionId = null;
    this.editingOptionId = null;
  }

  saveOption(questionId: number): void {
    const text = this.optionText.trim();
    if (!text) {
      this.quizErrorMessage = 'Option text cannot be empty.';
      return;
    }

    this.savingOption = true;
    this.quizErrorMessage = '';

    if (this.editingOptionId) {
      this.quizService.updateOption(this.editingOptionId, {
        text,
        is_correct: this.optionIsCorrect
      }).subscribe({
        next: () => {
          this.savingOption = false;
          this.showOptionFormForQuestionId = null;
          this.reloadQuiz();
          this.quizSuccessMessage = 'Option updated.';
        },
        error: (err) => {
          console.error('Failed to update option:', err);
          this.savingOption = false;
          this.quizErrorMessage = 'Unable to update option.';
        }
      });
    } else {
      this.quizService.createOption({
        question: questionId,
        text,
        is_correct: this.optionIsCorrect
      }).subscribe({
        next: () => {
          this.savingOption = false;
          this.showOptionFormForQuestionId = null;
          this.reloadQuiz();
          this.quizSuccessMessage = 'Option added.';
        },
        error: (err) => {
          console.error('Failed to create option:', err);
          this.savingOption = false;
          this.quizErrorMessage = 'Unable to add option.';
        }
      });
    }
  }

  setCorrectOption(q: QuizQuestion, optId: number): void {
    this.quizService.updateOption(optId, { is_correct: true }).subscribe({
      next: () => {
        const otherOptions = q.options.filter(o => o.id !== optId && o.is_correct);
        if (otherOptions.length === 0) {
          this.reloadQuiz();
          return;
        }
        let completed = 0;
        otherOptions.forEach(o => {
          this.quizService.updateOption(o.id, { is_correct: false }).subscribe({
            next: () => {
              completed++;
              if (completed === otherOptions.length) {
                this.reloadQuiz();
              }
            }
          });
        });
      },
      error: (err) => {
        console.error('Failed to set correct option:', err);
        this.quizErrorMessage = 'Unable to set correct option.';
      }
    });
  }

  deleteOption(optionId: number): void {
    if (!confirm('Are you sure you want to delete this option?')) return;
    this.deletingOptionId = optionId;

    this.quizService.deleteOption(optionId).subscribe({
      next: () => {
        this.deletingOptionId = null;
        this.reloadQuiz();
        this.quizSuccessMessage = 'Option deleted.';
      },
      error: (err) => {
        console.error('Failed to delete option:', err);
        this.deletingOptionId = null;
        this.quizErrorMessage = 'Unable to delete option.';
      }
    });
  }

  private reloadQuiz(): void {
    if (!this.courseQuiz) return;
    this.quizService.getQuizDetail(this.courseQuiz.id).subscribe({
      next: (fullQuiz) => {
        this.courseQuiz = fullQuiz;
      }
    });
  }

  validateQuiz(): string[] {
    const errors: string[] = [];
    if (!this.courseQuiz) {
      errors.push('No quiz created yet.');
      return errors;
    }

    const questions = this.courseQuiz.questions || [];
    if (questions.length === 0) {
      errors.push('Quiz must contain at least one question.');
      return errors;
    }

    questions.forEach((q, idx) => {
      const qNum = idx + 1;
      const options = q.options || [];
      if (options.length < 2) {
        errors.push(`Question ${qNum} ("${q.text.slice(0, 30)}...") must have at least 2 options.`);
      }
      const correctCount = options.filter(o => o.is_correct).length;
      if (correctCount === 0) {
        errors.push(`Question ${qNum} does not have any correct answer selected.`);
      } else if (correctCount > 1) {
        errors.push(`Question ${qNum} has multiple correct answers selected (${correctCount}). Exactly one is required.`);
      }
    });

    return errors;
  }

  toggleQuizPublish(): void {
    if (!this.courseQuiz) return;

    this.quizValidationErrors = [];
    this.quizErrorMessage = '';
    this.quizSuccessMessage = '';

    if (!this.courseQuiz.is_published) {
      const errors = this.validateQuiz();
      if (errors.length > 0) {
        this.quizValidationErrors = errors;
        this.quizErrorMessage = 'Cannot publish quiz: please resolve the validation issues below.';
        return;
      }
    }

    this.publishingQuiz = true;
    const nextState = !this.courseQuiz.is_published;

    this.quizService.updateQuiz(this.courseQuiz.id, {
      is_published: nextState
    }).subscribe({
      next: (updated) => {
        this.publishingQuiz = false;
        if (this.courseQuiz) {
          this.courseQuiz.is_published = updated.is_published;
        }
        this.quizSuccessMessage = nextState
          ? 'Quiz published successfully! Students can now take this assessment.'
          : 'Quiz unpublished (switched to draft).';
      },
      error: (err) => {
        console.error('Failed to toggle quiz publish:', err);
        this.publishingQuiz = false;
        if (err.error?.detail) {
          this.quizErrorMessage = err.error.detail;
        } else if (err.error?.non_field_errors) {
          this.quizErrorMessage = err.error.non_field_errors.join(' ');
        } else {
          this.quizErrorMessage = 'Unable to update quiz publication status.';
        }
      }
    });
  }

  // --------------------------------------------------
  // NAVIGATION
  // --------------------------------------------------

  cancel(): void {

    this.router.navigate([
      '/instructor/dashboard'
    ]);
  }
} 