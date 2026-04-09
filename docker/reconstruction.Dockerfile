FROM ubuntu:22.04

WORKDIR /app

# Install dependencies for COLMAP and Ceres
RUN apt-get update && apt-get install -y \
    git \
    cmake \
    build-essential \
    libboost-all-dev \
    libeigen3-dev \
    libsuitesparse-dev \
    libfreeimage-dev \
    libgoogle-glog-dev \
    libgflags-dev \
    libglew-dev \
    qtbase5-dev \
    libqt5opengl5-dev \
    libcgal-dev \
    libatlas-base-dev \
    libsuitesparse-dev \
    && rm -rf /var/lib/apt/lists/*

# Build and install Ceres Solver
RUN git clone https://github.com/ceres-solver/ceres-solver.git && \
    cd ceres-solver && \
    mkdir build && cd build && \
    cmake .. && \
    make -j$(nproc) && \
    make install && \
    cd ../.. && rm -rf ceres-solver

# Build and install COLMAP
RUN git clone https://github.com/colmap/colmap.git && \
    cd colmap && \
    mkdir build && cd build && \
    cmake .. && \
    make -j$(nproc) && \
    make install && \
    cd ../.. && rm -rf colmap

# Copy reconstruction scripts
COPY reconstruction/ ./reconstruction/

EXPOSE 8002

CMD ["bash"]
