# SkillSphere — Production Deployment Readiness Plan (Stage 22.7)

This document specifies the verified deployment strategy, hosting comparison, security hardening, disaster recovery, and operational procedures for deploying SkillSphere to a production environment.

---

## 1. Hosting Architecture Comparison

| Dimension | Option A: Low-Cost Self-Managed VPS *(Recommended)* | Option B: Managed PaaS / Cloud Services |
| :--- | :--- | :--- |
| **Target Providers** | **Hetzner Cloud (CPX21)** / **DigitalOcean Droplet** / **Linode** | **Render** / **Railway** / **Fly.io** + Managed DB (Neon/Supabase) |
| **Hardware Specs** | 3 vCPU (AMD/Intel), 4 GB RAM, 80 GB NVMe SSD, 20 TB egress | Managed container instances (1-2 GB RAM each) + Serverless PostgreSQL |
| **Pricing (Est. 2026)** | **€9.50 / month (~$10.50 USD)** (Hetzner) or **$24.00 / month** (DigitalOcean) | **$14.00 – $35.00 / month** total across DB and container compute |
| **Stack Execution** | Single-host orchestration via `docker-compose.prod.yml` | Segmented web service (Django) + Static CDN (Angular) + Managed DB |
| **Data Control** | Complete ownership of persistent volumes and local storage | Automatic backups by provider, but database resides on third-party host |
| **AI Runtime** | Host has capacity to bridge to external LLMs or local Ollama | External AI APIs only (Gemini / OpenAI); local Ollama requires extra GPU VM |
| **Maintenance Burden** | Moderate: requires OS security updates, UFW firewall, Docker daemon monitoring | Very low: provider handles OS updates, certificates, and DB failover |
| **Recommendation** | **Primary Choice:** Matches SkillSphere's unified Compose architecture, lowest cost, zero vendor lock-in | Secondary choice for teams with zero server administration capacity |

---

## 2. Infrastructure Architecture & Ingress Gateway

In production, all public client traffic is channeled exclusively through the Nginx Ingress Gateway on ports `80` and `443`. PostgreSQL and Django backend ports (`5436` and `8000`) are strictly closed to the host and external network.

```
       [ Internet / Client Browsers ]
                     │
          HTTPS (443) / HTTP (80)
                     ▼
  ┌──────────────────────────────────────────────┐
  │         Nginx Ingress (Port 80/443)          │
  │  (frontend container: skillsphere-frontend) │
  │                                              │
  │  • TLS Termination & HSTS Enforcement        │
  │  • Serves Angular SPA (index.html revalidated│
  │  • Serves Content-Hashed Bundles (immutable) │
  │  • Serves Django Admin Static Files (/static)│
  │  • Reverse Proxies /api/ and /admin/         │
  └──────┬────────────────────────────────┬──────┘
         │                                │
         │ HTTP (internal:8000)           │ Read-only volume mount
         ▼                                ▼
  ┌─────────────────────────────┐  ┌────────────────────────────┐
  │    Django Backend (8000)    │  │   django_static_volume     │
  │ (skillsphere-backend-prod)  │  │  (shared static assets)    │
  │  • Non-root user (1000:1000)│  └────────────────────────────┘
  │  • Gunicorn (3 workers)     │
  │  • CONN_MAX_AGE = 300s      │
  │  • DEBUG = False            │
  └──────────────┬──────────────┘
                 │
                 │ TCP (internal:5432)
                 ▼
  ┌─────────────────────────────┐
  │   PostgreSQL 17 Database    │
  │  (skillsphere-postgres-prod)│
  │  • No exposed host ports    │
  │  • Persistent Data Volume:  │
  │    skillsphere_postgres_data│
  └─────────────────────────────┘
```

---

## 3. TLS / HTTPS Termination & Certificate Automation

