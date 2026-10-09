# ============================================================
# Stage 1: Build Angular Production Application
# ============================================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency manifests
COPY package.json package-lock.json ./

# Install dependencies using package-lock.json
RUN npm ci

# Copy application source code
COPY . .

# Build Angular production bundle
RUN npm run build -- --configuration production

# ============================================================
# Stage 2: Serve via Production Nginx Alpine
# ============================================================
FROM nginx:alpine

# Copy Nginx server configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy production build artifacts into Nginx web root
COPY --from=builder /app/dist/skillsphere-frontend/browser /usr/share/nginx/html

# Expose HTTP port
EXPOSE 80

# Run Nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
