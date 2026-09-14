# Frontend Dockerfile
# Multi-stage build: 1) Build React app with Vite, 2) Serve static bundle with Nginx

FROM node:20-alpine AS builder
WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source code and build
COPY . .
RUN npm run build

# Production server
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html

# Custom nginx config for client-side routing (React Router)
RUN echo 'server {' \
    '  listen 80;' \
    '  server_name localhost;' \
    '  location / {' \
    '    root /usr/share/nginx/html;' \
    '    index index.html index.htm;' \
    '    try_files $uri $uri/ /index.html;' \
    '  }' \
    '}' > /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
