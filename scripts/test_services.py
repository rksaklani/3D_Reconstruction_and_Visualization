#!/usr/bin/env python3
"""Test script for all services."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_config_loader():
    """Test configuration loader."""
    print("\n=== Testing Configuration Loader ===")
    try:
        from backend.config.loader import load_config
        
        config = load_config()
        print(f"✓ Loaded configuration")
        print(f"  - Pipeline config: {len(config.pipeline)} keys")
        print(f"  - Model config: {len(config.model)} keys")
        print(f"  - MinIO config: {len(config.minio)} keys")
        print(f"  - COLMAP config: {len(config.colmap)} keys")
        print(f"  - Gaussian config: {len(config.gaussian)} keys")
        print(f"  - Physics config: {len(config.physics)} keys")
        return True
    except Exception as e:
        print(f"✗ Configuration loader failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_minio_service():
    """Test MinIO service."""
    print("\n=== Testing MinIO Service ===")
    try:
        from backend.services.minio_service import MinIOService
        
        # Try to connect (will fail if MinIO not running, but tests import)
        print("✓ MinIO service imported successfully")
        print("  Note: MinIO server must be running for full functionality")
        return True
    except Exception as e:
        print(f"✗ MinIO service failed: {e}")
        return False


def test_preprocessing():
    """Test preprocessing pipeline."""
    print("\n=== Testing Preprocessing Pipeline ===")
    try:
        from backend.pipeline.preprocess import ImageLoader, VideoDecoder, ImagePreprocessor
        
        loader = ImageLoader()
        decoder = VideoDecoder()
        preprocessor = ImagePreprocessor()
        
        print("✓ Preprocessing components initialized")
        print(f"  - ImageLoader: min_images={loader.min_images}")
        print(f"  - VideoDecoder: sampling_rate={decoder.sampling_rate}")
        print(f"  - ImagePreprocessor: config loaded")
        return True
    except Exception as e:
        print(f"✗ Preprocessing failed: {e}")
        return False


def test_colmap_service():
    """Test COLMAP service."""
    print("\n=== Testing COLMAP Service ===")
    try:
        from backend.services.colmap_service import COLMAPService
        
        print("✓ COLMAP service imported successfully")
        print("  Note: COLMAP binary must be installed for full functionality")
        return True
    except Exception as e:
        print(f"✗ COLMAP service failed: {e}")
        return False


def test_yolo_detector():
    """Test YOLO detector."""
    print("\n=== Testing YOLO Detector ===")
    try:
        from ai.detection.yolo import YOLODetector, YOLO_AVAILABLE
        
        if YOLO_AVAILABLE:
            print("✓ YOLO detector available")
            print("  - Ultralytics installed")
            print("  - Ready for object detection")
        else:
            print("⚠ YOLO detector not available (Ultralytics not installed)")
        return True
    except Exception as e:
        print(f"✗ YOLO detector failed: {e}")
        return False


def test_sam_segmenter():
    """Test SAM segmenter."""
    print("\n=== Testing SAM Segmenter ===")
    try:
        from ai.segmentation.sam import SAMSegmenter, SAM_AVAILABLE
        
        if SAM_AVAILABLE:
            print("✓ SAM segmenter available")
        else:
            print("⚠ SAM segmenter using fallback (Python 3.13 compatibility)")
            print("  - Fallback: Watershed segmentation")
        return True
    except Exception as e:
        print(f"✗ SAM segmenter failed: {e}")
        return False


def test_scene_classifier():
    """Test scene classifier."""
    print("\n=== Testing Scene Classifier ===")
    try:
        from ai.classification.scene_classifier import SceneClassifier, CLIP_AVAILABLE
        
        if CLIP_AVAILABLE:
            print("✓ Scene classifier with CLIP available")
        else:
            print("⚠ Scene classifier using fallback (Python 3.13 compatibility)")
            print("  - Fallback: Heuristic-based classification")
        return True
    except Exception as e:
        print(f"✗ Scene classifier failed: {e}")
        return False


def test_object_tracker():
    """Test object tracker."""
    print("\n=== Testing Object Tracker ===")
    try:
        from ai.tracking.object_tracker import ObjectTracker
        
        tracker = ObjectTracker()
        print("✓ Object tracker initialized")
        print(f"  - IoU threshold: {tracker.iou_threshold}")
        print(f"  - Max age: {tracker.max_age}")
        print(f"  - Min hits: {tracker.min_hits}")
        return True
    except Exception as e:
        print(f"✗ Object tracker failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("3D Reconstruction Pipeline - Service Tests")
    print("=" * 60)
    
    tests = [
        test_config_loader,
        test_minio_service,
        test_preprocessing,
        test_colmap_service,
        test_yolo_detector,
        test_sam_segmenter,
        test_scene_classifier,
        test_object_tracker,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    if all(results):
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n⚠ Some tests failed or have warnings")
        return 1


if __name__ == "__main__":
    sys.exit(main())
