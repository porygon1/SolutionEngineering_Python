# Spotify Recommendation Frontend Dockerfile
# Multi-stage build for optimized production deployment

# Stage 1: Build dependencies and application
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Install system dependencies for node-gyp and other native modules
RUN apk add --no-cache \
    python3 \
    make \
    g++ \
    git

# Copy package files
COPY package*.json ./

# Install all dependencies (needed for build process)
RUN --mount=type=cache,target=/root/.npm \
    npm install && \
    npm cache clean --force

# Copy source code
COPY . .

# Build arguments for environment variables
ARG VITE_BACKEND_URL=http://localhost:8000
ARG VITE_API_VERSION=v2
ARG VITE_NODE_ENV=production

# Create environment file with build arguments
RUN echo "VITE_BACKEND_URL=${VITE_BACKEND_URL}" > .env && \
    echo "VITE_API_VERSION=${VITE_API_VERSION}" >> .env && \
    echo "VITE_NODE_ENV=${VITE_NODE_ENV}" >> .env

# Build the application
RUN npm run build

# Stage 2: Production server with nginx
FROM nginx:1.25-alpine AS production

# Install curl for health checks
RUN apk add --no-cache curl

# Remove default nginx website
RUN rm -rf /usr/share/nginx/html/*

# Copy built application from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create nginx user and set permissions
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

# Switch to non-root user
USER nginx

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

# Stage 3: Development server (alternative target)
FROM node:18-alpine AS development

WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    python3 \
    make \
    g++ \
    git

# Copy package files
COPY package*.json ./

# Install all dependencies (including dev dependencies)
RUN npm ci --silent

# Copy source code
COPY . .

# Build arguments for development
ARG VITE_BACKEND_URL=http://localhost:8000
ARG VITE_API_VERSION=v2
ARG VITE_NODE_ENV=development

# Create environment file with build arguments
RUN echo "VITE_BACKEND_URL=${VITE_BACKEND_URL}" > .env && \
    echo "VITE_API_VERSION=${VITE_API_VERSION}" >> .env && \
    echo "VITE_NODE_ENV=${VITE_NODE_ENV}" >> .env

# Expose development port
EXPOSE 5173

# Health check for development
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5173 || exit 1

# Start development server
CMD ["npm", "run", "dev"] 