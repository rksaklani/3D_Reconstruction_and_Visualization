#!/bin/bash
# Download AI model weights for YOLOv8, SAM, and CLIP

set -e

echo "=== Downloading AI Model Weights ==="

# Create models directory
MODELS_DIR="ai/models"
mkdir -p "$MODELS_DIR"

echo ""
echo "1. Downloading YOLOv8 models..."
echo "   YOLOv8 models will be auto-downloaded on first use"
echo "   Available models: yolov8n.pt, yolov8s.pt, yolov8m.pt, yolov8l.pt, yolov8x.pt"

# Pre-download YOLOv8n (nano) model
python3 -c "
from ultralytics import YOLO
import os
os.makedirs('$MODELS_DIR', exist_ok=True)
model = YOLO('yolov8n.pt')
print('Downloaded YOLOv8n model')
"

echo ""
echo "2. Downloading SAM (Segment Anything) models..."
echo "   Downloading ViT-H model (2.4GB)..."

# Download SAM ViT-H checkpoint
SAM_CHECKPOINT="$MODELS_DIR/sam_vit_h_4b8939.pth"
if [ ! -f "$SAM_CHECKPOINT" ]; then
    wget -O "$SAM_CHECKPOINT" \
        https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth
    echo "   Downloaded SAM ViT-H checkpoint"
else
    echo "   SAM ViT-H checkpoint already exists"
fi

# Optionally download smaller SAM models
echo ""
echo "   Optional: Download smaller SAM models? (y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "   Downloading ViT-L model (1.2GB)..."
    SAM_VIT_L="$MODELS_DIR/sam_vit_l_0b3195.pth"
    if [ ! -f "$SAM_VIT_L" ]; then
        wget -O "$SAM_VIT_L" \
            https://dl.fbaipublicfiles.com/segment_anything/sam_vit_l_0b3195.pth
        echo "   Downloaded SAM ViT-L checkpoint"
    fi
    
    echo "   Downloading ViT-B model (375MB)..."
    SAM_VIT_B="$MODELS_DIR/sam_vit_b_01ec64.pth"
    if [ ! -f "$SAM_VIT_B" ]; then
        wget -O "$SAM_VIT_B" \
            https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth
        echo "   Downloaded SAM ViT-B checkpoint"
    fi
fi

echo ""
echo "3. Downloading CLIP models..."
echo "   CLIP models will be auto-downloaded on first use"
echo "   Available models: ViT-B/32, ViT-B/16, ViT-L/14"

# Pre-download CLIP ViT-B/32 model
python3 -c "
import clip
import torch
model, preprocess = clip.load('ViT-B/32', device='cpu')
print('Downloaded CLIP ViT-B/32 model')
"

echo ""
echo "=== Model Download Complete ==="
echo ""
echo "Downloaded models:"
echo "  - YOLOv8n: Object detection"
echo "  - SAM ViT-H: Semantic segmentation"
echo "  - CLIP ViT-B/32: Scene classification"
echo ""
echo "Models are stored in: $MODELS_DIR"
echo ""
echo "To use GPU acceleration, ensure CUDA is installed and configured."
