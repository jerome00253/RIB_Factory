# Stage 1: Build Frontend
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend

# Copy frontend dependency definitions
COPY frontend/package*.json ./

# Install dependencies (clean install)
RUN npm ci

# Copy frontend source code
COPY frontend/ .

# Build static files (output: "export" -> /out)
RUN npm run build


# Stage 2: Backend Runtime
FROM python:3.10-bookworm
WORKDIR /app

# Install system dependencies needed for Doctr and OpenCV
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    git \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ .

# Copy built frontend assets from Stage 1 to where FastAPI expects them
COPY --from=frontend-builder /app/frontend/out /app/static

# Expose port
EXPOSE 8000

# Run uvicorn (production mode)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
