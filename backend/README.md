# SkillSphere Backend (Django REST Framework)

SkillSphere is a role-based Learning Management System (LMS) and Intelligent Course Platform. The backend is built with **Django** and **Django REST Framework (DRF)**, providing a modular API architecture, PostgreSQL database persistence, JWT authentication, role-based access control (RBAC), and an integrated AI Learning Assistant.

---

## Table of Contents

- [Overview and Responsibilities](#overview-and-responsibilities)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Local Development Setup (Windows / PowerShell)](#local-development-setup-windows--powershell)
  - [1. Clone and Navigate](#1-clone-and-navigate)
  - [2. Create and Activate Virtual Environment](#2-create-and-activate-virtual-environment)
  - [3. Install Dependencies](#3-install-dependencies)
  - [4. Configure Environment Variables](#4-configure-environment-variables)
- [Database Configuration: Local vs Docker](#database-configuration-local-vs-docker)
- [Database Migrations](#database-migrations)
- [Superuser Creation](#superuser-creation)
- [Running the Development Server](#running-the-development-server)
- [Authentication and JWT Architecture](#authentication-and-jwt-architecture)
- [API Endpoints Overview](#api-endpoints-overview)
- [AI Learning Assistant](#ai-learning-assistant)
- [Running Backend Tests](#running-backend-tests)
- [Docker Production Container](#docker-production-container)
- [Useful Management Commands](#useful-management-commands)
- [Troubleshooting Common Setup Issues](#troubleshooting-common-setup-issues)
- [Security Notes](#security-notes)

---

## Overview and Responsibilities

The backend manages the platform's core data models, business logic, security policies, and AI orchestration:

- **Accounts & RBAC**: Custom user model supporting three distinct roles (`STUDENT`, `INSTRUCTOR`, `ADMIN`) with dedicated permission classes.
- **Courses & Curriculum**: Structured hierarchy of Courses, Modules, and Lessons with rich Markdown and video URL support.
- **Enrollments**: Student enrollment workflows with status tracking and duplicate prevention.
- **Learning Progress**: Granular lesson completion tracking and automatic course progress recalculation.
- **Quizzes & Assessments**: Course-level quizzes with multiple-choice questions, automated scoring, passing thresholds, and attempt history.
- **Certificates**: Automated certificate generation upon verified 100% course completion and passing quiz score, with unique UUIDs for public verification.
- **Reviews & Ratings**: Student reviews and star ratings (1–5) with aggregated course rating calculation.
- **Notifications**: Automated in-app notifications for enrollment, course completion, quiz results, and announcements.
- **AI Learning Assistant**: Context-grounded educational tutor supporting lesson-based Q&A, prompt injection defenses, and configurable model providers.

---

## Technology Stack

- **Language:** Python 3.12
- **Framework:** Django 6.1
- **API Engine:** Django REST Framework (DRF) 3.18.0
- **Database Driver:** `psycopg` / `psycopg-binary` 3.3.4 (PostgreSQL 17)
- **Authentication:** `djangorestframework-simplejwt` 5.5.1 & `PyJWT` 2.13.0
- **CORS Handling:** `django-cors-headers` 4.9.0
- **Production WSGI Server:** `gunicorn` 23.0.0
- **Database:** PostgreSQL 17

---

## Prerequisites

Ensure the following tools are installed on your host system:

- **Python 3.12+** (check with `python --version`)
- **Git**
- **Docker & Docker Compose** (for running PostgreSQL or the full stack)
- **PowerShell** (Windows) or bash (Linux/macOS)

---

## Local Development Setup (Windows / PowerShell)

### 1. Clone and Navigate

Open PowerShell and navigate to the `backend` directory:

```powershell
cd D:\Downloads\skillsphere\backend
```

### 2. Create and Activate Virtual Environment

Create a clean Python 3.12 virtual environment:

```powershell
python -m venv venv
```

Activate the virtual environment:

```powershell
.\venv\Scripts\Activate.ps1
```

> **Note for PowerShell execution policy:** If script execution is restricted on Windows, allow signed local scripts:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 3. Install Dependencies

Install the pinned requirements:

```powershell
pip install -r requirements.txt
```

Verify installed packages:

```powershell
pip list
```

### 4. Configure Environment Variables

The project reads configuration from a `.env` file located in the workspace root or in the `backend/` directory.

Copy the environment template from the repository root:

```powershell
Copy-Item ..\.env.example .env
```

Edit `.env` to configure your settings (see [Database Configuration](#database-configuration-local-vs-docker) below).

---

## Database Configuration: Local vs Docker

The Django settings (`backend/config/settings.py`) load database connection settings from environment variables:

| Variable | Local Host Default | Docker Container Value | Description |
| :--- | :--- | :--- | :--- |
| `DB_NAME` | `skillsphere` | `skillsphere` | PostgreSQL database name |
| `DB_USER` | `skillsphere_user` | `skillsphere_user` | PostgreSQL database user |
| `DB_PASSWORD` | *(from `.env`)* | *(from `.env`)* | PostgreSQL user password |
| `DB_HOST` | `localhost` | `postgres` | Host address of PostgreSQL |
| `DB_PORT` | `5436` | `5432` | Port mapped to PostgreSQL |
| `CONN_MAX_AGE` | `0` | `0` | Database connection lifetime in seconds (0 = close per request) |

### Running PostgreSQL in Docker for Local Host Development

To start the PostgreSQL container using Docker Compose from the project root:

```powershell
docker compose up -d postgres
```

The container maps PostgreSQL container port `5432` to host port `5436`. Therefore, when running Django locally outside Docker, keep `DB_HOST=localhost` and `DB_PORT=5436` in your local `.env`.

When running Django inside the Docker Compose network, Compose automatically sets `DB_HOST=postgres` and `DB_PORT=5432`.

---

## Database Migrations

Apply existing database migrations to set up or update the database schema:

```powershell
python manage.py migrate
```

To create new migrations after intentionally modifying application models:

```powershell
python manage.py makemigrations
```

> **Important Migration Safety Rule:** `makemigrations` should only be executed when model definitions are intentionally altered. All generated migration files must be carefully inspected and reviewed before applying them with `migrate`. Never run migrations blindly on existing populated databases or during read-only verification passes.

To inspect current migration status across all installed apps:

```powershell
python manage.py showmigrations
```


---

## Superuser Creation

Create an administrator account for Django Admin access (`/admin/`):

```powershell
python manage.py createsuperuser
```

Follow the interactive prompts to specify a username, email, and password.

---

## Running the Development Server

Start the Django development server on port 8000:

```powershell
python manage.py runserver 127.0.0.1:8000
```

The backend is now accessible at:
- **API Base:** `http://127.0.0.1:8000/api/`
- **Django Admin:** `http://127.0.0.1:8000/admin/`

---

## Authentication and JWT Architecture

SkillSphere uses **JWT (JSON Web Token)** Bearer authentication via `djangorestframework-simplejwt`.

### Token Lifetimes

- **Access Token:** 1 hour
- **Refresh Token:** 1 day

### Authentication Flow

1. **Obtain Tokens:**
   `POST /api/auth/token/`
   ```json
   {
     "username": "teststudent",
     "password": "your-password"
   }
   ```
   **Response (200 OK):**
   ```json
   {
     "access": "eyJhbGciOi...",
     "refresh": "eyJhbGciOi..."
   }
   ```

2. **Access Protected Endpoints:**
   Pass the access token in the `Authorization` header:
   ```http
   Authorization: Bearer <access_token>
   ```

3. **Refresh Expired Access Token:**
   `POST /api/auth/token/refresh/`
   ```json
   {
     "refresh": "eyJhbGciOi..."
   }
   ```

4. **Current User Profile:**
   `GET /api/auth/me/` with Bearer token returns:
   ```json
   {
     "id": 2,
     "username": "teststudent",
     "email": "teststudent@skillsphere.com",
     "role": "STUDENT"
   }
   ```

---

## API Endpoints Overview

All application API endpoints are mounted under `/api/`:

### 1. Authentication & Role Testing (`accounts`)

| Method | Endpoint | Description | Permission |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register/` | Register a new user | AllowAny |
| `POST` | `/api/auth/token/` | Obtain JWT access and refresh tokens | AllowAny |
| `POST` | `/api/auth/token/refresh/` | Refresh JWT access token | AllowAny |
| `GET` | `/api/auth/me/` | Current authenticated user profile | IsAuthenticated |
| `GET` | `/api/student-test/` | Student role verification test | IsAuthenticated (Student) |
| `GET` | `/api/instructor-test/` | Instructor role verification test | IsAuthenticated (Instructor) |
| `GET` | `/api/admin-test/` | Admin role verification test | IsAuthenticated (Admin) |

### 2. Courses & Curriculum (`courses`)

| Method | Endpoint | Description | Permission |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/courses/` | List published courses (or instructor's own) | IsAuthenticated |
| `POST` | `/api/courses/` | Create a new course | Instructor / Admin |
| `GET` | `/api/courses/<id>/` | Course detail with modules & lessons | IsAuthenticated |
| `PUT`, `PATCH`, `DELETE` | `/api/courses/<id>/` | Update or delete course | Owner Instructor / Admin |
| `GET`, `POST` | `/api/courses/modules/` | List or create modules | IsAuthenticated / Instructor |
| `GET`, `PUT`, `DELETE` | `/api/courses/modules/<id>/` | Module detail, update, delete | Owner Instructor / Admin |
| `GET`, `POST` | `/api/courses/lessons/` | List or create lessons | IsAuthenticated / Instructor |
| `GET`, `PUT`, `DELETE` | `/api/courses/lessons/<id>/` | Lesson detail, update, delete | Owner Instructor / Admin |

### 3. Enrollments (`enrollments`)

| Method | Endpoint | Description | Permission |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/enrollments/` | List student's enrollments | IsAuthenticated (Student) |
| `POST` | `/api/enrollments/` | Enroll in a course (`course_id`) | IsAuthenticated (Student) |

### 4. Learning & Progress (`learning`)

| Method | Endpoint | Description | Permission |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/learning/progress/` | List lesson completion progress | IsAuthenticated (Student) |
| `POST` | `/api/learning/progress/` | Mark lesson complete / update progress | IsAuthenticated (Student) |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/api/learning/progress/<id>/` | Retrieve, update, or delete progress | Progress Owner (Student) / Admin |

### 5. Quizzes & Assessments (`quizzes`)

| Method | Endpoint | Description | Permission |
| :--- | :--- | :--- | :--- |
| `GET`, `POST` | `/api/quizzes/` | List or create quizzes | IsAuthenticated / Instructor |
| `GET`, `PUT`, `DELETE` | `/api/quizzes/<id>/` | Quiz detail, update, delete | IsAuthenticated / Instructor |
| `GET` | `/api/quizzes/student/<id>/` | Retrieve quiz for student taking | Enrolled Student |
| `POST` | `/api/quizzes/student/<id>/submit/` | Submit quiz answers for scoring | Enrolled Student |
| `GET` | `/api/quizzes/attempts/` | List student's quiz attempts | IsAuthenticated (Student) |
| `GET` | `/api/quizzes/attempts/<id>/` | Detailed attempt score and review | Attempt Owner |
| `GET` | `/api/quizzes/instructor/attempts/` | View attempts on instructor's quizzes | Instructor / Admin |
| `GET`, `POST` | `/api/quizzes/questions/` | List or create quiz questions | Instructor / Admin |
| `GET`, `PUT`, `DELETE` | `/api/quizzes/questions/<id>/` | Question detail, update, delete | Owner Instructor / Admin |
| `GET`, `POST` | `/api/quizzes/options/` | List or create question answer options | Instructor / Admin |
| `GET`, `PUT`, `DELETE` | `/api/quizzes/options/<id>/` | Option detail, update, delete | Owner Instructor / Admin |

### 6. Certificates (`certificates`)

| Method | Endpoint | Description | Permission |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/certificates/` | Generate certificate upon course completion | Enrolled Student |
| `GET` | `/api/certificates/my/` | List student's earned certificates | IsAuthenticated (Student) |
| `GET` | `/api/certificates/<id>/` | Certificate detail and credentials | Certificate Owner |
| `GET` | `/api/certificates/verify/<uuid>/` | Public certificate verification | AllowAny |

### 7. Reviews & Ratings (`reviews`)

| Method | Endpoint | Description | Permission |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/reviews/?course=<id>` | List reviews for a course | IsAuthenticated |
| `POST` | `/api/reviews/` | Submit review and rating (1–5) | Enrolled Student |
| `GET`, `PUT`, `DELETE` | `/api/reviews/<id>/` | Retrieve, update, or delete review | Review Owner / Admin |
| `GET` | `/api/reviews/course/<course_id>/rating/` | Aggregated rating metrics | IsAuthenticated |

### 8. Notifications (`notifications`)

| Method | Endpoint | Description | Permission |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/notifications/` | List user's notifications | IsAuthenticated |
| `PATCH` | `/api/notifications/read-all/` | Mark all notifications as read | IsAuthenticated |
| `GET` | `/api/notifications/<id>/` | Retrieve specific notification | Notification Owner |
| `PATCH` | `/api/notifications/<id>/read/` | Mark specific notification as read | Notification Owner |

### 9. AI Learning Assistant (`ai_assistant`)

| Method | Endpoint | Description | Permission |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/ai/ask/` | Ask educational questions about a lesson | Enrolled Student / Instructor |

---

## AI Learning Assistant

The AI Learning Assistant provides contextual explanations, summaries, and pedagogical guidance based on the current lesson material.

### Configuration Settings

| Setting | Default | Description |
| :--- | :--- | :--- |
| `AI_PROVIDER` | `gemini` | Model provider (`gemini` or `mock`) |
| `AI_API_KEY` | `""` | API key for Google Gemini |
| `AI_MODEL` | `gemini-1.5-flash` | Gemini model identifier |
| `AI_REQUEST_TIMEOUT` | `30` | Timeout in seconds for external AI calls |
| `AI_RATE_LIMIT` | `30/minute` | Per-user rate throttle on `/api/ai/ask/` |
| `AI_MAX_LESSON_CHARS` | `15000` | Maximum lesson content budget passed to context |
| `AI_MAX_MESSAGE_CHARS` | `2000` | Maximum student query length |
| `AI_MAX_RESPONSE_CHARS`| `4000` | Maximum response length returned |

### Provider Behavior & Error Handling

- **Gemini (`AI_PROVIDER=gemini`):** Communicates with Google Generative Language API via standard library `urllib`. If `AI_API_KEY` is not set or empty, the server returns a sanitized `503 Service Unavailable` (`{"error": "AI assistant is currently not configured on the server."}`).
- **Mock (`AI_PROVIDER=mock`):** Used for automated tests and offline development without making external network calls.
- **Security & Prompt Injection Defenses:** The service strictly separates untrusted lesson reference material (`<lesson_context>`) and user input (`<student_question>`) from system tutor directives (`<course_context>`). Directives prevent disclosing system prompts, server credentials, or secrets.

---

## Running Backend Tests

The backend test suite contains **168 comprehensive tests** covering authentication, permissions, production settings hardening, Nginx and static asset delivery, application health endpoints, automated CI pipelines, production Compose security hardening, deployment readiness specifications, courses, enrollments, learning progress, quizzes, certificates, reviews, notifications, AI boundaries, rate throttling, and error handling.

To run all tests locally:

```powershell
python manage.py test
```

To run tests with verbosity:

```powershell
python manage.py test -v 2
```

To run tests for a specific application:

```powershell
python manage.py test accounts
python manage.py test courses
python manage.py test ai_assistant
```

To run tests inside the Docker container:

```powershell
docker exec skillsphere-backend python manage.py test
```

---

## Docker Production Container

The backend is containerized using **Python 3.12 slim** and runs under **Gunicorn** in production mode.

### Dockerfile Highlights

- **Base Image:** `python:3.12-slim`
- **Workdir:** `/app`
- **Port:** `8000`
- **Entrypoint:**
  ```dockerfile
  CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
  ```

### Build and Run with Docker Compose

Build the backend image:

```powershell
docker compose build backend
```

Start backend and PostgreSQL containers:

```powershell
docker compose up -d backend
```

View live container logs:

```powershell
docker logs -f skillsphere-backend
```

Stop backend containers without deleting volumes:

```powershell
docker compose stop backend
```

### Local Docker Foundation vs Public Production Deployment

The configuration in `docker-compose.yml` is an engineering-verified **local Docker foundation**:
- **PostgreSQL Port 5436:** Published to the host so developers can inspect and query the database with GUI tools (e.g., DBeaver, pgAdmin) alongside the running container.
- **Backend Port 8000:** Published to the host to allow direct API probing and automated test execution.
- **Nginx Port 4200:** Published to the host as the primary frontend gateway.

For a **public production deployment**, the following hardening steps must be implemented:
1. **Remove Public Ports:** Unpublish ports `5436` and `8000` from the host. Only the reverse proxy (ports 80 and 443) should accept inbound external connections.
2. **HTTPS / TLS Termination:** Secure Nginx with valid TLS certificates (e.g., Let's Encrypt / Certbot).
3. **Secret Enforcement:** Supply a cryptographically strong, random `SECRET_KEY` in environment variables. When `DEBUG=False`, startup will strictly fail if `SECRET_KEY` is empty or matches the development fallback.
4. **Environment Hardening:** Ensure `DEBUG=False` is strictly maintained and restrict `ALLOWED_HOSTS` to the verified domain name.
5. **Trusted Reverse Proxy Header:** Set `SECURE_PROXY_SSL_HEADER=True` when behind a trusted reverse proxy (e.g. Nginx, ALB) that safely controls `X-Forwarded-Proto`. (Trust assumption: only enable if the proxy strips/sets this header).
6. **CSRF Trusted Origins:** Define `CSRF_TRUSTED_ORIGINS` with comma-separated HTTPS origins (e.g. `https://yourdomain.com`). Defaults to localhost in local dev/Docker; defaults to empty in production deployments using public hostnames without localhost. Wildcards (`*`) are disallowed.
7. **Database Connection Lifetime:** Set `CONN_MAX_AGE` (e.g. `60` or `300` seconds) to enable connection reuse across requests under Gunicorn.
8. **HTTPS Security Headers:** Set `SECURE_SSL_REDIRECT=True`, `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`, and configure HSTS headers.
9. **Static Asset Pipeline & Ingress Routing (Stage 22.3):** Static assets are collected via `collectstatic --noinput` into `django_static_volume` (mounted to `/usr/share/nginx/html/static:ro` in Nginx). Nginx handles reverse proxying for `/admin/` and `/api/`, serves static files directly with 30-day immutable caching, and applies cache-busting revalidation for `index.html`.

---

## Useful Management Commands

### Seed Demo Data

SkillSphere includes a deterministic, realistic demo data generator (`courses/management/commands/seed_demo_data.py`).

It seeds realistic courses, modules, lessons, quizzes, questions, options, student enrollments, progress, quiz attempts, certificates, reviews, and notifications:

```powershell
python manage.py seed_demo_data
```

> **Safety Warning:** Do not run `seed_demo_data` during verification passes or on databases where strict baseline counts must remain untouched.

### Collect Static Files

Collects static files to `STATIC_ROOT` (`staticfiles/`):

```powershell
python manage.py collectstatic --noinput
```

### System Configuration Check

Validates Django system configuration and model relations:

```powershell
python manage.py check
```

---

## Troubleshooting Common Setup Issues

### 1. `psycopg.OperationalError: connection to server at "localhost", port 5436 failed`

- **Cause:** PostgreSQL container is not running or port 5436 is not mapped.
- **Fix:** Start the PostgreSQL container with `docker compose up -d postgres` and verify it is healthy with `docker ps`.

### 2. PowerShell Script Execution Error (`Activate.ps1 cannot be loaded`)

- **Cause:** Default Windows PowerShell script execution policy restricts unassigned scripts.
- **Fix:** Execute:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

### 3. Port 8000 Already in Use

- **Cause:** Another process or development server is already bound to port 8000.
- **Fix:** Identify and terminate the conflicting process:
  ```powershell
  netstat -ano | findstr :8000
  Stop-Process -Id <PID> -Force
  ```

### 4. `401 Unauthorized` on API Calls

- **Cause:** Missing or expired JWT access token.
- **Fix:** Obtain a fresh access token via `POST /api/auth/token/` and include it in your HTTP header: `Authorization: Bearer <access_token>`.

### 5. AI Assistant Returns `503 Service Unavailable`

- **Cause:** `AI_PROVIDER` is set to `gemini` but `AI_API_KEY` is empty in `.env`.
- **Fix:** Add a valid Gemini API key to `.env` or set `AI_PROVIDER=mock` for local development.

---

## Security Notes

1. **Never Commit Secrets:** Never commit `.env`, private keys, database passwords, or API keys to version control. Keep `.env` in `.gitignore`.
2. **Production Secret Key:** Always replace the default fallback `SECRET_KEY` with a strong, random 50+ character string generated specifically for production.
3. **Debug Mode:** Always set `DEBUG=False` in production environments.
4. **CORS and Allowed Hosts:** Never use wildcard `*` for `ALLOWED_HOSTS` or `CORS_ALLOWED_ORIGINS` in production.
5. **HTTPS & Cookie Hardening:** When deploying to production with HTTPS, enable `SECURE_SSL_REDIRECT=True`, `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`, and configure HSTS headers.
