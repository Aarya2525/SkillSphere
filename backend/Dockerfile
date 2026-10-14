FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application source
COPY . /app/

# Ensure entrypoint script has executable permissions
RUN chmod +x /app/entrypoint.sh

# Collect static assets into /app/staticfiles at build time
RUN python manage.py collectstatic --noinput

# Create non-privileged application user and grant directory permissions (Stage 22.6)
RUN groupadd -r -g 1000 skillsphere && \
    useradd -r -u 1000 -g skillsphere -d /app -s /sbin/nologin skillsphere && \
    mkdir -p /app/staticfiles && \
    chown -R skillsphere:skillsphere /app

# Expose backend port
EXPOSE 8000

# Set entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]

# Healthcheck probe (Stage 22.4)
HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/ || exit 1

# Run with Gunicorn in production mode
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