### 3.1 Domain & DNS Configuration
1. Reserve domain name (e.g., `skillsphere.example.com`).
2. Point DNS `A` record to your server's Public IPv4 address.
3. Point DNS `AAAA` record to your server's Public IPv6 address (if available).
4. Set DNS TTL to `300` seconds (5 minutes) during initial rollout for fast updates.

### 3.2 Two-Phase TLS Provisioning Workflow
To prevent the common Docker TLS failure where Nginx cannot boot on port 443 without certificates, SkillSphere utilizes a reliable two-phase rollout:

#### Phase 1: Domain Verification & Initial Certificate Issuance (HTTP Port 80)
1. Ensure DNS A record points to server IP.
2. Ensure the persistent database volume exists prior to initial launch:
   ```bash
   docker volume create --name skillsphere_skillsphere_postgres_data
   ```
3. Start the production stack on HTTP port 80:
   ```bash
   docker compose -f docker-compose.prod.yml up -d
   ```
4. Acquire certificates using Certbot with webroot verification:
   ```bash
   sudo mkdir -p /var/www/certbot
   sudo certbot certonly --webroot -w /var/www/certbot \
     -d skillsphere.example.com \
     --email admin@example.com --agree-tos --no-eff-email
   ```

#### Phase 2: Activate TLS Listener (HTTPS Port 443)
1. Instantiate the production Nginx configuration from the verified template:
   ```bash
   cp frontend/skillsphere-frontend/nginx.prod.conf.template frontend/skillsphere-frontend/nginx.prod.conf
   sed -i 's/${DOMAIN}/skillsphere.example.com/g' frontend/skillsphere-frontend/nginx.prod.conf
   ```
2. In `docker-compose.prod.yml`, uncomment port 443 and the certificate volume mounts:
   ```yaml
   ports:
     - "80:80"
     - "443:443"
   volumes:
     - django_static_volume:/usr/share/nginx/html/static:ro
     - /etc/letsencrypt:/etc/letsencrypt:ro
     - /var/www/certbot:/var/www/certbot:ro
     - ./frontend/skillsphere-frontend/nginx.prod.conf:/etc/nginx/conf.d/default.conf:ro
   ```
3. Re-launch production services:
   ```bash
   docker compose -f docker-compose.prod.yml up -d --force-recreate frontend
   ```
4. Verify HTTPS ingress and redirect:
   ```bash
   curl -I https://skillsphere.example.com/health
   curl -I http://skillsphere.example.com/ # Returns 301 Moved Permanently to HTTPS
   ```

### 3.3 HTTPS Security Headers & HSTS Enforcement
The production Nginx ingress terminates TLS and enforces HTTP Strict Transport Security:
- `Strict-Transport-Security`: `"max-age=31536000; includeSubDomains; preload"`
- `X-Content-Type-Options`: `"nosniff"`
- `X-Frame-Options`: `"DENY"`
- `Referrer-Policy`: `"strict-origin-when-cross-origin"`

In addition, Django's security middleware reinforces HSTS and cookie security when `SECURE_SSL_REDIRECT=True`:
- `SECURE_HSTS_SECONDS=31536000`
- `SECURE_HSTS_INCLUDE_SUBDOMAINS=True`
- `SECURE_HSTS_PRELOAD=True`

---

## 4. Environment Variables & Production Secrets Inventory

Create an isolated production `.env` file on the deployment server with `chmod 600 .env`:

```bash
# ============================================================
# SKILLSPHERE PRODUCTION ENVIRONMENT CONFIGURATION
# ============================================================

# Secret Generation (generate using: python -c "import secrets; print(secrets.token_urlsafe(50))")
SECRET_KEY=replace_with_a_unique_cryptographically_secure_random_production_secret

# Core Settings
DEBUG=False
ALLOWED_HOSTS=skillsphere.example.com
CORS_ALLOWED_ORIGINS=https://skillsphere.example.com
CSRF_TRUSTED_ORIGINS=https://skillsphere.example.com

# PostgreSQL Credentials
POSTGRES_DB=skillsphere
POSTGRES_USER=skillsphere_prod_user
POSTGRES_PASSWORD=replace_with_a_strong_database_password
CONN_MAX_AGE=300

# Security & Proxy Settings
SECURE_PROXY_SSL_HEADER=True
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# AI Learning Assistant
AI_PROVIDER=gemini
AI_API_KEY=your_production_gemini_api_key
AI_MODEL=gemini-1.5-flash
AI_REQUEST_TIMEOUT=30
AI_RATE_LIMIT=30/minute
```

