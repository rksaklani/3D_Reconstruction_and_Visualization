# Reconstruction Dependencies

This directory contains the source code for reconstruction libraries. These are large dependencies (6GB+) and are not tracked in git.

## Required Dependencies

### 1. COLMAP
Structure-from-Motion and Multi-View Stereo library.

**Installation:**
```bash
# Clone COLMAP
git clone https://github.com/colmap/colmap.git colmap-src
cd colmap-src
mkdir build && cd build
cmake .. -DCMAKE_CUDA_ARCHITECTURES=native
make -j$(nproc)
sudo make install
```

### 2. Ceres Solver
Non-linear least squares optimization library.

**Installation:**
```bash
# Clone Ceres Solver
git clone https://github.com/ceres-solver/ceres-solver.git ceres-src
cd ceres-src
mkdir build && cd build
cmake ..
make -j$(nproc)
sudo make install
```

### 3. Abseil C++
Dependency for Ceres Solver.

**Installation:**
```bash
# Clone Abseil
git clone https://github.com/abseil/abseil-cpp.git abseil-src
cd abseil-src
mkdir build && cd build
cmake ..
make -j$(nproc)
sudo make install
```

### 4. Gaussian Splatting
3D Gaussian Splatting implementation.

**Installation:**
```bash
# Clone Gaussian Splatting
git clone https://github.com/graphdeco-inria/gaussian-splatting.git gaussian-splatting-src
cd gaussian-splatting-src
pip install -r requirements.txt
pip install submodules/diff-gaussian-rasterization
pip install submodules/simple-knn
```

## Quick Setup Script

Run the setup script to install all dependencies:

```bash
cd scripts/setup
./install_deps.sh
```

## Directory Structure

```
reconstruction/
├── colmap-src/          # COLMAP source (not in git)
├── ceres-src/           # Ceres Solver source (not in git)
├── abseil-src/          # Abseil C++ source (not in git)
├── gaussian-splatting-src/  # Gaussian Splatting source (not in git)
├── scripts/             # Helper scripts
└── README.md            # This file
```

## Notes

- These directories are excluded from git due to their large size (6GB+)
- Each developer needs to install these dependencies locally
- The setup script automates the installation process
- Make sure you have CUDA installed for GPU acceleration
