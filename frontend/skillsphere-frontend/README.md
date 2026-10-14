# SkillSphere Frontend (Angular 20 Standalone SPA)

SkillSphere is a modern, responsive Single Page Application (SPA) built with **Angular 20**, featuring standalone components, Signals-based state, fine-grained Role-Based Access Control (RBAC), and an embedded AI Learning Assistant.

In production, the frontend is compiled into optimized static browser bundles and served via a hardened **Nginx Alpine** container that reverse-proxies `/api/` traffic directly to the Django backend.

---

## Table of Contents

- [Overview and Feature Areas](#overview-and-feature-areas)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
  - [1. Navigate and Install Dependencies](#1-navigate-and-install-dependencies)
  - [2. Start the Development Server](#2-start-the-development-server)
- [Environment Configuration and Relative `/api` Routing](#environment-configuration-and-relative-api-routing)
- [Authentication and JWT Integration](#authentication-and-jwt-integration)
- [Route Architecture and Feature Modules](#route-architecture-and-feature-modules)
- [Running Unit Tests](#running-unit-tests)
- [Production Build](#production-build)
- [Docker and Nginx Configuration](#docker-and-nginx-configuration)
- [Troubleshooting Common Setup Issues](#troubleshooting-common-setup-issues)
- [Security Notes](#security-notes)

---

## Overview and Feature Areas

The frontend provides specialized, high-performance user experiences for Students, Instructors, and Administrators:

1. **Authentication & Onboarding (`features/auth`)**:
   - Secure login and registration flows with real-time field validation.
   - Role-aware redirection upon authentication.
2. **Student Dashboard (`features/dashboard`)**:
   - Active course cards with completion percentages and quick-resume actions.
   - Recent quiz scores and earned certificate previews.
3. **Course Catalog & Detail (`features/courses`)**:
   - Searchable, category-filtered course catalog.
   - Comprehensive course details, syllabus accordion, instructor profiles, and enrollment actions.
4. **Learning Player (`features/learning`)**:
   - Immersive course player with video playback, rich lesson Markdown, lesson completion toggles, and adjacent lesson navigation.
   - Embedded **AI Learning Assistant** panel with suggested prompts ("Summarize this lesson", "Practical example", "Best practices & pitfalls").
5. **Quizzes & Assessments (`features/quizzes`)**:
   - Interactive quiz player with timed attempts, randomized questions, multiple-choice options, instant scoring, attempt reviews, and student attempt histories.
6. **Certificates (`features/certificates`)**:
   - Automated certificate issuance upon 100% course completion and passing quiz score.
   - Printable certificate detail view with certificate IDs, student credentials, and public verification URLs (`/certificates/verify/:certificateId`).
7. **Reviews & Ratings (`features/reviews`)**:
   - Course rating summaries (1–5 stars) and student feedback reviews.
8. **Notifications (`features/notifications`)**:
   - In-app notification center for enrollment updates, quiz evaluations, certificates, and system messages.
9. **Instructor Studio (`features/instructor`)**:
   - Instructor management dashboard with enrolled student metrics.
   - Course authoring studio for creating modules, drafting lesson content, and configuring course quizzes (with student attempt tracking supported via backend APIs).

---

## Technology Stack

- **Framework:** Angular 20.3.0 (Standalone Components Architecture)
- **CLI:** Angular CLI 20.3.32 (`@angular/build:application`)
- **Language:** TypeScript 5.9.2
- **Reactive Library:** RxJS 7.8.0
- **Styles:** Scoped SCSS with custom design tokens, fluid responsive layouts, and CSS Grid/Flexbox
- **Testing Engine:** Karma 6.4.4 & Jasmine 5.9.0 (karma-jasmine 5.1.0, Headless Chrome)
- **Production Server:** Nginx Alpine (Reverse Proxy & SPA Static Host)
- **Container Build:** Node 20 Alpine Multi-Stage Dockerfile

---

## Prerequisites

Ensure your system has the required development tooling installed:

- **Node.js:** Node 20 LTS (verify with `node -v`)
- **Package Manager:** npm 10+ (verify with `npm -v`)
- **Angular CLI (optional global):** `@angular/cli@20`
- **Docker:** Required for running the containerized Nginx frontend

---

## Local Development Setup

### 1. Navigate and Install Dependencies

Open your terminal or PowerShell and navigate to the frontend workspace:

```powershell
cd D:\Downloads\skillsphere\frontend\skillsphere-frontend
```

Install the pinned dependencies using `package-lock.json`:

```powershell
npm ci
```

*(Alternatively, use `npm install` if working in offline development mode).*

### 2. Start the Development Server

Start the Angular local development server:

```powershell
npm start
```

*(or run `ng serve` directly).*

Once compiled, navigate to `http://localhost:4200/` in your browser.

- By default, the development server proxies or targets the local Django backend running at `http://127.0.0.1:8000/api`.
- Live reloading is enabled; changes to TypeScript, HTML, or SCSS files automatically trigger incremental compilation.

---

## Environment Configuration and Relative `/api` Routing

SkillSphere separates development and production API routing via Angular environment configuration:

### Development Environment (`src/environments/environment.ts`)

```typescript
export const environment = {
  production: false,
  apiUrl: 'http://127.0.0.1:8000/api'
};
```

Used when running `ng serve` locally on the host, sending cross-origin requests directly to the Django development server on port 8000.

### Production Environment (`src/environments/environment.prod.ts`)

```typescript
export const environment = {
  production: true,
  apiUrl: '/api'
};
```

When building for production (`ng build --configuration production`), Angular swaps in `environment.prod.ts`.

**Why Relative `/api` Routing?**
- Decouples client-side JavaScript bundles from hardcoded domains or ports (`localhost`, `127.0.0.1:8000`, or external URLs).
- In Docker, the browser communicates directly with Nginx on port 4200. Nginx intercepts `/api/` requests and proxies them internally to `http://backend:8000/api/`.
- Eliminates Cross-Origin Resource Sharing (CORS) preflight overhead in production since frontend assets and `/api/` share the exact same origin.

---

## Authentication and JWT Integration

SkillSphere uses stateless **JWT Bearer Authentication** managed by core services and interceptors:

### 1. Token Management (`AuthService`)
- On login (`POST /api/auth/token/`), tokens are stored securely in browser `localStorage`:
  - `skillsphere_access_token` (expires in 1 hour)
  - `skillsphere_refresh_token` (expires in 1 day)
- Current user profile state is persisted in `localStorage` (`skillsphere_current_user`) and queried via `getCurrentUser()` and `getCurrentUserSnapshot()`.

### 2. Automatic Header Injection (`authInterceptor`)
- Automatically intercepts all outbound HTTP requests made through `HttpClient`.
- Injects the `Authorization: Bearer <access_token>` header for protected endpoints.
- Skips token injection for public authentication routes (`/auth/token/`, `/auth/register/`).

### 3. Transparent Token Refresh Lifecycle
- If an API call fails with HTTP `401 Unauthorized`, `authInterceptor` catches the error.
- It attempts a silent token refresh via `POST /api/auth/token/refresh/` using the stored refresh token.
- If refresh succeeds, the new access token is saved and the original failed HTTP request is automatically retried with the fresh token.
- If refresh fails, `authService.logout()` is called, clearing stored tokens and redirecting the user to `/login`.

### 4. Route Protection (`authGuard` & `roleGuard`)
- `authGuard`: Blocks unauthenticated users and redirects to `/login`.
- `roleGuard`: Enforces role-based permissions on routes (e.g., student dashboard requires `['STUDENT', 'ADMIN']`, instructor suite requires `['INSTRUCTOR']`).

---

## Route Architecture and Feature Modules

Routes are configured in `src/app/app.routes.ts`:

| Route Path | Component | Guard / Access | Description |
| :--- | :--- | :--- | :--- |
| `/login` | `LoginComponent` | Public | User authentication |
| `/register` | `RegisterComponent` | Public | Student/Instructor account creation |
| `/certificates/verify/:certificateId` | `CertificateVerifyComponent` | Public | Public certificate verification by UUID |
| `/dashboard` | `DashboardComponent` | `authGuard`, Student/Admin | Student learning overview |
| `/courses` | `CourseListComponent` | `authGuard` | Published courses catalog |
| `/courses/:id` | `CourseDetailComponent` | `authGuard` | Syllabus and enrollment view |
| `/learning` | `MyLearningComponent` | `authGuard`, Student/Admin | Enrolled courses list |
| `/learning/lesson/:lessonId` | `LessonDetailComponent` | `authGuard`, Student/Admin | Course player with embedded AI tutor |
| `/quizzes` | `QuizListComponent` | `authGuard` | Available quizzes |
| `/quizzes/:id` | `QuizAttemptComponent` | `authGuard`, Student/Admin | Interactive quiz taking |
| `/quizzes/:id/result` | `QuizResultComponent` | `authGuard`, Student/Admin | Quiz score summary |
| `/quizzes/history` | `QuizHistoryComponent` | `authGuard`, Student/Admin | Past attempt history |
| `/quizzes/attempts/:id` | `QuizAttemptDetailComponent` | `authGuard`, Student/Admin | Granular answer review |
| `/certificates` | `CertificateListComponent` | `authGuard`, Student/Admin | Earned certificates |
| `/certificates/:id` | `CertificateDetailComponent` | `authGuard`, Student/Admin | Credential detail view |
| `/reviews` | `ReviewsComponent` | `authGuard` | Platform reviews |
| `/notifications` | `NotificationsComponent` | `authGuard` | Notification inbox |
| `/instructor/dashboard` | `InstructorDashboardComponent` | `authGuard`, Instructor | Instructor metrics & courses |
| `/instructor/courses/create`| `InstructorCourseManagementComponent` | `authGuard`, Instructor | Course creation studio |
| `/instructor/courses/:id` | `InstructorCourseManagementComponent` | `authGuard`, Instructor | Curriculum editor |

---

## Running Unit Tests

SkillSphere frontend features **81 comprehensive unit tests** covering components, services, interceptors, route guards, and instructor workflows (expanded from the historical 66-test baseline).

### Run Tests in Headless Mode (CI / Verification)

Execute Karma tests with headless Chrome without browser windows:

```powershell
npm test -- --watch=false --browsers=ChromeHeadless
```

Expected output:
```text
Chrome Headless 155.0.0.0 (Windows 10): Executed 81 of 81 SUCCESS
TOTAL: 81 SUCCESS
```
*(Historical baseline: 66 tests).*

### Run Tests in Interactive Watch Mode

For active component development:

```powershell
npm test
```

---

## Production Build

To compile the Angular application for production:

```powershell
npm run build
```

*(or `ng build --configuration production`).*

### Build Artifacts
- **Output Directory:** `dist/skillsphere-frontend/browser`
- **Output Files:**
  - `main-<hash>.js` (~626 kB raw, ~130 kB gzipped transfer)
  - `polyfills-<hash>.js` (~34 kB raw, ~11 kB gzipped)
  - `styles-<hash>.css` (~27 kB raw, ~4 kB gzipped)
  - `index.html` & `favicon.ico`

*(Note: Budget warnings for initial chunk ~88 kB over 600 kB are non-blocking informational notices).*

---

## Docker and Nginx Configuration

The frontend is containerized using a multi-stage Docker build and served through Nginx.

### Multi-Stage Dockerfile Highlights (`Dockerfile`)

```dockerfile
# Stage 1: Build Angular production bundle
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build -- --configuration production

# Stage 2: Serve via Nginx Alpine
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist/skillsphere-frontend/browser /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Nginx Server Configuration (`nginx.conf`)

- **SPA Routing Fallback:**
  ```nginx
  location / {
      try_files $uri $uri/ /index.html;
  }
  ```
  Ensures browser refreshes on routes like `/courses/4` or `/learning/lesson/9` resolve to `index.html` without returning 404 errors.

- **API Reverse Proxy:**
  ```nginx
  location /api/ {
      proxy_pass http://backend:8000/api/;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto $scheme;
  }
  ```
  Proxies all `/api/` traffic directly to the Django backend container (`skillsphere-backend`) over the internal Docker network.

### Build and Run with Docker Compose

To build the frontend container:

```powershell
docker compose build frontend
```

To run the containerized frontend:

```powershell
docker compose up -d frontend
```

The containerized application will be available at:
`http://localhost:4200`

---

## Troubleshooting Common Setup Issues

### 1. Port 4200 Already in Use

- **Cause:** Another host process or background `ng serve` is running on port 4200.
- **Fix:**
  ```powershell
  netstat -ano | findstr :4200
  Stop-Process -Id <PID> -Force
  ```

### 2. Angular Build Errors (`node_modules` Mismatch)

- **Cause:** Corrupted node modules or lockfile discrepancy.
- **Fix:**
  ```powershell
  Remove-Item -Recurse -Force node_modules, .angular
  npm ci
  ```

### 3. API Calls Return 404 in Docker Container

- **Cause:** `environment.prod.ts` is incorrectly pointing to an absolute host address instead of relative `/api`.
- **Fix:** Verify `src/environments/environment.prod.ts` contains `apiUrl: '/api'`.

### 4. Direct Refresh on Routes Returns 404 (Nginx)

- **Cause:** Missing SPA fallback rule.
- **Fix:** Verify `nginx.conf` contains `try_files $uri $uri/ /index.html;` in `location /`.

---

## Security Notes

1. **No Client-Side Secrets:** Never store private API keys, backend master secrets, or administrative credentials in Angular code or environment files. Everything shipped in the Angular bundle is readable by users.
2. **Token Security:** JWT tokens are stored in `localStorage`. Cross-Site Scripting (XSS) protections are enforced through Angular's built-in contextual encoding and sanitization.
3. **Defense in Depth:** While client-side route guards (`authGuard`, `roleGuard`) provide clean user navigation, real security authorization is strictly enforced on every request by the Django REST Framework backend.
4. **Isolated Public Endpoints:** Public verification routes like `/certificates/verify/:certificateId` do not expose private student records or account data.
