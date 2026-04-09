# 3D Reconstruction and Visualization Pipeline

An intelligent, interactive 3D world engine that transforms 2D images or video into fully interactive, physics-enabled 3D scenes with semantic understanding.

## Features

- 🎥 **Input Processing**: Images or video → frame extraction
- 📸 **Structure from Motion**: COLMAP + Ceres bundle adjustment
- 🧠 **AI Scene Understanding**: Object detection (YOLOv8), segmentation (SAM), tracking, classification
- 🎨 **Hybrid Representation**: Static/dynamic Gaussian Splatting + mesh extraction
- ⚙️ **Physics Simulation**: Collision detection, gravity, interactive objects
- 🎮 **Hybrid Rendering**: Babylon.js + custom Gaussian shaders + physics rendering
- 🌐 **Interactive 3D World**: Photorealistic, physics-enabled, editable scenes

## Project Structure

```
project-root/
├── backend/          # API, pipeline orchestration, workers, services
├── ai/              # Object detection, segmentation, tracking, classification
├── reconstruction/  # COLMAP, Ceres, Gaussian Splatting sources
├── rendering/       # Gaussian renderer, shaders, WebGL utilities
├── frontend/        # React application with Babylon.js viewer
├── storage/         # Local development storage
├── configs/         # YAML configuration files
├── docker/          # Docker containers
└── scripts/         # Setup, dev, and deployment scripts
```

## Technology Stack

**Backend/AI**: Python 3.10+, FastAPI, PyTorch, Celery, Redis  
**Reconstruction**: COLMAP (C++), Ceres Solver (C++), Gaussian Splatting  
**Rendering**: TypeScript, Babylon.js, WebGL, Ammo.js (Bullet Physics)  
**Frontend**: React, TypeScript, Vite, Tailwind CSS  
**Storage**: MinIO (S3-compatible object storage)  
**Infrastructure**: Docker, Docker Compose, Kubernetes (optional)

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- CUDA 11.8+ or 12.0+ (for GPU acceleration)
- Docker & Docker Compose (optional)

### Setup

1. **Clone and navigate to project**
```bash
cd ~/aditya
```

2. **Install reconstruction dependencies (COLMAP, Ceres, Gaussian Splatting)**
```bash
cd scripts/setup
./install_reconstruction_deps.sh
```
Note: This installs ~6GB of dependencies. These are excluded from git and must be installed locally.

3. **Install backend dependencies**
```bash
cd ../../backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

4. **Install frontend dependencies**
```bash
cd ../frontend
npm install
```

5. **Download AI models**
```bash
cd ../scripts/setup
./download_models.sh
```

6. **Setup MinIO (optional for development)**
```bash
./setup_minio.sh
```

### Development

**Start backend server:**
```bash
cd backend
source venv/bin/activate
uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload
```

**Start frontend dev server:**
```bash
cd frontend
npm run dev
```

**Access the application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Documentation

- [Design Document](.kiro/specs/3d-reconstruction-pipeline/design.md)
- [Requirements](.kiro/specs/3d-reconstruction-pipeline/requirements.md)
- [Implementation Tasks](.kiro/specs/3d-reconstruction-pipeline/tasks.md)

## Current Implementation Status

✅ **Completed** (~20%):
- COLMAP, Ceres Solver, Gaussian Splatting installations
- Basic FastAPI backend with job management
- Basic React frontend
- File upload and job tracking

🚧 **In Progress** (~0%):
- AI Scene Understanding Layer
- Hybrid Representation Layer
- Physics Engine Integration
- Hybrid Rendering Layer
- MinIO Storage Integration
- Advanced orchestration (Celery + Redis)

See [tasks.md](.kiro/specs/3d-reconstruction-pipeline/tasks.md) for detailed implementation plan.

## License

See individual component licenses:
- COLMAP: BSD 3-Clause
- Ceres Solver: BSD 3-Clause
- Gaussian Splatting: Custom (research/non-commercial)
- Babylon.js: Apache 2.0

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.
