"""
SkillSphere — Realistic LMS Demo Data Seeder Management Command
Creates comprehensive, production-grade demo data for SkillSphere LMS.
Safely idempotent: can be run repeatedly without duplicating records or corrupting existing data.
"""

from datetime import datetime, timedelta
import uuid

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from courses.models import Course, Module, Lesson
from enrollments.models import Enrollment
from learning.models import LessonProgress
from quizzes.models import Quiz, Question, Option, QuizAttempt, Answer
from certificates.models import Certificate
from reviews.models import Review
from notifications.models import Notification

User = get_user_model()


class Command(BaseCommand):
    help = "Seed SkillSphere with realistic, portfolio-grade demo data."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting SkillSphere demo data seeding..."))

        # Protected entity IDs (Must never be modified, deleted, or overwritten)
        PROTECTED_USER_IDS = [1, 2, 3, 4]
        PROTECTED_COURSE_IDS = [1, 2, 3]

        # ------------------------------------------------------------------
        # 1. NEW USERS (Instructors and Students)
        # ------------------------------------------------------------------
        self.stdout.write("Seeding users...")
        instructors_data = [
            {
                "username": "sarah_connor",
                "email": "sarah.connor@skillsphere.com",
                "first_name": "Sarah",
                "last_name": "Connor",
                "role": User.Role.INSTRUCTOR,
            },
            {
                "username": "marcus_vance",
                "email": "marcus.vance@skillsphere.com",
                "first_name": "Marcus",
                "last_name": "Vance",
                "role": User.Role.INSTRUCTOR,
            },
            {
                "username": "elena_rostova",
                "email": "elena.rostova@skillsphere.com",
                "first_name": "Elena",
                "last_name": "Rostova",
                "role": User.Role.INSTRUCTOR,
            },
        ]

        students_data = [
            {
                "username": "alex_rivera",
                "email": "alex.rivera@skillsphere.com",
                "first_name": "Alex",
                "last_name": "Rivera",
                "role": User.Role.STUDENT,
            },
            {
                "username": "david_kim",
                "email": "david.kim@skillsphere.com",
                "first_name": "David",
                "last_name": "Kim",
                "role": User.Role.STUDENT,
            },
            {
                "username": "maya_patel",
                "email": "maya.patel@skillsphere.com",
                "first_name": "Maya",
                "last_name": "Patel",
                "role": User.Role.STUDENT,
            },
            {
                "username": "jordan_lee",
                "email": "jordan.lee@skillsphere.com",
                "first_name": "Jordan",
                "last_name": "Lee",
                "role": User.Role.STUDENT,
            },
            {
                "username": "sofia_martinez",
                "email": "sofia.martinez@skillsphere.com",
                "first_name": "Sofia",
                "last_name": "Martinez",
                "role": User.Role.STUDENT,
            },
            {
                "username": "liam_chen",
                "email": "liam.chen@skillsphere.com",
                "first_name": "Liam",
                "last_name": "Chen",
                "role": User.Role.STUDENT,
            },
            {
                "username": "chloe_dupont",
                "email": "chloe.dupont@skillsphere.com",
                "first_name": "Chloe",
                "last_name": "Dupont",
                "role": User.Role.STUDENT,
            },
        ]

        users = {}
        # Fetch existing users
        for u in User.objects.all():
            users[u.username] = u

        # Seed new instructors
        for u_info in instructors_data:
            user, created = User.objects.get_or_create(
                username=u_info["username"],
                defaults={
                    "email": u_info["email"],
                    "first_name": u_info["first_name"],
                    "last_name": u_info["last_name"],
                    "role": u_info["role"],
                    "is_active": True,
                },
            )
            if created:
                user.set_password("TestPass123!")
                user.save()
            users[u_info["username"]] = user

        # Seed new students
        for u_info in students_data:
            user, created = User.objects.get_or_create(
                username=u_info["username"],
                defaults={
                    "email": u_info["email"],
                    "first_name": u_info["first_name"],
                    "last_name": u_info["last_name"],
                    "role": u_info["role"],
                    "is_active": True,
                },
            )
            if created:
                user.set_password("TestPass123!")
                user.save()
            users[u_info["username"]] = user

        # ------------------------------------------------------------------
        # 2. NEW COURSES & CURRICULUM
        # ------------------------------------------------------------------
        self.stdout.write("Seeding courses, modules, and lessons...")

        courses_manifest = [
            {
                "title": "Modern Angular & Enterprise Architecture",
                "instructor_username": "InstructorTest",
                "is_published": True,
                "description": (
                    "Master modern frontend engineering with Angular 19+: standalone components, "
                    "fine-grained reactivity with Signals, state management using NgRx, resilient HTTP interceptors, "
                    "and scalable micro-frontend architectures."
                ),
                "modules": [
                    {
                        "title": "Standalone Components & Modern Setup",
                        "lessons": [
                            ("Angular Evolution & Standalone Paradigm", "## Modern Angular Architecture\n\nAngular has evolved significantly with standalone components, replacing NgModule overhead with direct imports.\n\n### Key Concepts\n- Direct component dependency imports\n- Lighter application startup\n- Simplified dependency injection tree\n\n```typescript\n@Component({\n  selector: 'app-profile',\n  standalone: true,\n  imports: [CommonModule, RouterModule],\n  template: `<h1>User Profile</h1>`\n})\nexport class ProfileComponent {}\n```\n\n### Best Practices\n1. Prefer standalone components for all new feature development.\n2. Leverage barrel files carefully to prevent circular dependencies.\n3. Keep component boundaries strictly decoupled."),
                            ("Dependency Injection & Inject Function", "## Functional Dependency Injection\n\nThe `inject()` function enables functional DI across components, services, and routing guards.\n\n```typescript\nexport class CourseService {\n  private http = inject(HttpClient);\n  private auth = inject(AuthService);\n}\n```\n\n### Advantages\n- Cleaner constructor signatures\n- Ability to inject dependencies inside custom factory functions\n- Improved type inference in test environments."),
                            ("Control Flow Syntax & Performance", "## Built-in Control Flow\n\nAngular introduces native template control flow syntax (`@if`, `@for`, `@switch`), replacing legacy structural directives for optimal change detection.\n\n```html\n@if (isEnrolled) {\n  <button class=\"btn-primary\">Continue Learning</button>\n} @else {\n  <button class=\"btn-secondary\">Enroll Now</button>\n}\n```\n\n### Performance Gains\n- Faster compilation\n- Mandatory `@for (item of items; track item.id)` prevents unnecessary DOM re-renders\n- Better type-narrowing in templates."),
                            ("Component Inputs, Outputs & Model API", "## Signal Inputs & Outputs\n\nModern inputs use signal-based reactive primitives.\n\n```typescript\nexport class CourseCardComponent {\n  course = input.required<Course>();\n  enrolled = output<number>();\n}\n```\n\n### Benefits\n- Automatic read-only signal wrapping\n- Compile-time required input checks\n- Zero boilerplate event emitters."),
                            ("Content Projection & Template Outlets", "## Advanced Projection\n\nReusable card and dialog layouts leverage multi-slot content projection.\n\n```html\n<div class=\"card\">\n  <header><ng-content select=\"[header]\"></ng-content></header>\n  <main><ng-content></ng-content></main>\n</div>\n```\n\n### Summary\nMulti-slot projection maintains styling encapsulation while providing host components complete layout freedom."),
                        ],
                    },
                    {
                        "title": "Fine-Grained Reactivity with Signals",
                        "lessons": [
                            ("Signals Foundations: signal(), computed()", "## Signal Primitives\n\nSignals represent values that notify consumers whenever they mutate.\n\n```typescript\nconst count = signal(0);\nconst double = computed(() => count() * 2);\ncount.set(5);\nconsole.log(double()); // 10\n```\n\n### Rules of Signals\n- Never execute side-effects inside `computed`\n- Keep derivations pure and idempotent\n- Signals guarantee glitch-free reactive updates."),
                            ("Managing Side Effects with effect()", "## Side Effects in Angular\n\n`effect()` runs side-effects whenever its tracked dependencies change.\n\n```typescript\neffect(() => {\n  console.log(`Current filter state: ${this.activeFilter()}`);\n});\n```\n\n### Common Use Cases\n- Synchronizing with third-party charts\n- Logging and analytics dispatch\n- LocalStorage persistence."),
                            ("RxJS Interoperability: toSignal & toObservable", "## Bridging RxJS and Signals\n\n`toSignal` converts continuous RxJS streams into easy-to-read template signals without manual async pipe unwrapping.\n\n```typescript\nreadonly courses$ = this.http.get<Course[]>('/api/courses');\nreadonly courses = toSignal(this.courses$, { initialValue: [] });\n```\n\n### Best Practice\nUse RxJS for event orchestration, timing, and HTTP requests, and Signals for template state presentation."),
                            ("Linked Signals & Dynamic State Derivations", "## Linked Signals Pattern\n\nLinked signals automatically update their fallback value when dependent state shifts.\n\n```typescript\nconst selectedOption = linkedSignal(() => this.defaultOption());\n```\n\n### Practical Example\nResetting pagination to page 1 whenever search filters or sort options change."),
                        ],
                    },
                    {
                        "title": "Enterprise Routing & Performance",
                        "lessons": [
                            ("Functional Route Guards & Resolvers", "## Modern Route Guards\n\nFunctional guards replace class-based guard boilerplate.\n\n```typescript\nexport const authGuard: CanActivateFn = (route, state) => {\n  const authService = inject(AuthService);\n  const router = inject(Router);\n  return authService.isAuthenticated() ? true : router.createUrlTree(['/login']);\n};\n```\n\n### Features\n- Direct dependency injection\n- Easy unit testing without complex testbed mocking."),
                            ("Lazy Loading Strategies & Preloading", "## Code Splitting\n\nChunk bundles by route to optimize initial transfer size.\n\n```typescript\n{\n  path: 'courses',\n  loadComponent: () => import('./course-list').then(m => m.CourseListComponent)\n}\n```\n\n### Preloading Strategies\n- `PreloadAllModules`\n- Custom predictive preloading on user link hover."),
                            ("Query Parameter Synchronization", "## URL State as Single Source of Truth\n\nSynchronizing search terms, tab selections, and filters with route parameters allows shareable URLs and bookmarking.\n\n```typescript\nthis.router.navigate([], {\n  relativeTo: this.route,\n  queryParams: { search: term },\n  queryParamsHandling: 'merge'\n});\n```"),
                            ("Hydration & Server-Side Rendering (SSR)", "## Angular SSR & Hydration\n\nNon-destructive hydration ensures smooth transition from server-rendered HTML to interactive client DOM without flicker.\n\n### Optimization Tips\n- Avoid direct `window` access during SSR\n- Use `isPlatformBrowser` guards for client-only logic."),
                        ],
                    },
                    {
                        "title": "Scalable State Management & Architecture",
                        "lessons": [
                            ("Service-with-a-Subject vs Signal Store", "## Architecture Patterns\n\nComparing lightweight service stores with formal state architectures.\n\n### When to use:\n- **Signal Service:** Simple, domain-specific component trees\n- **NgRx Signal Store:** Complex caching, optimistic UI updates, multi-entity relationships."),
                            ("Entity Management & Normalization", "## Normalizing Nested Collections\n\nStoring collections by ID prevents data duplication and keeps updates O(1).\n\n```typescript\ninterface EntityState<T> {\n  ids: (string | number)[];\n  entities: Record<string | number, T>;\n}\n```"),
                            ("Optimistic Updates & Error Rollback", "## Optimistic UI Patterns\n\nUpdating local state immediately before the HTTP response arrives, rolling back on error.\n\n```typescript\nmarkLessonCompleted(id: number) {\n  const prev = this.completed();\n  this.completed.update(set => new Set([...set, id]));\n  this.http.post(`/api/lessons/${id}/complete`).subscribe({\n    error: () => this.completed.set(prev)\n  });\n}\n```"),
                            ("Micro-Frontend Design & Module Federation", "## Micro-Frontend Boundaries\n\nDecomposing monolithic SPAs into independently deployable enterprise sub-apps with Webpack/Vite module federation."),
                        ],
                    },
                    {
                        "title": "Testing, Tooling & Production Delivery",
                        "lessons": [
                            ("Unit Testing Signals with Jasmine", "## Testing Signals\n\nTesting reactive signals synchronously without asynchronous fixture waits.\n\n```typescript\nit('should increment counter', () => {\n  component.increment();\n  expect(component.count()).toBe(1);\n});\n```"),
                            ("Component Harnesses & Accessibility", "## Angular CDK Harnesses\n\nTesting user interaction through accessible DOM harnesses ensuring screen-reader compliance."),
                            ("Bundle Budget Audits & Lighthouse Optimization", "## Production Performance\n\nEnforcing build bundle budgets in `angular.json` and optimizing Largest Contentful Paint (LCP) and Cumulative Layout Shift (CLS)."),
                            ("Continuous Delivery & Automated Quality Gates", "## Enterprise CI/CD Pipeline\n\nIntegrating headless Chromium test runners, strict linting, and automated Docker container builds."),
                        ],
                    },
                    {
                        "title": "Enterprise Security, CSRF & Content Security Policies",
                        "lessons": [
                            ("Cross-Site Scripting (XSS) Prevention & DomSanitizer", "## Preventing Cross-Site Scripting in Angular\n\nAngular treats all values as untrusted by default. When values are inserted into the DOM via interpolation or property binding, Angular automatically sanitizes them.\n\n### Built-in Contextual Sanitization\nAngular provides distinct sanitization contexts:\n- **HTML:** Bound to `innerHTML`\n- **Style:** Bound to `style.color` or `[style]`\n- **Script:** Never allowable via bindings\n- **URL / ResourceURL:** Bound to `href`, `src`\n\n### Working with DomSanitizer\nWhen rendering trusted external HTML (e.g., vetted LMS course articles), inject `DomSanitizer`:\n\n```typescript\nimport { Component, inject, input } from '@angular/core';\nimport { DomSanitizer, SafeHtml } from '@angular/platform-browser';\n\n@Component({\n  selector: 'app-lesson-content',\n  standalone: true,\n  template: `<div [innerHTML]=\"trustedContent\"></div>`\n})\nexport class LessonContentComponent {\n  private sanitizer = inject(DomSanitizer);\n  rawHtml = input.required<string>();\n\n  get trustedContent(): SafeHtml {\n    return this.sanitizer.bypassSecurityTrustHtml(this.rawHtml());\n  }\n}\n```\n\n### Security Best Practices\n1. Never bypass security trust with user-supplied input.\n2. Rely on Angular template syntax instead of manual DOM mutations (`ElementRef.nativeElement.innerHTML`).\n3. Audit all usages of `bypassSecurityTrust*` during peer reviews."),
                            ("CSRF Token Interceptors & Cookie Authentication", "## Cross-Site Request Forgery (CSRF) Defense\n\nIn enterprise web applications where sessions or authentication tokens are stored in `HttpOnly` cookies, Angular must synchronize with backend CSRF protection mechanisms.\n\n### HttpClientXsrfModule & Default Token Names\nBy default, Angular looks for a cookie named `XSRF-TOKEN` and sets an HTTP header named `X-XSRF-TOKEN`.\n\n```typescript\nimport { provideHttpClient, withXsrfConfiguration } from '@angular/common/http';\n\nexport const appConfig: ApplicationConfig = {\n  providers: [\n    provideHttpClient(\n      withXsrfConfiguration({\n        cookieName: 'csrftoken',\n        headerName: 'X-CSRFToken',\n      })\n    )\n  ]\n};\n```\n\n### Custom Functional Interceptors\nFor fine-grained control across microservice domains:\n\n```typescript\nimport { HttpInterceptorFn } from '@angular/common/http';\n\nexport const csrfInterceptor: HttpInterceptorFn = (req, next) => {\n  const token = getCookie('csrftoken');\n  if (token && !['GET', 'HEAD', 'OPTIONS'].includes(req.method)) {\n    const cloned = req.clone({\n      headers: req.headers.set('X-CSRFToken', token)\n    });\n    return next(cloned);\n  }\n  return next(req);\n};\n```\n\n### Verification Checklist\n1. Ensure `SameSite=Lax` or `SameSite=Strict` is configured on all session cookies.\n2. Enforce CSRF tokens on all state-mutating requests (`POST`, `PUT`, `PATCH`, `DELETE`)."),
                            ("Strict Content Security Policy (CSP) & Nonces", "## Enforcing Content Security Policy (CSP)\n\nA Content Security Policy restricts the sources from which browsers can load resources (scripts, styles, images, fonts), mitigating code injection vulnerabilities.\n\n### Modern CSP Headers\nA production CSP header for an Angular application looks like:\n\n```http\nContent-Security-Policy: default-src 'self'; script-src 'self' 'nonce-random123'; style-src 'self' 'nonce-random123' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://api.skillsphere.com;\n```\n\n### Configuring Angular CSP Nonces\nAngular supports runtime nonces to allow inline critical CSS without requiring `'unsafe-inline'`:\n\n```typescript\nimport { CSP_NONCE } from '@angular/core';\n\nexport const appConfig: ApplicationConfig = {\n  providers: [\n    {\n      provide: CSP_NONCE,\n      useValue: window.__SERVER_CSP_NONCE__\n    }\n  ]\n};\n```\n\n### Key Takeaways\n- Eliminate `'unsafe-inline'` and `'unsafe-eval'` from script directives.\n- Use CSP reporting endpoints (`report-to` or `report-uri`) to catch policy violations in production."),
                            ("Role-Based Route Guards & JWT Claims Parsing", "## Role-Based Access Control (RBAC) in Angular\n\nSecuring application routes requires validating authentication status and checking authorized user roles before route activation.\n\n### Functional Role Guards\nModern Angular replaces class-based guards with composable functional guards:\n\n```typescript\nimport { CanActivateFn, Router } from '@angular/router';\nimport { inject } from '@angular/core';\nimport { AuthService } from '../core/services/auth.service';\n\nexport const roleGuard = (allowedRoles: string[]): CanActivateFn => {\n  return () => {\n    const auth = inject(AuthService);\n    const router = inject(Router);\n    const userRole = auth.currentUserRole();\n\n    if (!auth.isAuthenticated()) {\n      return router.createUrlTree(['/login']);\n    }\n\n    if (userRole && allowedRoles.includes(userRole)) {\n      return true;\n    }\n\n    return router.createUrlTree(['/unauthorized']);\n  };\n};\n```\n\n### Route Declaration Example\n```typescript\nexport const routes: Routes = [\n  {\n    path: 'instructor/dashboard',\n    loadComponent: () => import('./instructor-dash').then(m => m.InstructorDashboardComponent),\n    canActivate: [roleGuard(['INSTRUCTOR', 'ADMIN'])]\n  }\n];\n```\n\n### Safety Principles\n- Client-side route guards are for user experience and navigation control.\n- Backend APIs must remain the final authoritative authority on every endpoint."),
                            ("Secure Session Invalidation & Automatic Logout", "## Client-Side Session Invalidation & Timeout\n\nProper session lifecycle management guarantees that user credentials and stale authorization tokens do not persist on shared or compromised devices.\n\n### Handling 401 Unauthorized Responses\nWhen a backend returns HTTP 401 and token refresh fails, the client must purge memory state:\n\n```typescript\nimport { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';\nimport { inject } from '@angular/core';\nimport { catchError, throwError } from 'rxjs';\nimport { AuthService } from './auth.service';\n\nexport const authErrorInterceptor: HttpInterceptorFn = (req, next) => {\n  const auth = inject(AuthService);\n\n  return next(req).pipe(\n    catchError((error: HttpErrorResponse) => {\n      if (error.status === 401 && !req.url.includes('/api/auth/login/')) {\n        auth.logout();\n      }\n      return throwError(() => error);\n    })\n  );\n};\n```\n\n### Inactivity Timeout Service\nImplementing a client-side timer that tracks user interactions:\n- Monitors `mousemove`, `keydown`, `click` events\n- Dispatches a warning dialog at 15 minutes of inactivity\n- Automatically executes clean logout at 20 minutes."),
                        ],
                    },
                ],
            },
            {
                "title": "FastAPI: High-Performance Python Microservices",
                "instructor_username": "sarah_connor",
                "is_published": True,
                "description": (
                    "Build resilient, asynchronous Python microservices with FastAPI. Deep dive into Pydantic v2 "
                    "validation, asynchronous SQLAlchemy, PostgreSQL pooling, JWT authentication, and Docker deployment."
                ),
                "modules": [
                    {
                        "title": "FastAPI Foundations & Async I/O",
                        "lessons": [
                            ("Async Python Event Loop & Uvicorn", "## Asynchronous Python in Practice\n\nUnderstanding `async`/`await` and non-blocking I/O execution with ASGI servers.\n\n```python\nfrom fastapi import FastAPI\napp = FastAPI(title='LMS Service')\n\n@app.get('/health')\nasync def health():\n    return {'status': 'healthy'}\n```"),
                            ("Path Parameters, Query Strings & Status Codes", "## Routing & OpenAPI Specifications\n\nFastAPI automatically generates interactive Swagger documentation from type annotations and routing definitions.\n\n```python\n@app.get('/courses/{course_id}', status_code=200)\nasync def get_course(course_id: int, include_drafts: bool = False):\n    return {'course_id': course_id, 'drafts': include_drafts}\n```"),
                            ("Dependency Injection System", "## Dependency Injection in FastAPI\n\nUsing `Depends` to inject database sessions, configuration objects, and authentication context cleanly."),
                            ("Custom Middlewares & Request Timing", "## Middleware Architecture\n\nAdding timing headers, distributed tracing IDs, and CORS policies across incoming microservice requests."),
                        ],
                    },
                    {
                        "title": "Validation & Schemas with Pydantic v2",
                        "lessons": [
                            ("Pydantic Models & Field Validations", "## Data Validation\n\nPydantic v2 compiles validation logic in Rust for blazingly fast schema serialization.\n\n```python\nfrom pydantic import BaseModel, Field, EmailStr\n\nclass UserCreate(BaseModel):\n    username: str = Field(..., min_length=3, max_length=50)\n    email: EmailStr\n```"),
                            ("Nested Schemas & Polymorphic Data", "## Handling Complex Schemas\n\nModeling relational structures, polymorphic payloads, and custom validators for enterprise APIs."),
                            ("Settings Management & Environment Variables", "## BaseSettings\n\nType-safe environment configuration management using `pydantic-settings`."),
                            ("Error Handling & Custom Request Validation Handlers", "## Error Serialization\n\nCustomizing 422 Unprocessable Entity responses into clean, client-friendly error dictionaries."),
                        ],
                    },
                    {
                        "title": "Relational Databases with Async SQLAlchemy",
                        "lessons": [
                            ("Async Engine & Connection Pooling", "## Async Database Access\n\nConfiguring `asyncpg` with SQLAlchemy 2.0 async engine and resilient connection pools.\n\n```python\nfrom sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker\nengine = create_async_engine('postgresql+asyncpg://user:pass@localhost/db', pool_size=20)\n```"),
                            ("Async CRUD Operations & Relations", "## Declarative Models & Queries\n\nExecuting joined loads, eager fetching, and bulk inserts asynchronously."),
                            ("Database Migrations with Alembic", "## Database Version Control\n\nGenerating revision scripts, applying forward migrations, and handling zero-downtime column migrations."),
                            ("Transaction Management & Isolation Levels", "## ACID Transactions\n\nManaging explicit database transactions, savepoints, and preventing race conditions during concurrent user operations."),
                        ],
                    },
                    {
                        "title": "Authentication, Security & RBAC",
                        "lessons": [
                            ("OAuth2 Password Flow & JWT Tokens", "## Stateless Authentication\n\nIssuing short-lived access tokens and refresh tokens using cryptographic signature algorithms."),
                            ("Role-Based Access Control (RBAC)", "## Permission Scopes\n\nRestricting endpoint access by user roles (Student, Instructor, Admin) using dependency injection."),
                            ("Password Hashing with Argon2 & Bcrypt", "## Secure Hashing\n\nEmploying modern adaptive hashing algorithms with automatic salting to protect user credentials."),
                            ("Rate Limiting & Security Headers", "## API Hardening\n\nProtecting endpoints against brute-force attacks and abuse using sliding-window rate limiters."),
                        ],
                    },
                    {
                        "title": "Microservice Architecture & Deployment",
                        "lessons": [
                            ("Background Tasks & Celery / Redis Integration", "## Asynchronous Job Processing\n\nOffloading heavy tasks (certificate generation, email dispatch) to background worker queues."),
                            ("Containerization with Multi-Stage Dockerfiles", "## Production Containers\n\nBuilding minimal, secure production Docker containers with non-root runtime users."),
                            ("Health Checks & Graceful Shutdowns", "## Production Reliability\n\nImplementing liveness/readiness probes and handling SIGTERM signals gracefully."),
                            ("Distributed Tracing & Structured JSON Logging", "## Observability\n\nExporting structured JSON logs and distributed traces to Prometheus and Grafana."),
                        ],
                    },
                    {
                        "title": "Advanced Asynchronous Patterns & WebSockets",
                        "lessons": [
                            ("Real-Time Bi-Directional Streaming with WebSockets", "## WebSockets with FastAPI\n\nWebSockets enable persistent, bi-directional, full-duplex communication channels between clients and Python ASGI microservices.\n\n```python\nfrom fastapi import FastAPI, WebSocket, WebSocketDisconnect\n\napp = FastAPI()\n\n@app.websocket('/ws/notifications/{user_id}')\nasync def notification_endpoint(websocket: WebSocket, user_id: int):\n    await websocket.accept()\n    try:\n        while True:\n            data = await websocket.receive_text()\n            await websocket.send_text(f'Echo: {data}')\n    except WebSocketDisconnect:\n        print(f'User {user_id} disconnected')\n```\n\n### Production Considerations\n- Use authentication query params or initial handshake message to validate tokens.\n- Enforce maximum ping/pong heartbeat intervals to prune dead connections."),
                            ("Managing Connection Managers & Broadcast Channels", "## WebSocket Broadcast Manager\n\nTracking active connections across multiple rooms and broadcasting events cleanly.\n\n```python\nclass ConnectionManager:\n    def __init__(self):\n        self.active_connections: dict[int, list[WebSocket]] = {}\n\n    async def connect(self, course_id: int, websocket: WebSocket):\n        await websocket.accept()\n        self.active_connections.setdefault(course_id, []).append(websocket)\n\n    async def broadcast_course(self, course_id: int, message: dict):\n        for connection in self.active_connections.get(course_id, []):\n            await connection.send_json(message)\n```"),
                            ("Async Generators & Server-Sent Events (SSE)", "## Server-Sent Events (SSE)\n\nWhen communication is strictly one-way (server to client), SSE provides a lightweight alternative to WebSockets over standard HTTP.\n\n```python\nfrom fastapi.responses import StreamingResponse\nimport asyncio\n\nasync def event_stream():\n    while True:\n        yield f'data: {{\"time\": {time.time()}}}\\n\\n'\n        await asyncio.sleep(2)\n\n@app.get('/events')\nasync def stream_events():\n    return StreamingResponse(event_stream(), media_type='text/event-stream')\n```"),
                            ("Handling Long-Running Tasks with Redis Pub/Sub", "## Multi-Worker Event Distribution\n\nScaling WebSocket connections across multiple Uvicorn worker processes with Redis Pub/Sub channels.\n\n### Flow Architecture\n1. Web worker publishes message to Redis topic (`PUBLISH course_updates msg`).\n2. All worker nodes subscribe to the topic and broadcast to their local connected WebSockets.\n3. Eliminates in-memory isolation across cluster nodes."),
                            ("Concurrency Limits & Semaphore Throttling", "## Concurrency Control with Asyncio Semaphores\n\nPreventing resource exhaustion during spikes by bounding concurrent downstream requests.\n\n```python\nimport asyncio\n\nsem = asyncio.Semaphore(10) # Max 10 concurrent requests\n\nasync def fetch_external_resource():\n    async with sem:\n        return await http_client.get('https://api.thirdparty.com')\n```"),
                        ],
                    },
                ],
            },
            {
                "title": "Full-Stack TypeScript with Node.js & PostgreSQL",
                "instructor_username": "sarah_connor",
                "is_published": True,
                "description": (
                    "Construct robust full-stack applications with TypeScript across the entire stack. Learn clean "
                    "architecture with Express, Prisma ORM, PostgreSQL transactions, and automated integration testing."
                ),
                "modules": [
                    {
                        "title": "TypeScript Foundations for Backend",
                        "lessons": [
                            ("Strict Typing & Advanced Types", "## TypeScript on the Server\n\nLeveraging strict null checks, union types, and generics to eliminate runtime errors in server applications."),
                            ("Module Systems (ESM vs CommonJS)", "## Modern Module Resolution\n\nConfiguring `tsconfig.json` for ES Modules, top-level await, and native Node.js execution."),
                            ("Dependency Management & Monorepo Tooling", "## Code Organization\n\nStructuring shared types and utility libraries across frontend and backend services."),
                            ("Configuration Validation with Zod", "## Runtime Type Validation\n\nValidating environment variables and external payloads with Zod schemas for total type safety."),
                        ],
                    },
                    {
                        "title": "REST API Architecture with Express & Node.js",
                        "lessons": [
                            ("Clean Architecture & Controller-Service Pattern", "## Layered Architecture\n\nDecoupling HTTP transport controllers from business logic services and persistence repositories."),
                            ("Async Error Handling Middleware", "## Centralized Error Handling\n\nCatching asynchronous exceptions and translating domain errors into standardized HTTP responses."),
                            ("Request Validation & Sanitization", "## Input Sanitization\n\nProtecting against injection attacks and malformed payloads using reusable Express middleware."),
                            ("Logging with Winston & Morgan", "## Server Logging\n\nStructuring log levels and rotating log files for production auditing and monitoring."),
                        ],
                    },
                    {
                        "title": "Database Modeling with Prisma & PostgreSQL",
                        "lessons": [
                            ("Prisma Schema Design & Relations", "## Type-Safe Persistence\n\nDefining relational models, composite keys, and cascade constraints in `schema.prisma`."),
                            ("Query Optimization & Indexing", "## Database Indexing\n\nCreating B-tree and composite indexes in PostgreSQL to accelerate high-volume query filters."),
                            ("Transactions & Concurrency Control", "## Interactive Transactions\n\nGuaranteed consistency across multiple database mutations using Prisma interactive transactions."),
                            ("Seeding Data & Migration Workflows", "## Database Versioning\n\nManaging schema migrations and writing repeatable seed scripts for development environments."),
                        ],
                    },
                    {
                        "title": "Security, Authentication & Testing",
                        "lessons": [
                            ("Secure JWT Authentication Flow", "## Token Security\n\nImplementing secure HTTP-only cookie storage, token rotation, and refresh workflows."),
                            ("Integration Testing with Jest & Supertest", "## Automated Test Suites\n\nWriting fast, isolated API integration tests against ephemeral test database containers."),
                            ("CORS, Helmet & Security Headers", "## Defense-in-Depth\n\nHardening Express apps with Helmet, Content Security Policy, and strict CORS rules."),
                            ("Docker Compose for Local Development", "## Containerized Dev Environment\n\nOrchestrating Node.js, PostgreSQL, and Redis locally with Docker Compose."),
                        ],
                    },
                    {
                        "title": "Production Deployment & Scaling",
                        "lessons": [
                            ("Cluster Mode & PM2 Process Management", "## Multi-Core Scaling\n\nUtilizing all CPU cores with Node.js cluster mode and PM2 process supervision."),
                            ("Database Connection Pooling with PgBouncer", "## Connection Pooling\n\nPreventing PostgreSQL connection starvation under high concurrency with PgBouncer."),
                            ("CI/CD Pipeline with GitHub Actions", "## Automated Pipelines\n\nRunning automated lints, tests, and building optimized Docker artifacts on every commit."),
                            ("Monitoring, Sentry & APM Metrics", "## Production Observability\n\nCapturing unhandled exceptions and performance bottlenecks in real-time with Sentry."),
                        ],
                    },
                    {
                        "title": "Caching Strategies & Background Jobs with Redis",
                        "lessons": [
                            ("In-Memory Caching Patterns with Redis & Key Expiration", "## High-Performance Caching with Redis\n\nDatabase queries for static or slow-changing data (course catalogs, syllabus outlines) should be cached in Redis with strict time-to-live (TTL).\n\n### Cache-Aside Implementation\n```typescript\nimport { createClient } from 'redis';\n\nconst redis = createClient({ url: process.env.REDIS_URL });\nawait redis.connect();\n\nexport async function getCourseWithCache(courseId: number): Promise<Course> {\n  const cacheKey = `course:${courseId}`;\n  const cached = await redis.get(cacheKey);\n\n  if (cached) {\n    return JSON.parse(cached);\n  }\n\n  const course = await prisma.course.findUniqueOrThrow({\n    where: { id: courseId },\n    include: { modules: { include: { lessons: true } } }\n  });\n\n  await redis.setEx(cacheKey, 3600, JSON.stringify(course));\n  return course;\n}\n```\n\n### Expiration Strategies\n- Use jitter on TTLs (`3600 + Math.random() * 300`) to prevent cache stampedes.\n- Evict keys explicitly upon course updates."),
                            ("BullMQ: Reliable Background Job Queues in Node.js", "## Asynchronous Background Processing with BullMQ\n\nOffload heavy operations such as PDF certificate generation, thumbnail resizing, and email notifications to background workers.\n\n### Defining Queues and Workers\n```typescript\nimport { Queue, Worker } from 'bullmq';\n\nconst connection = { host: 'localhost', port: 6379 };\n\nexport const certificateQueue = new Queue('certificate-generation', { connection });\n\nexport async function enqueueCertificate(studentId: number, courseId: number) {\n  await certificateQueue.add('generate-pdf', { studentId, courseId }, {\n    attempts: 3,\n    backoff: { type: 'exponential', delay: 2000 }\n  });\n}\n\nconst worker = new Worker('certificate-generation', async job => {\n  const { studentId, courseId } = job.data;\n  console.log(`Generating certificate for student ${studentId} in course ${courseId}`);\n  await generateCertificatePDF(studentId, courseId);\n}, { connection });\n```"),
                            ("Handling Concurrency & Distributed Locks with Redlock", "## Distributed Locking with Redlock\n\nIn multi-instance Node.js deployments, prevent race conditions (such as double enrollment or concurrent balance deductions) using distributed locks.\n\n### Implementing Redlock\n```typescript\nimport Redlock from 'redlock';\nimport Client from 'ioredis';\n\nconst redisClient = new Client();\nconst redlock = new Redlock([redisClient], {\n  driftFactor: 0.01,\n  retryCount: 3,\n  retryDelay: 200,\n  retryJitter: 200\n});\n\nexport async function enrollWithLock(studentId: number, courseId: number) {\n  const lockKey = `locks:enroll:${studentId}:${courseId}`;\n  const lock = await redlock.acquire([lockKey], 5000);\n\n  try {\n    const existing = await prisma.enrollment.findFirst({\n      where: { studentId, courseId }\n    });\n    if (existing) throw new Error('Already enrolled');\n\n    return await prisma.enrollment.create({ data: { studentId, courseId } });\n  } finally {\n    await lock.release();\n  }\n}\n```"),
                            ("Worker Process Scaling & Dead-Letter Job Isolation", "## Worker Resilience & Dead-Letter Isolation\n\nFailing jobs must not block processing queues. Isolate poison-pill messages and notify engineering teams.\n\n### Handling Failed Jobs\n```typescript\nworker.on('failed', (job, err) => {\n  console.error(`Job ${job?.id} failed with error: ${err.message}`);\n  if (job && job.attemptsMade >= (job.opts.attempts || 1)) {\n    console.error(`Job ${job.id} moved to dead-letter queue!`);\n  }\n});\n```\n\n### Worker Scaling Rules\n- Scale workers independently from web API pods using Kubernetes Horizontal Pod Autoscaler (HPA) driven by queue length.\n- Ensure all jobs are strictly idempotent."),
                            ("Cache Invalidation & Write-Through vs Cache-Aside", "## Cache Invalidation Topologies\n\n'There are only two hard things in Computer Science: cache invalidation and naming things.' — Phil Karlton.\n\n### Invalidation Pattern\n```typescript\nexport async function updateCourse(id: number, data: UpdateCourseDto) {\n  const updated = await prisma.course.update({ where: { id }, data });\n  await redis.del(`course:${id}`);\n  await redis.del('courses:catalog');\n  return updated;\n}\n```"),
                        ],
                    },
                ],
            },
            {
                "title": "Applied Machine Learning & Deep Learning with Python",
                "instructor_username": "marcus_vance",
                "is_published": True,
                "description": (
                    "A comprehensive, practical exploration of machine learning and deep neural networks. From data "
                    "preprocessing and Scikit-Learn pipelines to training computer vision models in PyTorch."
                ),
                "modules": [
                    {
                        "title": "Feature Engineering & Data Preprocessing",
                        "lessons": [
                            ("NumPy Vectorization & Pandas Wrangling", "## High-Performance Data Manipulation\n\nMastering array vectorization, broadcast operations, and handling missing values with Pandas."),
                            ("Categorical Encoding & Feature Scaling", "## Data Transformation\n\nApplying One-Hot Encoding, Target Encoding, StandardScaler, and RobustScaler to prevent data leakage."),
                            ("Dimensionality Reduction with PCA & t-SNE", "## Dimensionality Reduction\n\nCompressing high-dimensional feature spaces while preserving variance and visualizing clusters."),
                            ("Constructing Resilient Scikit-Learn Pipelines", "## ML Pipelines\n\nEncapsulating transformation and estimator steps into reproducible, leak-free pipelines."),
                        ],
                    },
                    {
                        "title": "Supervised Learning & Model Evaluation",
                        "lessons": [
                            ("Linear Models, Regularization (Lasso/Ridge)", "## Regularized Regression\n\nPreventing overfitting through L1 and L2 penalty terms in high-dimensional feature spaces."),
                            ("Ensemble Methods: Random Forests & XGBoost", "## Gradient Boosting\n\nConstructing gradient boosted decision trees for state-of-the-art tabular performance."),
                            ("Cross-Validation & Hyperparameter Tuning", "## Model Selection\n\nImplementing Stratified K-Fold cross validation and Bayesian optimization with Optuna."),
                            ("Classification Metrics: ROC-AUC, F1 & Precision-Recall", "## Evaluation Beyond Accuracy\n\nNavigating imbalanced class distributions with Precision-Recall curves and F1-score optimization."),
                        ],
                    },
                    {
                        "title": "Deep Learning Foundations with PyTorch",
                        "lessons": [
                            ("Tensors, Autograd & Computational Graphs", "## PyTorch Core\n\nUnderstanding dynamic computation graphs and automatic differentiation with `torch.autograd`."),
                            ("Building Multi-Layer Perceptrons (MLPs)", "## Neural Network Architecture\n\nImplementing custom `nn.Module` classes, activation functions, and layer initializations."),
                            ("Loss Functions & Optimization Algorithms", "## Training Dynamics\n\nComparing SGD, AdamW, and learning rate schedulers for accelerated convergence."),
                            ("Custom Datasets & DataLoaders", "## Efficient Data Ingestion\n\nBuilding multi-threaded, memory-mapped PyTorch DataLoaders for large datasets."),
                        ],
                    },
                    {
                        "title": "Convolutional Networks & Computer Vision",
                        "lessons": [
                            ("Convolution, Pooling & Receptive Fields", "## Computer Vision Mechanics\n\nUnderstanding 2D spatial convolutions, stride, padding, and feature map extraction."),
                            ("Transfer Learning with ResNet & EfficientNet", "## Transfer Learning\n\nFine-tuning pre-trained ImageNet backbones for custom classification tasks with minimal data."),
                            ("Data Augmentation with Torchvision", "## Generalization\n\nApplying random rotations, crops, color jitters, and mixup to boost model robustness."),
                            ("Model Export to ONNX & Quantization", "## Inference Optimization\n\nExporting PyTorch models to ONNX and applying INT8 post-training quantization for low-latency inference."),
                        ],
                    },
                    {
                        "title": "MLOps & Model Serving",
                        "lessons": [
                            ("Model Serving with FastAPI & TorchScript", "## Real-Time Predictions\n\nPackaging models into high-throughput asynchronous REST APIs."),
                            ("Experiment Tracking with MLflow", "## Reproducibility\n\nLogging hyperparameters, metrics, and model artifacts to central MLflow registries."),
                            ("Monitoring Data Drift & Model Degradation", "## Production Monitoring\n\nDetecting distribution shifts in production feature inputs over time."),
                            ("Continuous Training Pipelines", "## Automated Retraining\n\nTriggering automated pipeline executions when data drift thresholds are exceeded."),
                        ],
                    },
                    {
                        "title": "Advanced Deep Learning & Transfer Learning",
                        "lessons": [
                            ("Transfer Learning with Pretrained Vision Models", "## Transfer Learning in Computer Vision\n\nLeveraging feature representations from foundation models pretrained on ImageNet.\n\n```python\nimport torch\nimport torchvision.models as models\nimport torch.nn as nn\n\nmodel = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)\nfor param in model.parameters():\n    param.requires_grad = False # Freeze backbone\n\nmodel.fc = nn.Sequential(\n    nn.Linear(model.fc.in_features, 256),\n    nn.ReLU(),\n    nn.Dropout(0.3),\n    nn.Linear(256, 10)\n)\n```\n\n### Key Principles\n- Freeze early feature extraction layers to preserve general edge/texture detectors.\n- Fine-tune higher-level semantic layers with low learning rates ($10^{-5}$)."),
                            ("Fine-Tuning BERT for Text Classification", "## Transformer Transfer Learning\n\nFine-tuning bidirectional encoder representations for sentiment analysis and intent classification.\n\n```python\nfrom transformers import AutoModelForSequenceClassification, AutoTokenizer\n\ntokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')\nmodel = AutoModelForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=3)\n```\n\n### Best Practices\n- Apply warmup linear schedulers to prevent catastrophic forgetting.\n- Use gradient clipping ($||g|| \\le 1.0$) to stabilize optimization."),
                            ("Data Augmentation Techniques with Albumentations", "## Robust Data Augmentation\n\nExpanding training distributions with geometric and photometric transformations.\n\n```python\nimport albumentations as A\n\ntransform = A.Compose([\n    A.RandomCrop(width=224, height=224),\n    A.HorizontalFlip(p=0.5),\n    A.RandomBrightnessContrast(p=0.2),\n    A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),\n])\n```"),
                            ("Learning Rate Schedulers & Early Stopping Callbacks", "## Training Optimization & Convergence\n\nDynamically adapting learning rates based on validation loss plateaus.\n\n```python\nfrom torch.optim.lr_scheduler import ReduceLROnPlateau\n\noptimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-2)\nscheduler = ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=3)\n```"),
                            ("Mixed Precision Training with PyTorch AMP", "## Accelerating Training with Automatic Mixed Precision\n\nUtilizing FP16 computation on Tensor Cores while preserving FP32 master weights.\n\n```python\nfrom torch.cuda.amp import autocast, GradScaler\n\nscaler = GradScaler()\nfor inputs, targets in dataloader:\n    optimizer.zero_grad()\n    with autocast():\n        outputs = model(inputs)\n        loss = criterion(outputs, targets)\n    scaler.scale(loss).backward()\n    scaler.step(optimizer)\n    scaler.update()\n```"),
                        ],
                    },
                ],
            },
            {
                "title": "Generative AI & LLM Engineering with LangChain",
                "instructor_username": "marcus_vance",
                "is_published": True,
                "description": (
                    "Build next-generation AI applications with Large Language Models. Master prompt engineering, "
                    "vector indexing, Retrieval-Augmented Generation (RAG), and autonomous agentic workflows."
                ),
                "modules": [
                    {
                        "title": "LLM Fundamentals & Prompt Engineering",
                        "lessons": [
                            ("Transformer Architecture & Tokenization", "## Understanding LLMs\n\nExploring self-attention mechanisms, causal language modeling, and token budgets."),
                            ("Few-Shot Prompting & Chain-of-Thought", "## Prompt Techniques\n\nEliciting structured, logical reasoning through structured few-shot exemplars and step-by-step thinking."),
                            ("Structured Outputs & JSON Mode", "## Reliable Formatting\n\nEnforcing strict Pydantic JSON schemas on model responses for programmatic downstream consumption."),
                            ("Context Window Management & Chunking", "## Context Strategy\n\nSplitting text semantically using recursive character text splitters to prevent semantic loss."),
                        ],
                    },
                    {
                        "title": "Vector Embeddings & Vector Stores",
                        "lessons": [
                            ("Embedding Models & Distance Metrics", "## Vector Representations\n\nComparing cosine similarity, dot product, and euclidean distance in semantic embedding spaces."),
                            ("Vector Databases: Chroma, Qdrant & Pinecone", "## Vector Search Engines\n\nIndexing millions of document vectors with HNSW algorithms for sub-millisecond retrieval."),
                            ("Metadata Filtering & Hybrid Search", "## Precision Search\n\nCombining dense semantic vectors with sparse BM25 keyword matching for optimal recall."),
                            ("Document Ingestion & Updating Strategies", "## Document Pipelines\n\nBuilding resilient ingestion pipelines that handle PDF, Markdown, and API documents."),
                        ],
                    },
                    {
                        "title": "Retrieval-Augmented Generation (RAG)",
                        "lessons": [
                            ("Naive vs Advanced RAG Architecture", "## Enterprise RAG\n\nMoving beyond basic top-k similarity search to multi-query expansion and contextual compression."),
                            ("Reranking with Cross-Encoders", "## Two-Stage Retrieval\n\nEmploying Cohere or BGE rerankers to rank the most relevant text passages before passing them to the generator."),
                            ("Handling Hallucinations & Source Citations", "## Grounded Generation\n\nConstraining LLMs to context-only answers with verbatim source chunk citations."),
                            ("Contextual Compression & Token Optimization", "## Cost Optimization\n\nExtracting only the exact answering sentences from retrieved documents to minimize prompt token usage."),
                        ],
                    },
                    {
                        "title": "LangChain Agents & Tool Calling",
                        "lessons": [
                            ("ReAct Pattern & Reasoning Loops", "## Autonomous Agents\n\nImplementing the Reason-Action-Observation loop to solve multi-step problems autonomously."),
                            ("Custom Tools & API Integrations", "## Tool Execution\n\nEmpowering agents to query internal SQL databases, call REST endpoints, and run sandboxed Python code."),
                            ("Agent Memory & Stateful Conversations", "## Conversational Context\n\nManaging sliding window and summarized conversational memory across long user sessions."),
                            ("Multi-Agent Collaboration with LangGraph", "## Orchestrated Agents\n\nBuilding state machines where specialized agents collaborate on research and code writing."),
                        ],
                    },
                    {
                        "title": "Evaluation, Safety & Production Deployment",
                        "lessons": [
                            ("RAG Triad Evaluation with Ragas", "## Quantitative Evaluation\n\nMeasuring Faithfulness, Answer Relevance, and Context Precision systematically."),
                            ("Guardrails & PII Masking", "## Safety & Compliance\n\nFiltering jailbreaks, toxic prompts, and anonymizing personally identifiable information."),
                            ("Caching LLM Responses with Redis", "## Semantic Caching\n\nSlashing API costs and latency by caching semantically similar query responses."),
                            ("Production Observability with LangSmith", "## Trace Monitoring\n\nMonitoring latency, token expenditures, and tracing execution chains in production."),
                        ],
                    },
                    {
                        "title": "Autonomous Agents & Advanced Tool Execution",
                        "lessons": [
                            ("ReAct Prompting & Thought-Action-Observation Loops", "## The ReAct Architecture\n\nCombining Reasoning (Thought) with Action and Environment Feedback (Observation) in autonomous agents.\n\n```text\nThought: The user wants to know the latest enrollment numbers for course 4.\nAction: query_database(course_id=4)\nObservation: 12 students enrolled.\nThought: I now have the answer.\nFinal Answer: Course 4 currently has 12 active enrolled students.\n```\n\n### Benefits\n- Reduces reasoning drift and hallucination.\n- Provides full interpretability for auditing agent execution paths."),
                            ("OpenAI Function Calling & Dynamic Tool Schemas", "## Function Calling & Tool Definition\n\nBinding typed JSON schema definitions to Large Language Models for deterministic API invocation.\n\n```python\nfrom langchain_core.tools import tool\n\n@tool\ndef calculate_gpa(student_id: int) -> float:\n    \"\"\"Calculate current cumulative grade point average for a given student.\"\"\"\n    return 3.85\n\ntools = [calculate_gpa]\nllm_with_tools = llm.bind_tools(tools)\n```"),
                            ("Human-in-the-Loop Approval & State Persistence", "## Human-in-the-Loop Safety Patterns\n\nPausing autonomous workflows before executing high-risk actions (e.g. database deletions or money transfers).\n\n```python\nfrom langgraph.checkpoint.memory import MemorySaver\n\ncheckpointer = MemorySaver()\n# Interrupt graph execution before the 'send_email' or 'refund' node\napp = workflow.compile(checkpointer=checkpointer, interrupt_before=['execute_refund'])\n```"),
                            ("Self-Correction & Autonomous Reflection Patterns", "## Self-Reflective Loops\n\nEquipping agents with a critic evaluator that inspects their own code or text outputs before finalizing.\n\n### Reflection Workflow\n1. Generator produces candidate code.\n2. Critic tests candidate code in sandbox.\n3. If error occurs, error traceback is fed back to generator for self-repair.\n4. Repeats until all assertions pass or max retries reached."),
                            ("Multi-Agent Debate & Consensus Workflows", "## Multi-Agent Debate\n\nUsing diverse agent personas to review complex technical architecture decisions.\n\n### Persona Specialization\n- **Security Agent:** Scans design for injection and privilege escalation risks.\n- **Performance Agent:** Audits for memory leaks and latency bottlenecks.\n- **Architect Agent:** Reconciles debates and selects optimal compromise."),
                        ],
                    },
                ],
            },
            {
                "title": "Kubernetes for Production: Container Orchestration",
                "instructor_username": "elena_rostova",
                "is_published": True,
                "description": (
                    "Deploy, operate, and scale production-grade microservices in Kubernetes. Learn cluster architecture, "
                    "Helm packaging, Ingress routing, zero-downtime rolling updates, and GitOps deployments."
                ),
                "modules": [
                    {
                        "title": "Cluster Architecture & Core Primitives",
                        "lessons": [
                            ("Control Plane vs Worker Nodes", "## Kubernetes Architecture\n\nDeep dive into kube-apiserver, etcd consensus, kube-scheduler, and kubelet node agents."),
                            ("Pods, ReplicaSets & Declarative Deployments", "## Workload Management\n\nManaging pod lifecycles, self-healing replicas, and declarative YAML manifests."),
                            ("Namespaces, Resource Quotas & Limits", "## Multi-Tenancy\n\nIsolating teams and workloads with CPU/memory requests, limits, and resource quotas."),
                            ("Troubleshooting Pods & Cluster Debugging", "## Diagnostics\n\nMastering `kubectl describe`, `logs`, events, and ephemeral debug containers."),
                        ],
                    },
                    {
                        "title": "Networking, Services & Ingress",
                        "lessons": [
                            ("ClusterIP, NodePort & LoadBalancer", "## Service Discovery\n\nExposing internal microservices with kube-proxy iptables rules and cloud load balancers."),
                            ("Ingress Controllers & Path-Based Routing", "## HTTP Routing\n\nConfiguring NGINX Ingress Controller for TLS termination and multi-service path routing."),
                            ("CoreDNS & Cluster Service Resolution", "## DNS Internals\n\nUnderstanding internal domain resolution (`service.namespace.svc.cluster.local`)."),
                            ("Network Policies & Zero-Trust Security", "## East-West Traffic\n\nRestricting pod-to-pod communication using declarative Kubernetes NetworkPolicies."),
                        ],
                    },
                    {
                        "title": "Configuration & Persistent Storage",
                        "lessons": [
                            ("ConfigMaps & Decoupled Configuration", "## App Configuration\n\nInjecting environment variables and mounting configuration files dynamically."),
                            ("Secret Management & SealedSecrets", "## Secure Credentials\n\nSafely storing TLS certificates, API keys, and database passwords with encryption at rest."),
                            ("PersistentVolumes & PersistentVolumeClaims", "## Stateful Storage\n\nMounting dynamic cloud storage volumes with CSI drivers for stateful workloads."),
                            ("StatefulSets & Ordered Pod Deployment", "## Distributed Databases\n\nRunning databases and message queues with predictable network identities and persistent volumes."),
                        ],
                    },
                    {
                        "title": "Helm Packaging & GitOps Workflows",
                        "lessons": [
                            ("Authoring Helm Charts & Templates", "## Package Management\n\nCreating configurable, reusable Helm charts with dynamic `values.yaml` overlays."),
                            ("Chart Dependencies & Versioning", "## Dependency Trees\n\nManaging subcharts and managing semver releases across development and production."),
                            ("GitOps Principles with ArgoCD", "## GitOps Delivery\n\nContinuous synchronization of cluster state from Git repositories using ArgoCD."),
                            ("Canary Releases & Blue-Green Deployments", "## Progressive Delivery\n\nShifting user traffic gradually using Argo Rollouts to eliminate release downtime."),
                        ],
                    },
                    {
                        "title": "Cluster Security, Monitoring & Scaling",
                        "lessons": [
                            ("Horizontal Pod Autoscaler (HPA)", "## Dynamic Scaling\n\nAutoscaling pod replicas based on real-time CPU, memory, and custom Prometheus metrics."),
                            ("Role-Based Access Control (RBAC)", "## Cluster Security\n\nDefining Roles, ClusterRoles, and ServiceAccounts with least-privilege principles."),
                            ("Prometheus & Grafana Cluster Monitoring", "## Observability\n\nScraping metrics, building cluster dashboards, and configuring Alertmanager rules."),
                            ("Disaster Recovery & Cluster Backups with Velero", "## Business Continuity\n\nBacking up Kubernetes resource manifests and persistent volume snapshots."),
                        ],
                    },
                    {
                        "title": "Service Mesh with Istio & Production Security",
                        "lessons": [
                            ("Service Mesh Fundamentals & Istio Envoy Sidecars", "## Service Mesh Architecture with Istio\n\nA service mesh provides transparent, language-agnostic traffic management, telemetry, and zero-trust security across microservices.\n\n### Data Plane vs Control Plane\n- **Control Plane (`istiod`):** Translates high-level declarative YAML into Envoy configuration and manages TLS certificates.\n- **Data Plane (Envoy Sidecars):** Injected proxies alongside application containers intercepting all ingress and egress TCP/HTTP traffic.\n\n### Enabling Sidecar Injection\n```yaml\napiVersion: v1\nkind: Namespace\nmetadata:\n  name: skillsphere-prod\n  labels:\n    istio-injection: enabled\n```"),
                            ("Mutual TLS (mTLS) Encryption Between Microservices", "## Zero-Trust Security with Strict Mutual TLS\n\nIn cloud environments, internal cluster networks cannot be assumed safe. Istio automatically provisions X.509 certificates and encrypts pod-to-pod traffic.\n\n### Strict PeerAuthentication\n```yaml\napiVersion: security.istio.io/v1beta1\nkind: PeerAuthentication\nmetadata:\n  name: default\n  namespace: skillsphere-prod\nspec:\n  mtls:\n    mode: STRICT\n```\n\n### Benefits\n- Automatic certificate rotation every 24 hours without service restart.\n- Strong cryptographic workload identity via SPIFFE IDs (`spiffe://cluster.local/ns/prod/sa/backend-sa`)."),
                            ("Traffic Management: Canary Releases & Fault Injection", "## Advanced Traffic Routing with VirtualServices\n\nRoute percentages of production traffic to new releases dynamically without modifying deployment manifests.\n\n### 90/10 Canary Split\n```yaml\napiVersion: networking.istio.io/v1alpha3\nkind: VirtualService\nmetadata:\n  name: course-service\nspec:\n  hosts:\n  - course-service\n  http:\n  - route:\n    - destination:\n        host: course-service\n        subset: v1\n      weight: 90\n    - destination:\n        host: course-service\n        subset: v2\n      weight: 10\n```\n\n### Chaos Engineering: Fault Injection\nInject artificial 3-second delays or HTTP 500 errors into 5% of traffic to validate application resilience and circuit breaking."),
                            ("NetworkPolicies & Pod Security Standards (PSS)", "## Hardening Workloads with Pod Security Standards\n\nKubernetes Pod Security Admission enforces baseline and restricted security profiles across namespaces.\n\n### Enforcing Restricted Profile\n```yaml\napiVersion: v1\nkind: Namespace\nmetadata:\n  name: secure-apps\n  labels:\n    pod-security.kubernetes.io/enforce: restricted\n    pod-security.kubernetes.io/enforce-version: latest\n```\n\n### Restricted Constraints\n- Disallows running containers as `root` user (`runAsNonRoot: true`).\n- Drops all default Linux capabilities (`capabilities: drop: ['ALL']`).\n- Disallows privilege escalation (`allowPrivilegeEscalation: false`).\n- Enforces read-only root filesystems."),
                            ("Cluster Observability with Kiali & Prometheus Dashboards", "## Visualizing Microservice Topology with Kiali\n\nKiali analyzes telemetry data reported by Envoy sidecars to render live visual service dependency graphs.\n\n### Key Observability Features\n- Real-time visualization of HTTP response codes (green, yellow, red edges).\n- Live request rate and throughput indicators.\n- Instant detection of failing mTLS handshakes or misconfigured VirtualServices.\n- Direct drill-down into Grafana latency histograms and Jaeger distributed spans."),
                        ],
                    },
                ],
            },
            {
                "title": "System Design: Scalable & Distributed Architectures",
                "instructor_username": "elena_rostova",
                "is_published": True,
                "description": (
                    "Master the principles of designing high-availability, planetary-scale distributed systems. "
                    "Deep dive into caching topologies, database sharding, message queues, and consensus algorithms."
                ),
                "modules": [
                    {
                        "title": "Foundational Principles & CAP Theorem",
                        "lessons": [
                            ("Horizontal vs Vertical Scaling", "## Scalability Fundamentals\n\nAnalyzing bottlenecks, load balancing algorithms, and cost trade-offs of distributed systems."),
                            ("CAP Theorem & PACELC Trade-Offs", "## Consistency vs Availability\n\nUnderstanding trade-offs in distributed data stores under network partition conditions."),
                            ("Latency vs Throughput & Back-of-the-Envelope Math", "## Estimation Math\n\nCalculating storage, bandwidth, and IOPS requirements for systems handling millions of QPS."),
                            ("Single Points of Failure (SPOF) & Redundancy", "## High Availability\n\nDesigning redundant active-active and active-passive topologies with automatic failover."),
                        ],
                    },
                    {
                        "title": "Caching Topologies & Data Storage",
                        "lessons": [
                            ("Cache Patterns: Cache-Aside, Write-Through & Write-Back", "## Caching Strategies\n\nComparing cache invalidation strategies and preventing cache stampedes with probabilistic early expiration."),
                            ("Distributed Caching with Redis Clusters", "## In-Memory Caching\n\nHash slots, master-replica replication, and Sentinel failover in distributed Redis."),
                            ("Relational vs NoSQL: Choosing the Right Engine", "## Storage Engines\n\nSelecting between B-Tree (RDBMS), LSM-Tree (Cassandra), and Document stores based on read/write profiles."),
                            ("Database Sharding & Consistent Hashing", "## Horizontal Partitioning\n\nDistributing data across database shards with consistent hashing rings to minimize re-sharding overhead."),
                        ],
                    },
                    {
                        "title": "Asynchronous Systems & Message Queues",
                        "lessons": [
                            ("Message Queues vs Event Streams (RabbitMQ vs Kafka)", "## Asynchronous Decoupling\n\nComparing message broker push queues with partitioned commit log streaming architectures."),
                            ("Idempotency, At-Least-Once Delivery & Deduplication", "## Reliable Delivery\n\nDesigning consumers that handle duplicate deliveries gracefully using unique idempotency keys."),
                            ("Backpressure, Rate Limiting & Dead Letter Queues", "## Resilient Queuing\n\nProtecting downstream workers with token bucket rate limiters and isolating poison-pill messages."),
                            ("Event Sourcing & CQRS Pattern", "## Advanced Patterns\n\nSeparating write commands from read projections for ultimate auditability and high-throughput reads."),
                        ],
                    },
                    {
                        "title": "Distributed Consensus & Transactions",
                        "lessons": [
                            ("Distributed Consensus: Raft & Paxos", "## Leader Election\n\nUnderstanding leader election, log replication, and quorum consistency in distributed clusters."),
                            ("Two-Phase Commit (2PC) vs Saga Pattern", "## Distributed Transactions\n\nManaging cross-service transactions with compensating transactions instead of blocking distributed locks."),
                            ("Distributed Locking with Redlock & Zookeeper", "## Mutual Exclusion\n\nSafely acquiring distributed mutex locks with TTL expiration and fencing tokens."),
                            ("Clock Synchronization & Lamport Timestamps", "## Time in Distributed Systems\n\nNavigating clock drift and ordering distributed events with logical and vector clocks."),
                        ],
                    },
                    {
                        "title": "Reliability, Observability & Architecture Blueprints",
                        "lessons": [
                            ("Designing a Global URL Shortener (Bitly)", "## System Architecture\n\nEnd-to-end design: Base62 encoding, distributed ID generation, caching, and analytics tracking."),
                            ("Designing a Real-Time Collaborative Feed (Twitter/X)", "## Fan-Out Architectures\n\nComparing Fan-out-on-write vs Fan-out-on-read for high-celebrity timeline generation."),
                            ("Circuit Breakers & Graceful Degradation", "## Fault Tolerance\n\nPreventing cascading failures across microservice chains using Netflix Hystrix / resilience patterns."),
                            ("Distributed Tracing with OpenTelemetry", "## Observability\n\nTracing requests across service boundaries with correlation IDs and Jaeger visualizers."),
                        ],
                    },
                ],
            },
            {
                "title": "Draft: Rust Fundamentals for Systems Programming",
                "instructor_username": "elena_rostova",
                "is_published": False,  # Draft course
                "description": (
                    "An in-depth introduction to systems programming with Rust. Master memory safety without garbage "
                    "collection, ownership semantics, borrowing, lifetimes, and fearless concurrency."
                ),
                "modules": [
                    {
                        "title": "Toolchain & Core Language Syntax",
                        "lessons": [
                            ("Cargo, Rustup & Project Structure", "## The Rust Ecosystem\n\nManaging toolchains, compiling binaries, and running tests with Cargo."),
                            ("Variables, Mutability & Shadowing", "## Immutability by Default\n\nUnderstanding value semantics, immutable bindings, and intentional shadowing."),
                            ("Scalar Types, Compound Types & Functions", "## Type System\n\nIntegers, floating-point numbers, tuples, arrays, and expression-oriented functions."),
                            ("Control Flow & Idiomatic Loops", "## Loops and Branches\n\nWorking with `loop`, `while`, `for` iterators, and labeled break expressions."),
                        ],
                    },
                    {
                        "title": "Ownership, Borrowing & Lifetimes",
                        "lessons": [
                            ("The Ownership Model & Stack vs Heap", "## Memory Management\n\nHow Rust manages memory at compile-time without a runtime garbage collector."),
                            ("References, Borrowing & Aliasing Rules", "## Borrow Checker\n\nEnforcing either multiple immutable references OR a single mutable reference at any time."),
                            ("Slice Types & Memory Safety", "## Contiguous Slices\n\nBorrowing views into collections and strings without data duplication."),
                            ("Lifetimes & Compile-Time Lifetime Annotations", "## Reference Lifetimes\n\nAnnotating relationships between function input and output reference lifetimes."),
                        ],
                    },
                    {
                        "title": "Structs, Enums & Pattern Matching",
                        "lessons": [
                            ("Defining Structs & Method Implementations", "## Data Modeling\n\nCreating custom structs and implementing associated functions with `impl` blocks."),
                            ("Enums & The Powerful Option / Result Types", "## Error Handling\n\nHandling potential failure and missing values cleanly without null pointers."),
                            ("Pattern Matching with match & if let", "## Exhaustive Matching\n\nDeconstructing complex nested enums with compile-time exhaustiveness guarantees."),
                            ("Packages, Crates & Module Visibility", "## Encapsulation\n\nStructuring modular code with `pub`, `use`, and hierarchical file trees."),
                        ],
                    },
                    {
                        "title": "Traits, Generics & Error Handling",
                        "lessons": [
                            ("Defining & Implementing Traits", "## Shared Behavior\n\nCreating interfaces and trait bounds for generic types."),
                            ("Generics & Monomorphization", "## Zero-Cost Abstractions\n\nCompiling highly efficient specialized code without dynamic dispatch overhead."),
                            ("Recoverable Errors with Result & ? Operator", "## Error Propagation\n\nConcise error propagation using the `?` question mark operator."),
                            ("Fearless Concurrency with Threads & Channels", "## Concurrency\n\nSpawning native OS threads and communicating safely using message-passing channels."),
                        ],
                    },
                ],
            },
        ]

        courses = {}
        for c in Course.objects.all():
            courses[c.title] = c

        all_created_lessons = []
        course_lessons_map = {}

        for c_manifest in courses_manifest:
            instructor = users[c_manifest["instructor_username"]]
            course, _ = Course.objects.get_or_create(
                title=c_manifest["title"],
                defaults={
                    "instructor": instructor,
                    "description": c_manifest["description"],
                    "is_published": c_manifest["is_published"],
                },
            )
            courses[course.title] = course
            course_lessons_map[course.id] = []

            for m_idx, m_info in enumerate(c_manifest["modules"], start=1):
                module, _ = Module.objects.get_or_create(
                    course=course,
                    title=m_info["title"],
                    defaults={"order": m_idx},
                )

                for l_idx, (l_title, l_content) in enumerate(m_info["lessons"], start=1):
                    lesson, _ = Lesson.objects.get_or_create(
                        module=module,
                        title=l_title,
                        defaults={
                            "content": l_content,
                            "order": l_idx,
                        },
                    )
                    all_created_lessons.append(lesson)
                    course_lessons_map[course.id].append(lesson)

        # ------------------------------------------------------------------
        # 3. QUIZZES (1 Assessment Quiz for each of the 7 new published courses)
        # ------------------------------------------------------------------
        self.stdout.write("Seeding assessment quizzes, questions, and options...")

        quizzes_manifest = [
            {
                "course_title": "Modern Angular & Enterprise Architecture",
                "title": "Angular Enterprise Mastery Assessment",
                "description": "Comprehensive assessment covering Standalone Components, Signals, Routing, and NgRx.",
                "questions": [
                    ("What is the primary architectural advantage of Angular standalone components?", [
                        ("They eliminate the requirement for NgModule declarations and streamline tree-shaking.", True),
                        ("They automatically convert all CSS into Tailwind classes.", False),
                        ("They disable Angular's change detection engine.", False),
                        ("They require Webpack 4 configuration.", False),
                    ]),
                    ("How does the inject() function differ from constructor-based dependency injection?", [
                        ("It allows functional dependency injection outside of class constructors and in route guards.", True),
                        ("It can only inject HttpClient.", False),
                        ("It is deprecated in Angular 19.", False),
                        ("It creates a new singleton service instance on every call.", False),
                    ]),
                    ("What is the required attribute for an @for loop in Angular's modern control flow?", [
                        ("The track expression (e.g. track item.id)", True),
                        ("The index alias", False),
                        ("The ngForOf attribute", False),
                        ("The pipe operator", False),
                    ]),
                    ("Which signal function is used to create a read-only derived value from other signals?", [
                        ("computed()", True),
                        ("signal()", False),
                        ("effect()", False),
                        ("toObservable()", False),
                    ]),
                    ("What happens if you attempt to mutate a signal directly inside an effect() by default?", [
                        ("Angular throws an error unless allowSignalWrites is explicitly enabled.", True),
                        ("The browser restarts the page.", False),
                        ("The signal becomes immutable permanently.", False),
                        ("The application silently ignores the mutation.", False),
                    ]),
                    ("Which utility converts an RxJS Observable stream into a Signal with an initial value?", [
                        ("toSignal(observable$, { initialValue })", True),
                        ("asSignal(observable$)", False),
                        ("fromObservable(observable$)", False),
                        ("observable$.toSignal()", False),
                    ]),
                    ("What return type can an Angular functional CanActivateFn guard provide to redirect users?", [
                        ("A UrlTree representing the destination route.", True),
                        ("A plain string URL only.", False),
                        ("A number status code 302.", False),
                        ("A DOM Event object.", False),
                    ]),
                    ("Why should heavy operations be avoided in pure computed() signals?", [
                        ("Because computed signals should remain pure, idempotent, and side-effect free.", True),
                        ("Because computed signals run in a separate web worker.", False),
                        ("Because computed signals cannot access component properties.", False),
                        ("Because computed signals require async/await.", False),
                    ]),
                    ("What is the primary benefit of signal inputs using input.required<T>()?", [
                        ("Compile-time safety guaranteeing the parent component provides the input.", True),
                        ("They execute HTTP requests automatically.", False),
                        ("They bypass change detection.", False),
                        ("They create two-way form bindings.", False),
                    ]),
                    ("How does non-destructive hydration improve Angular SSR performance?", [
                        ("It attaches event listeners to existing server-rendered DOM nodes without tearing them down.", True),
                        ("It recompiles TypeScript on the client from scratch.", False),
                        ("It downloads images in WebP format only.", False),
                        ("It caches everything in sessionStorage.", False),
                    ]),
                ],
            },
            {
                "course_title": "FastAPI: High-Performance Python Microservices",
                "title": "FastAPI Microservices Architecture Assessment",
                "description": "Assess your skills in Async Python, Pydantic v2, SQLAlchemy async, and JWT auth.",
                "questions": [
                    ("What Python ASGI framework standard does FastAPI run on top of?", [
                        ("Starlette and Uvicorn", True),
                        ("Django Channels only", False),
                        ("Flask WSGI", False),
                        ("Tornado Server", False),
                    ]),
                    ("Why is Pydantic v2 significantly faster than Pydantic v1?", [
                        ("Its core validation logic is written in Rust.", True),
                        ("It disables type checking in production.", False),
                        ("It uses CPython bytecode optimizations.", False),
                        ("It relies on SQLite internally.", False),
                    ]),
                    ("Which FastAPI decorator parameter specifies the successful HTTP response status code?", [
                        ("status_code=status.HTTP_201_CREATED", True),
                        ("response_code=201", False),
                        ("http_status=201", False),
                        ("return_code=201", False),
                    ]),
                    ("How is dependency injection declared in FastAPI route handlers?", [
                        ("Using Depends() in the parameter default value.", True),
                        ("Using @inject decorator above the function.", False),
                        ("Through global app.dependencies list only.", False),
                        ("By importing dependencies in every function body.", False),
                    ]),
                    ("Which database driver provides asynchronous PostgreSQL connections for SQLAlchemy 2.0?", [
                        ("asyncpg", True),
                        ("psycopg2-binary (synchronous)", False),
                        ("sqlite3", False),
                        ("mysqlclient", False),
                    ]),
                    ("What is the purpose of Alembic in a FastAPI / SQLAlchemy project?", [
                        ("To handle database schema versioning and migrations.", True),
                        ("To serve static assets.", False),
                        ("To act as an API gateway.", False),
                        ("To encrypt passwords.", False),
                    ]),
                    ("Which algorithm is standard for signing JSON Web Tokens in FastAPI security?", [
                        ("HS256 or RS256", True),
                        ("MD5", False),
                        ("SHA1", False),
                        ("Plain Base64 encoding", False),
                    ]),
                    ("How are background tasks executed within a standard FastAPI endpoint?", [
                        ("By accepting BackgroundTasks parameter and calling tasks.add_task().", True),
                        ("By spawning an OS thread manually.", False),
                        ("By calling time.sleep() asynchronously.", False),
                        ("By triggering an OS cron job.", False),
                    ]),
                    ("What HTTP status code does FastAPI return automatically on request validation failure?", [
                        ("422 Unprocessable Entity", True),
                        ("400 Bad Request", False),
                        ("500 Internal Server Error", False),
                        ("404 Not Found", False),
                    ]),
                    ("Why should database connection pools have bounded maximum overflow limits?", [
                        ("To prevent exhausting PostgreSQL server connection limits under heavy traffic.", True),
                        ("To make SQL queries execute faster.", False),
                        ("To encrypt queries automatically.", False),
                        ("To enable Redis caching.", False),
                    ]),
                ],
            },
            {
                "course_title": "Full-Stack TypeScript with Node.js & PostgreSQL",
                "title": "TypeScript Full-Stack Engineering Assessment",
                "description": "Evaluation of TypeScript backend patterns, Prisma ORM, and Express architecture.",
                "questions": [
                    ("What is the primary benefit of enabling strict: true in tsconfig.json?", [
                        ("It enables strict null checks and enforces exhaustive type checking.", True),
                        ("It speeds up npm install.", False),
                        ("It minifies JavaScript code.", False),
                        ("It bundles CSS modules.", False),
                    ]),
                    ("How does Prisma prevent SQL injection in database queries?", [
                        ("By using parameterized queries at the driver level for all inputs.", True),
                        ("By removing quotation marks from strings.", False),
                        ("By running in an isolated Docker container.", False),
                        ("By only allowing read queries.", False),
                    ]),
                    ("What is the recommended pattern for decoupling business logic from Express routing?", [
                        ("The Controller-Service-Repository layered architecture.", True),
                        ("Putting all queries directly inside the route callback.", False),
                        ("Using global window variables.", False),
                        ("Writing raw SQL inside EJS templates.", False),
                    ]),
                    ("How should asynchronous errors in Express 4 middleware be passed to the error handler?", [
                        ("By passing the error to next(err) or using an async wrapper.", True),
                        ("By calling process.exit(1).", False),
                        ("By ignoring them.", False),
                        ("By returning res.status(200).", False),
                    ]),
                    ("What is the purpose of an interactive transaction in Prisma ($transaction)?", [
                        ("To execute a sequence of dependent queries atomically within a single database transaction.", True),
                        ("To run queries across different databases concurrently.", False),
                        ("To format JSON responses.", False),
                        ("To log database queries to the console.", False),
                    ]),
                    ("Why should JWT access tokens be stored in HttpOnly cookies rather than localStorage?", [
                        ("To mitigate Cross-Site Scripting (XSS) token theft vulnerabilities.", True),
                        ("Because cookies are larger than localStorage.", False),
                        ("Because localStorage does not support strings.", False),
                        ("To allow CSS styling of tokens.", False),
                    ]),
                    ("What is the function of the Helmet middleware in an Express application?", [
                        ("It sets secure HTTP response headers (HSTS, CSP, X-Frame-Options).", True),
                        ("It compresses images.", False),
                        ("It validates incoming email addresses.", False),
                        ("It restarts Node.js when it crashes.", False),
                    ]),
                    ("How does PgBouncer improve PostgreSQL scaling with Node.js microservices?", [
                        ("It pools and multiplexes database connections efficiently across short-lived processes.", True),
                        ("It rewrites SQL queries to GraphQL.", False),
                        ("It serves as a Redis replacement.", False),
                        ("It translates TypeScript to SQL.", False),
                    ]),
                    ("Which HTTP status code is most appropriate when a valid JWT token lacks permission for a resource?", [
                        ("403 Forbidden", True),
                        ("401 Unauthorized", False),
                        ("404 Not Found", False),
                        ("500 Internal Server Error", False),
                    ]),
                    ("What does Jest's beforeAll hook commonly do in integration testing?", [
                        ("Initializes test database connections or runs ephemeral container migrations.", True),
                        ("Installs npm packages.", False),
                        ("Sends an email report.", False),
                        ("Deletes the source code.", False),
                    ]),
                ],
            },
            {
                "course_title": "Applied Machine Learning & Deep Learning with Python",
                "title": "Machine Learning & Deep Learning Assessment",
                "description": "Examine your knowledge of feature engineering, evaluation metrics, and PyTorch models.",
                "questions": [
                    ("What critical issue does fitting a scaler only on training data prevent?", [
                        ("Data leakage from the test set into the model training pipeline.", True),
                        ("Underfitting on simple datasets.", False),
                        ("Division by zero in NumPy.", False),
                        ("GPU memory exhaustion.", False),
                    ]),
                    ("Which regularization technique performs feature selection by shrinking coefficients to zero?", [
                        ("L1 Regularization (Lasso)", True),
                        ("L2 Regularization (Ridge)", False),
                        ("Early stopping only", False),
                        ("Batch Normalization", False),
                    ]),
                    ("Why is accuracy an ineffective evaluation metric on highly imbalanced classification datasets?", [
                        ("A trivial model predicting only the majority class can yield high accuracy with zero predictive utility.", True),
                        ("Accuracy cannot be computed with float numbers.", False),
                        ("Accuracy is only defined for binary classification.", False),
                        ("Accuracy causes gradient explosion.", False),
                    ]),
                    ("In PyTorch, what does calling loss.backward() accomplish?", [
                        ("Computes the gradients of the loss with respect to all leaf tensors with requires_grad=True.", True),
                        ("Updates the model weights directly.", False),
                        ("Resets gradients to zero.", False),
                        ("Saves the model to disk.", False),
                    ]),
                    ("Why must optimizer.zero_grad() be called before loss.backward() in a training loop?", [
                        ("Because PyTorch accumulates gradients by default on subsequent backward passes.", True),
                        ("To clear the GPU cache.", False),
                        ("To reload model weights.", False),
                        ("To reset the learning rate.", False),
                    ]),
                    ("What is the primary role of a Convolutional layer in Computer Vision?", [
                        ("Extracting translation-invariant local spatial features from multi-channel input tensors.", True),
                        ("Sorting image pixels in ascending order.", False),
                        ("Converting images into text captions.", False),
                        ("Compressing JPEG files.", False),
                    ]),
                    ("How does Transfer Learning accelerate training on custom computer vision tasks?", [
                        ("By reusing pre-trained feature extraction weights learned from large datasets like ImageNet.", True),
                        ("By skipping gradient computation entirely.", False),
                        ("By doubling the learning rate.", False),
                        ("By reducing the image resolution to 1x1.", False),
                    ]),
                    ("What is the advantage of exporting a trained PyTorch model to the ONNX format?", [
                        ("It enables optimized hardware inference across diverse runtime engines (ONNX Runtime, TensorRT).", True),
                        ("It converts Python code into C++ source code.", False),
                        ("It automatically trains the model further.", False),
                        ("It removes the need for test datasets.", False),
                    ]),
                    ("What type of distribution shift occurs when P(X) changes over time while P(Y|X) remains constant?", [
                        ("Covariate shift (Feature drift)", True),
                        ("Concept drift", False),
                        ("Prior probability shift", False),
                        ("Label corruption", False),
                    ]),
                    ("Which metric is specifically suitable for tuning probability thresholds in imbalanced fraud detection?", [
                        ("Precision-Recall AUC (PR-AUC)", True),
                        ("R-squared", False),
                        ("Mean Absolute Error", False),
                        ("Huber loss", False),
                    ]),
                ],
            },
            {
                "course_title": "Generative AI & LLM Engineering with LangChain",
                "title": "Generative AI & LLM Engineering Assessment",
                "description": "Assess your understanding of embeddings, RAG architectures, and autonomous agent loops.",
                "questions": [
                    ("What mathematical operation powers semantic vector similarity search in embedding spaces?", [
                        ("Cosine similarity or Dot product between normalized vector embeddings.", True),
                        ("Levenshtein edit distance.", False),
                        ("Regex pattern matching.", False),
                        ("MD5 checksum hashing.", False),
                    ]),
                    ("What is the primary goal of Retrieval-Augmented Generation (RAG)?", [
                        ("To augment LLM prompts with authoritative external context to reduce hallucinations and ground answers.", True),
                        ("To train LLMs from scratch without GPUs.", False),
                        ("To compress vector databases into ZIP files.", False),
                        ("To translate Python into SQL.", False),
                    ]),
                    ("In advanced RAG, what is the role of a Cross-Encoder Reranker?", [
                        ("Scores query-document pairs jointly to accurately re-rank candidate chunks retrieved by fast vector search.", True),
                        ("Generates synthetic test questions.", False),
                        ("Encrypts database queries.", False),
                        ("Translates documents into multiple languages.", False),
                    ]),
                    ("How does the ReAct (Reason-Action) pattern enable LLM agents to solve complex tasks?", [
                        ("By alternating between verbal reasoning steps and tool execution observations until an answer is reached.", True),
                        ("By running multiple models in parallel without communication.", False),
                        ("By fine-tuning model weights after every user prompt.", False),
                        ("By caching outputs in browser cookies.", False),
                    ]),
                    ("What technique is used to enforce strict JSON schemas on modern LLM outputs?", [
                        ("Constrained decoding and structured output schemas via Pydantic.", True),
                        ("Hoping the model obeys the system prompt.", False),
                        ("Running regex search on raw strings.", False),
                        ("Disabling temperature completely.", False),
                    ]),
                    ("What does the RAG Triad measure when evaluating generative systems?", [
                        ("Faithfulness, Answer Relevance, and Context Precision.", True),
                        ("GPU temperature, CPU load, and network ping.", False),
                        ("Code length, line count, and indentation.", False),
                        ("Model file size, token price, and context window.", False),
                    ]),
                    ("Why is semantic caching beneficial in high-volume LLM production APIs?", [
                        ("It returns cached answers for semantically equivalent queries, cutting latency and API token costs.", True),
                        ("It increases the context window size.", False),
                        ("It trains the model offline.", False),
                        ("It prevents model quantization.", False),
                    ]),
                    ("What is Chunk Overlap in text splitting pipelines?", [
                        ("A shared token window between adjacent chunks to maintain context continuity across boundaries.", True),
                        ("A bug in recursive text splitters.", False),
                        ("Duplicate entries in a vector store.", False),
                        ("A technique to compress images.", False),
                    ]),
                    ("How do LLM Guardrails improve application safety?", [
                        ("By actively intercepting prompt injection attacks, jailbreaks, and filtering toxic or PII content.", True),
                        ("By blocking all API requests.", False),
                        ("By limiting models to 10 tokens.", False),
                        ("By replacing words with asterisks.", False),
                    ]),
                    ("What is the primary advantage of LangGraph over simple sequential chains?", [
                        ("It supports stateful cyclical graphs, multi-agent coordination, and human-in-the-loop branching.", True),
                        ("It compiles Python to Rust.", False),
                        ("It eliminates the need for an LLM provider.", False),
                        ("It runs without an internet connection.", False),
                    ]),
                ],
            },
            {
                "course_title": "Kubernetes for Production: Container Orchestration",
                "title": "Kubernetes Production Engineering Assessment",
                "description": "Evaluation of cluster components, pod lifecycles, Ingress, Helm, and zero-downtime rollouts.",
                "questions": [
                    ("Which Kubernetes control plane component acts as the consistent, high-availability key-value datastore?", [
                        ("etcd", True),
                        ("kube-scheduler", False),
                        ("kube-proxy", False),
                        ("kubelet", False),
                    ]),
                    ("What is the difference between a Pod's resource request and its resource limit?", [
                        ("Request is used by kube-scheduler for placement; Limit is the maximum enforced boundary by cgroups.", True),
                        ("Request is in gigabytes; Limit is in megabytes.", False),
                        ("Request applies to memory only; Limit applies to CPU only.", False),
                        ("Request is optional; Limit is required by Linux.", False),
                    ]),
                    ("Which Kubernetes Service type creates an internal cluster IP accessible only inside the cluster?", [
                        ("ClusterIP", True),
                        ("NodePort", False),
                        ("LoadBalancer", False),
                        ("ExternalName", False),
                    ]),
                    ("How does an Ingress Controller route incoming HTTP traffic to backend Services?", [
                        ("By inspecting HTTP request host headers and URL paths according to Ingress resource rules.", True),
                        ("By opening a direct SSH tunnel to every container.", False),
                        ("By modifying the client's /etc/hosts file.", False),
                        ("By running iptables rules on client machines.", False),
                    ]),
                    ("What happens to an application pod when its livenessProbe fails continuously?", [
                        ("The kubelet restarts the container according to its restartPolicy.", True),
                        ("The pod is permanently deleted from etcd.", False),
                        ("Traffic is paused without restarting the container.", False),
                        ("The worker node reboots.", False),
                    ]),
                    ("Why are StatefulSets used instead of Deployments for clustered databases?", [
                        ("They provide unique, stable network identifiers and dedicated, persistent storage per replica.", True),
                        ("They run faster than Deployments.", False),
                        ("They do not require container images.", False),
                        ("They bypass Kubernetes networking.", False),
                    ]),
                    ("In Helm, what is the role of the values.yaml file?", [
                        ("It defines default configuration parameters that can be overridden per deployment environment.", True),
                        ("It contains compiled binary code.", False),
                        ("It stores the Dockerfile.", False),
                        ("It runs database migrations.", False),
                    ]),
                    ("What is the core principle of GitOps deployment with tools like ArgoCD?", [
                        ("Git is the single source of truth, and cluster state is continuously reconciled to match Git.", True),
                        ("Developers SSH into production servers to run kubectl apply.", False),
                        ("Docker containers are built directly on production nodes.", False),
                        ("Kubernetes manifests are generated manually.", False),
                    ]),
                    ("How does the Horizontal Pod Autoscaler (HPA) scale workloads?", [
                        ("It dynamically adjusts the number of pod replicas based on observed CPU/memory utilization or custom metrics.", True),
                        ("It increases the physical RAM on worker nodes.", False),
                        ("It restarts slow containers.", False),
                        ("It optimizes SQL queries.", False),
                    ]),
                    ("What security principle should guide the creation of Kubernetes RBAC ServiceAccounts?", [
                        ("Principle of Least Privilege: grant only the minimum necessary verbs and API resources required.", True),
                        ("Give all pods cluster-admin permissions for simplicity.", False),
                        ("Disable authentication in internal namespaces.", False),
                        ("Share a single token among all pods.", False),
                    ]),
                ],
            },
            {
                "course_title": "System Design: Scalable & Distributed Architectures",
                "title": "Distributed System Design & Architecture Assessment",
                "description": "Examine mastery of high-availability, caching, sharding, consensus, and fault tolerance.",
                "questions": [
                    ("According to the CAP Theorem, what must a distributed system sacrifice when a network partition occurs?", [
                        ("Either Consistency (C) or Availability (A).", True),
                        ("Partition Tolerance (P).", False),
                        ("Data Durability.", False),
                        ("Network Bandwidth.", False),
                    ]),
                    ("In the Cache-Aside pattern, what happens when a read request misses the cache?", [
                        ("The application fetches data from the database, writes it to the cache, and returns it to the client.", True),
                        ("The database writes directly to the client browser.", False),
                        ("An HTTP 404 error is returned.", False),
                        ("The cache automatically queries the database asynchronously.", False),
                    ]),
                    ("How does Consistent Hashing minimize data movement when a new storage node is added to a cluster?", [
                        ("Only K/N keys need to be remapped on average, rather than nearly all keys under simple modulo hashing.", True),
                        ("It copies the entire database to the new node.", False),
                        ("It freezes all incoming write operations.", False),
                        ("It re-indexes all tables synchronously.", False),
                    ]),
                    ("What is the primary difference between a message broker (RabbitMQ) and an event log (Apache Kafka)?", [
                        ("Kafka maintains an immutable, partitioned, append-only log that multiple consumers can read independently at their own pace.", True),
                        ("RabbitMQ can only handle 10 messages per minute.", False),
                        ("Kafka does not support persistence.", False),
                        ("RabbitMQ requires ZooKeeper.", False),
                    ]),
                    ("Why is Idempotency essential when designing distributed API consumers?", [
                        ("To ensure that processing duplicate messages (due to at-least-once delivery) produces the exact same outcome.", True),
                        ("To speed up network transit times.", False),
                        ("To encrypt payload bodies.", False),
                        ("To avoid using database transactions.", False),
                    ]),
                    ("How does the Saga pattern manage distributed transactions across multiple microservices?", [
                        ("Through a sequence of local transactions with compensating transactions executed if any step fails.", True),
                        ("By holding global two-phase locks across all microservice databases.", False),
                        ("By storing all data in a single shared PostgreSQL instance.", False),
                        ("By ignoring database rollbacks.", False),
                    ]),
                    ("What is the primary function of a Circuit Breaker (e.g. Netflix Hystrix pattern)?", [
                        ("To fail fast and prevent cascading system failures when downstream dependent services become degraded.", True),
                        ("To compress network packets.", False),
                        ("To restart servers when CPU spikes.", False),
                        ("To balance load across database replicas.", False),
                    ]),
                    ("In a distributed consensus protocol like Raft, how is split-brain avoided during network partitions?", [
                        ("A leader can only commit log entries if acknowledged by a strict majority (quorum) of nodes.", True),
                        ("By electing the node with the highest IP address.", False),
                        ("By shutting down all worker nodes.", False),
                        ("By relying on NTP timestamps.", False),
                    ]),
                    ("What is the purpose of a Dead Letter Queue (DLQ) in an asynchronous messaging architecture?", [
                        ("To isolate poison-pill messages that fail processing repeatedly for inspection without blocking the queue.", True),
                        ("To store successfully processed messages forever.", False),
                        ("To route messages to spam folders.", False),
                        ("To delete failed messages immediately.", False),
                    ]),
                    ("How does Database Sharding differ from Read-Replica Replication?", [
                        ("Sharding partitions distinct subsets of data across multiple database servers to scale both writes and storage.", True),
                        ("Sharding only handles read traffic.", False),
                        ("Replication splits tables by column.", False),
                        ("Sharding is only supported by NoSQL databases.", False),
                    ]),
                ],
            },
        ]

        created_quizzes = {}
        for q in Quiz.objects.all():
            created_quizzes[q.course_id] = q

        for q_info in quizzes_manifest:
            course = courses[q_info["course_title"]]
            quiz, _ = Quiz.objects.get_or_create(
                course=course,
                title=q_info["title"],
                defaults={
                    "description": q_info["description"],
                    "passing_score": 70,
                    "is_published": True,
                },
            )
            created_quizzes[course.id] = quiz

            for q_idx, (q_text, options_list) in enumerate(q_info["questions"], start=1):
                question, _ = Question.objects.get_or_create(
                    quiz=quiz,
                    text=q_text,
                    defaults={"order": q_idx},
                )

                for opt_text, is_correct in options_list:
                    Option.objects.get_or_create(
                        question=question,
                        text=opt_text,
                        defaults={"is_correct": is_correct},
                    )

        # ------------------------------------------------------------------
        # 4. ENROLLMENTS (Realistic Learner Personas -> Target 34 total)
        # ------------------------------------------------------------------
        self.stdout.write("Seeding enrollments and progress scenarios...")

        # Map course objects by short keys
        c1 = Course.objects.get(id=1)  # Django Fundamentals
        c2 = Course.objects.get(id=2)  # Python Backend Development
        c3 = Course.objects.get(id=3)  # Cloud Computing with AWS
        c4 = courses["Modern Angular & Enterprise Architecture"]
        c5 = courses["FastAPI: High-Performance Python Microservices"]
        c6 = courses["Full-Stack TypeScript with Node.js & PostgreSQL"]
        c7 = courses["Applied Machine Learning & Deep Learning with Python"]
        c8 = courses["Generative AI & LLM Engineering with LangChain"]
        c9 = courses["Kubernetes for Production: Container Orchestration"]
        c10 = courses["System Design: Scalable & Distributed Architectures"]

        enrollments_plan = [
            # High-performing: Maya Patel (4 courses)
            ("maya_patel", [c4, c5, c6, c7]),
            # High-performing: Liam Chen (4 courses)
            ("liam_chen", [c5, c6, c9, c10]),
            # Active: David Kim (4 courses)
            ("david_kim", [c4, c7, c8, c9]),
            # Active: Jordan Lee (4 courses)
            ("jordan_lee", [c4, c5, c8, c10]),
            # Mixed: Sofia Martinez (4 courses)
            ("sofia_martinez", [c5, c6, c7, c10]),
            # Beginner: Alex Rivera (3 courses)
            ("alex_rivera", [c4, c5, c6]),
            # Beginner: Chloe Dupont (3 courses)
            ("chloe_dupont", [c7, c8, c9]),
            # Preserved student: teststudent (currently in c1, c2, c3 -> add c4, c9)
            ("teststudent", [c4, c9]),
        ]

        enrolled_set = set()
        for e in Enrollment.objects.all():
            enrolled_set.add((e.student_id, e.course_id))

        new_notifications_count = 0

        for username, course_list in enrollments_plan:
            student = users[username]
            for c_idx, crs in enumerate(course_list):
                if (student.id, crs.id) not in enrolled_set:
                    Enrollment.objects.get_or_create(
                        student=student,
                        course=crs,
                    )
                    enrolled_set.add((student.id, crs.id))

                # Deterministic unread: latest 2 courses for student are unread (or latest 1 for teststudent)
                threshold = 1 if username == "teststudent" else 2
                is_read_flag = (c_idx < len(course_list) - threshold)
                notif, created = Notification.objects.get_or_create(
                    recipient=student,
                    notification_type="ENROLLMENT",
                    title="Course Enrollment Successful",
                    message=f"You have successfully enrolled in {crs.title}.",
                    defaults={"is_read": is_read_flag},
                )
                if not created and notif.is_read != is_read_flag:
                    notif.is_read = is_read_flag
                    notif.save(update_fields=["is_read"])

        # ------------------------------------------------------------------
        # 5. LESSON PROGRESS (Persona-Specific Completion)
        # ------------------------------------------------------------------
        # Helper to get lessons for a course
        def get_lessons(crs):
            return list(Lesson.objects.filter(module__course=crs).order_by("module__order", "order"))

        progress_plan = [
            # 100% completion courses (Eligibility for Certificates):
            ("maya_patel", c4, 1.0),
            ("maya_patel", c5, 1.0),
            ("maya_patel", c6, 1.0),
            ("liam_chen", c9, 1.0),
            ("liam_chen", c10, 1.0),
            ("liam_chen", c5, 1.0),
            ("david_kim", c7, 1.0),
            ("david_kim", c8, 1.0),
            ("jordan_lee", c4, 1.0),
            ("jordan_lee", c8, 1.0),
            ("sofia_martinez", c6, 1.0),
            ("teststudent", c4, 1.0),
            ("teststudent", c9, 1.0),

            # Partial progress courses:
            ("maya_patel", c7, 0.40),
            ("liam_chen", c6, 0.45),
            ("david_kim", c4, 0.35),
            ("david_kim", c9, 0.30),
            ("jordan_lee", c5, 0.40),
            ("jordan_lee", c10, 0.30),
            ("sofia_martinez", c5, 0.35),
            ("sofia_martinez", c7, 0.15),
            ("alex_rivera", c4, 0.20),
            ("alex_rivera", c5, 0.15),
            ("alex_rivera", c6, 0.10),
            ("chloe_dupont", c7, 0.20),
            ("chloe_dupont", c8, 0.15),
            ("chloe_dupont", c9, 0.10),
        ]

        now = timezone.now()
        for username, crs, completion_ratio in progress_plan:
            student = users[username]
            crs_lessons = get_lessons(crs)
            total = len(crs_lessons)
            num_to_complete = int(total * completion_ratio)

            for idx, lsn in enumerate(crs_lessons):
                is_comp = idx < num_to_complete
                comp_time = now - timedelta(days=(total - idx)) if is_comp else None
                lp, created = LessonProgress.objects.get_or_create(
                    student=student,
                    lesson=lsn,
                    defaults={
                        "is_completed": is_comp,
                        "completed_at": comp_time,
                    },
                )
                if is_comp and not lp.is_completed:
                    lp.is_completed = True
                    lp.completed_at = comp_time
                    lp.save(update_fields=["is_completed", "completed_at"])

        # ------------------------------------------------------------------
        # 6. QUIZ ATTEMPTS & ANSWERS (Consistent Scores & Passes)
        # ------------------------------------------------------------------
        self.stdout.write("Seeding quiz attempts and student answers...")

        # List of (student_username, course, score, is_passed)
        quiz_attempts_plan = [
            # Passed attempts for 100% completed courses (Cert requirements)
            ("maya_patel", c4, 9, True),
            ("maya_patel", c5, 10, True),
            ("maya_patel", c6, 9, True),
            ("liam_chen", c9, 9, True),
            ("liam_chen", c10, 10, True),
            ("liam_chen", c5, 9, True),
            ("david_kim", c7, 8, True),
            ("david_kim", c8, 8, True),
            ("jordan_lee", c4, 8, True),
            ("jordan_lee", c8, 9, True),
            ("sofia_martinez", c6, 8, True),
            ("teststudent", c4, 9, True),
            ("teststudent", c9, 9, True),

            # Passed retakes after initial fails
            ("david_kim", c4, 8, True),
            ("jordan_lee", c5, 8, True),
            ("liam_chen", c6, 8, True),

            # Initial Failed Attempts (Learner realism)
            ("david_kim", c4, 5, False),
            ("jordan_lee", c5, 6, False),
            ("liam_chen", c6, 6, False),
            ("sofia_martinez", c5, 5, False),
            ("alex_rivera", c4, 4, False),
            ("alex_rivera", c5, 4, False),
            ("chloe_dupont", c7, 5, False),
            ("chloe_dupont", c8, 4, False),

            # Additional attempts by active learners
            ("maya_patel", c7, 7, True),
            ("david_kim", c9, 7, True),
            ("jordan_lee", c10, 7, True),
            ("sofia_martinez", c7, 5, False),
            ("alex_rivera", c6, 4, False),
            ("chloe_dupont", c9, 5, False),
            ("david_kim", c7, 6, False),
            ("jordan_lee", c4, 6, False),
            ("maya_patel", c4, 8, True),
            ("liam_chen", c9, 8, True),
            ("teststudent", c4, 7, True),
        ]

        for username, crs, score, is_passed in quiz_attempts_plan:
            student = users[username]
            quiz = created_quizzes.get(crs.id)
            if not quiz:
                continue

            questions = list(quiz.questions.all().order_by("order"))
            total_q = len(questions)
            if total_q == 0:
                continue

            pct = round((score / total_q) * 100)
            submitted_time = now - timedelta(days=(12 - score))

            attempt = QuizAttempt.objects.filter(
                student=student,
                quiz=quiz,
                score=score,
                is_passed=is_passed,
            ).first()

            if not attempt:
                attempt = QuizAttempt.objects.create(
                    student=student,
                    quiz=quiz,
                    score=score,
                    total_questions=total_q,
                    percentage=pct,
                    is_passed=is_passed,
                )
                # Ensure correct submitted_at
                QuizAttempt.objects.filter(id=attempt.id).update(submitted_at=submitted_time)

                # Create Answer records for each question
                answers_to_create = []
                for q_idx, q in enumerate(questions):
                    options = list(q.options.all())
                    correct_opt = next((o for o in options if o.is_correct), options[0])
                    incorrect_opts = [o for o in options if not o.is_correct]

                    # If question index < score, select correct option, else incorrect
                    selected = correct_opt if q_idx < score else (incorrect_opts[0] if incorrect_opts else correct_opt)
                    answers_to_create.append(Answer(attempt=attempt, question=q, selected_option=selected))

                Answer.objects.bulk_create(answers_to_create)

            # Quiz Notification (Idempotent)
            status_text = "PASSED" if is_passed else "FAILED"
            Notification.objects.get_or_create(
                recipient=student,
                notification_type="QUIZ",
                title=f"Quiz {status_text}: {quiz.title}",
                message=f"You scored {score}/{total_q} ({pct}%). Status: {status_text} (Passing score: {quiz.passing_score}%).",
                defaults={"is_read": (score >= 7)},
            )

        # ------------------------------------------------------------------
        # 7. CERTIFICATES (Strict Eligibility Enforcement)
        # ------------------------------------------------------------------
        self.stdout.write("Seeding verified certificates...")

        # Eligible certificate candidates (13 certificates):
        cert_candidates = [
            ("maya_patel", c4),
            ("maya_patel", c5),
            ("maya_patel", c6),
            ("liam_chen", c9),
            ("liam_chen", c10),
            ("liam_chen", c5),
            ("david_kim", c7),
            ("david_kim", c8),
            ("jordan_lee", c4),
            ("jordan_lee", c8),
            ("sofia_martinez", c6),
            ("teststudent", c4),
            ("teststudent", c9),
        ]

        for username, crs in cert_candidates:
            student = users[username]
            # Verify 100% lessons are completed
            total_lessons = Lesson.objects.filter(module__course=crs).count()
            completed_count = LessonProgress.objects.filter(
                student=student,
                lesson__module__course=crs,
                is_completed=True,
            ).count()

            # Verify quiz passed
            quiz = created_quizzes.get(crs.id)
            has_passed = QuizAttempt.objects.filter(
                student=student,
                quiz=quiz,
                is_passed=True,
            ).exists()

            if total_lessons > 0 and completed_count == total_lessons and has_passed:
                cert, created = Certificate.objects.get_or_create(
                    student=student,
                    course=crs,
                    defaults={
                        "certificate_id": uuid.uuid4(),
                        "completion_percentage": 100,
                    },
                )
                # 6 unread cert notifications (recent achievements)
                is_unread_cert = (username, crs.id) in [
                    ("maya_patel", c6.id),
                    ("liam_chen", c5.id),
                    ("david_kim", c8.id),
                    ("jordan_lee", c8.id),
                    ("sofia_martinez", c6.id),
                    ("teststudent", c9.id),
                ]
                is_read_flag = not is_unread_cert
                notif, n_created = Notification.objects.get_or_create(
                    recipient=student,
                    notification_type="CERTIFICATE",
                    title="Certificate Earned!",
                    message=f"Congratulations! You have earned your certificate for {crs.title}.",
                    defaults={"is_read": is_read_flag},
                )
                if not n_created and notif.is_read != is_read_flag:
                    notif.is_read = is_read_flag
                    notif.save(update_fields=["is_read"])

        # ------------------------------------------------------------------
        # 8. REVIEWS & REVIEW NOTIFICATIONS (Target 20 new -> 22 total)
        # ------------------------------------------------------------------
        self.stdout.write("Seeding course reviews...")

        reviews_plan = [
            # 5-star reviews (11 reviews = 55%)
            ("maya_patel", c4, 5, "Outstanding course! The deep dive into Angular Signals and standalone architecture completely transformed how I structure frontend enterprise applications."),
            ("maya_patel", c5, 5, "Best FastAPI course available. The Pydantic v2 deep dive and async SQLAlchemy connection pooling lessons were production gold."),
            ("liam_chen", c9, 5, "Exceptionally well-structured Kubernetes curriculum. The Helm chart templates and ArgoCD GitOps lessons were directly applicable to our team's cluster."),
            ("liam_chen", c10, 5, "Comprehensive and rigorous system design guide. The breakdown of Consistent Hashing and Kafka partitioned logs cleared up years of confusion."),
            ("david_kim", c8, 5, "Fascinating journey through Generative AI and LangChain. The RAG reranker and semantic caching patterns saved our startup thousands in API costs."),
            ("teststudent", c4, 5, "Super clear explanations and high-quality code snippets. Really enjoyed testing the new reactive inputs and computed signals!"),
            ("teststudent", c9, 5, "Production-grade Kubernetes lessons! Setting up Ingress with TLS and debugging pod failures gave me real hands-on confidence."),
            ("liam_chen", c5, 5, "FastAPI microservices built the right way. Clean layered architecture and zero-downtime deployment patterns."),
            ("jordan_lee", c8, 5, "The LangGraph agentic workflow section is top tier. Practical, modern, and zero fluff."),
            ("maya_patel", c6, 5, "Full-stack TypeScript perfection. Prisma interactive transactions and strict typing on the backend solved so many subtle bugs for me."),
            ("david_kim", c7, 5, "Hands-on PyTorch with practical feature engineering. Loved the section on avoiding data leakage in Scikit-Learn pipelines."),

            # 4-star reviews (7 reviews = 35%)
            ("david_kim", c9, 4, "Great hands-on Kubernetes drills. Deploying ingress controllers and debugging crashlooping pods gave me a much deeper grasp of cluster operations."),
            ("jordan_lee", c4, 4, "Very solid Angular course. The modern control flow syntax and NgRx Signal Store examples made complex state management easy to digest."),
            ("sofia_martinez", c6, 4, "Extremely thorough TypeScript and Node.js walkthrough. The Prisma ORM integration and Jest API test suites were super clear."),
            ("jordan_lee", c10, 4, "Strong distributed systems fundamentals. The consensus protocols and distributed caching patterns were explained with exceptional clarity."),
            ("sofia_martinez", c5, 4, "Great introduction to asynchronous Python web services. The authentication and OAuth2 token refresh flow was easy to implement."),
            ("alex_rivera", c4, 4, "As someone coming from React, this made modern Angular feel intuitive and powerful. Great pace and structured modules."),
            ("chloe_dupont", c7, 4, "Clear explanations of gradient boosting and feature encoding. The visual graphs helped me understand ROC curves much better."),

            # 3-star reviews (2 reviews = 10%)
            ("alex_rivera", c5, 3, "Comprehensive content, but async SQLAlchemy and Alembic migrations move quite fast for beginner Python developers. Rewatching helped."),
            ("chloe_dupont", c9, 3, "Very in-depth Kubernetes concepts, though setting up the local multi-node cluster took some troubleshooting on Windows."),
        ]

        for rev_idx, (username, crs, rating, comment) in enumerate(reviews_plan):
            student = users[username]
            review, created = Review.objects.get_or_create(
                student=student,
                course=crs,
                defaults={
                    "rating": rating,
                    "comment": comment,
                },
            )
            # 8 unread review notifications across instructors (realistic active inbox)
            is_unread_review = rev_idx in [0, 2, 4, 6, 8, 10, 11, 13]
            is_read_flag = not is_unread_review
            notif, n_created = Notification.objects.get_or_create(
                recipient=crs.instructor,
                notification_type="REVIEW",
                title="New Course Review",
                message=f"{student.username} reviewed your course {crs.title} with a rating of {rating}/5.",
                defaults={"is_read": is_read_flag},
            )
            if not n_created and notif.is_read != is_read_flag:
                notif.is_read = is_read_flag
                notif.save(update_fields=["is_read"])

        # ------------------------------------------------------------------
        # 9. SYSTEM NOTIFICATIONS
        # ------------------------------------------------------------------
        self.stdout.write("Seeding welcome and platform notifications...")
        for u in [users["alex_rivera"], users["david_kim"], users["maya_patel"], users["chloe_dupont"]]:
            # alex_rivera and chloe_dupont (beginners) have unread welcome notifications
            is_read_flag = u.username in ["david_kim", "maya_patel"]
            notif, created = Notification.objects.get_or_create(
                recipient=u,
                notification_type="SYSTEM",
                title="Welcome to SkillSphere!",
                message="Welcome to SkillSphere! Discover structured courses, test your skills with quizzes, and earn verified certificates.",
                defaults={"is_read": is_read_flag},
            )
            if not created and notif.is_read != is_read_flag:
                notif.is_read = is_read_flag
                notif.save(update_fields=["is_read"])

        self.stdout.write(self.style.SUCCESS("SkillSphere demo data seeded successfully!"))
