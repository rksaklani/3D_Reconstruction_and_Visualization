FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/
COPY ai/ ./ai/
COPY configs/ ./configs/

# Expose port
EXPOSE 8000

# Run backend server
CMD ["uvicorn", "backend.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