> 🔒 **Security Notice:** Never commit `.env` files, production database credentials, or API keys to version control.

---

## 5. Database Backup, Restoration, and Disaster Recovery

### 5.1 Automated Database Backup Procedure
Schedule daily automated backups via `cron`:

```bash
#!/bin/bash
# /opt/skillsphere/scripts/backup_db.sh
set -euo pipefail

BACKUP_DIR="/var/backups/skillsphere"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/skillsphere_${TIMESTAMP}.dump"

mkdir -p "${BACKUP_DIR}"

# Export PostgreSQL dump in custom compressed format (-Fc)
docker exec skillsphere-postgres-prod pg_dump \
  -U skillsphere_prod_user \
  -d skillsphere \
  -Fc > "${BACKUP_FILE}"

chmod 600 "${BACKUP_FILE}"

# Retain backups for 14 days locally
find "${BACKUP_DIR}" -name "skillsphere_*.dump" -type f -mtime +14 -delete

echo "[$(date)] Backup completed: ${BACKUP_FILE}"
```

### 5.2 Database Restoration Procedure
In the event of database recovery or server migration:

```bash
# 1. Stop backend service to prevent write conflicts:
docker compose -f docker-compose.prod.yml stop backend

# 2. Restore PostgreSQL dump into database container:
docker exec -i skillsphere-postgres-prod pg_restore \
  -U skillsphere_prod_user \
  -d skillsphere \
  --clean \
  --if-exists < /var/backups/skillsphere/skillsphere_YYYYMMDD_HHMMSS.dump

# 3. Restart backend service:
docker compose -f docker-compose.prod.yml start backend

# 4. Verify system health probe:
curl -f http://localhost:8000/api/health/
```

---

## 6. Zero-Downtime Deployment & Safe Rollback

### 6.1 Executing a Production Release
```bash
# 1. Pull latest verified commits from origin:
git pull origin main

# 2. Build production containers and assemble static assets:
docker compose -f docker-compose.prod.yml build

# 3. Apply any pending database schema migrations:
docker compose -f docker-compose.prod.yml run --rm backend python manage.py migrate --noinput

# 4. Re-launch production services with rolling replacement:
docker compose -f docker-compose.prod.yml up -d --remove-orphans

# 5. Verify health probes:
curl -f https://skillsphere.example.com/api/health/
```

### 6.2 Emergency Rollback Procedure
If a regression or critical fault occurs post-deployment:

```bash
# 1. Check out previous stable git commit:
git checkout <previous_stable_commit_hash>

# 2. Rebuild and restart production containers immediately:
docker compose -f docker-compose.prod.yml up -d --build

# 3. If a database migration must be rolled back:
docker compose -f docker-compose.prod.yml run --rm backend python manage.py migrate <app_name> <previous_migration_name>

# 4. Verify health probe recovery:
curl -f https://skillsphere.example.com/api/health/
```

---

## 7. Operational Monitoring & Diagnostics

- **Container Status & Uptime:** `docker compose -f docker-compose.prod.yml ps`
- **Application Health Probe:** `curl -i http://localhost/health`
- **Backend Application Logs:** `docker logs -f --tail=100 skillsphere-backend-prod`
- **Nginx Ingress Access & Error Logs:** `docker logs -f --tail=100 skillsphere-frontend-prod`
- **PostgreSQL Database Logs:** `docker logs -f --tail=100 skillsphere-postgres-prod`
