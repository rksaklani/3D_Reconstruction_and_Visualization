"""Mesh extraction stub - simplified version without Open3D."""

import numpy as np
from typing import Optional, Dict
from dataclasses import dataclass
import logging

from backend.pipeline.gaussian_splatting import GaussianParameters

logger = logging.getLogger(__name__)


@dataclass
class Mesh:
    """Triangle mesh representation."""
    vertices: np.ndarray  # (V, 3)
    faces: np.ndarray  # (F, 3) indices
    normals: Optional[np.ndarray] = None  # (V, 3)
    colors: Optional[np.ndarray] = None  # (V, 3)
    
    def is_valid(self) -> bool:
        """Check if mesh is valid."""
        if len(self.vertices) < 4:
            return False
        if len(self.faces) < 1:
            return False
        return True
    
    def num_vertices(self) -> int:
        """Get number of vertices."""
        return len(self.vertices)
    
    def num_faces(self) -> int:
        """Get number of faces."""
        return len(self.faces)


class MeshExtractor:
    """Extract meshes from Gaussian representations (stub)."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize mesh extractor."""
        self.config = config or {}
        logger.warning("MeshExtractor is using stub implementation (Open3D not available)")
    
    def extract_mesh_from_gaussians(
        self,
        gaussians: GaussianParameters,
        method: str = "poisson"
    ) -> Optional[Mesh]:
        """Extract mesh (stub - returns None)."""
        logger.warning("Mesh extraction not available (Open3D not installed)")
        return None


def handle_extraction_failure(
    gaussians: GaussianParameters,
    fallback: str = "pure_gaussian"
) -> Dict:
    """Handle mesh extraction failure."""
    logger.warning(f"Mesh extraction failed, using fallback: {fallback}")
    
    if fallback == "pure_gaussian":
        return {
            'type': 'gaussian',
            'editable': False,
            'num_gaussians': len(gaussians.positions),
            'fallback_reason': 'mesh_extraction_not_available'
        }
    elif fallback == "point_cloud":
        return {
            'type': 'point_cloud',
            'editable': False,
            'num_points': len(gaussians.positions),
            'fallback_reason': 'mesh_extraction_not_available'
        }
    else:
        raise ValueError(f"Unknown fallback strategy: {fallback}")
