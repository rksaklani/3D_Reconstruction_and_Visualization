FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

WORKDIR /app

# Install Python
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend/requirements.txt .

# Install PyTorch with CUDA support
RUN pip3 install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Install other dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy AI code
COPY ai/ ./ai/
COPY configs/ ./configs/

# Download AI models (optional, can be done at runtime)
# RUN python3 -m ai.download_models

EXPOSE 8001

CMD ["python3", "-m", "ai.server"]
