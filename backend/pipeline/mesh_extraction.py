"""Mesh extraction from Gaussian Splatting representations."""

import numpy as np
from typing import Optional, Tuple, Dict
from dataclasses import dataclass
import logging

try:
    import open3d as o3d
    OPEN3D_AVAILABLE = True
except ImportError:
    OPEN3D_AVAILABLE = False
    logging.warning("Open3D not installed. Mesh extraction will not be available.")

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
    """Extract meshes from Gaussian representations."""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize mesh extractor.
        
        Args:
            config: Configuration dictionary
        """
        if not OPEN3D_AVAILABLE:
            raise ImportError(
                "Open3D not installed. Install with: pip install open3d"
            )
        
        self.config = config or {}
    
    def extract_from_gaussians(
        self,
        gaussians: GaussianParameters,
        method: str = "poisson",
        voxel_size: Optional[float] = None
    ) -> Optional[Mesh]:
        """
        Extract mesh from Gaussian representation.
        
        Args:
            gaussians: Gaussian parameters
            method: Extraction method ('poisson', 'ball_pivoting', 'alpha_shape')
            voxel_size: Voxel size for downsampling (optional)
            
        Returns:
            Extracted mesh or None if extraction failed
        """
        logger.info(f"Extracting mesh using {method} method")
        
        try:
            # Create point cloud from Gaussian centers
            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(gaussians.positions)
            
            if gaussians.colors is not None:
                pcd.colors = o3d.utility.Vector3dVector(gaussians.colors)
            
            # Downsample if requested
            if voxel_size is not None:
                pcd = pcd.voxel_down_sample(voxel_size)
                logger.debug(f"Downsampled to {len(pcd.points)} points")
            
            # Estimate normals
            pcd.estimate_normals(
                search_param=o3d.geometry.KDTreeSearchParamHybrid(
                    radius=0.1, max_nn=30
                )
            )
            pcd.orient_normals_consistent_tangent_plane(k=15)
            
            # Extract mesh based on method
            if method == "poisson":
                mesh_o3d = self._poisson_reconstruction(pcd)
            elif method == "ball_pivoting":
                mesh_o3d = self._ball_pivoting(pcd)
            elif method == "alpha_shape":
                mesh_o3d = self._alpha_shape(pcd)
            else:
                raise ValueError(f"Unknown extraction method: {method}")
            
            if mesh_o3d is None:
                logger.error("Mesh extraction failed")
                return None
            
            # Convert to our Mesh format
            mesh = self._convert_o3d_mesh(mesh_o3d)
            
            # Validate mesh
            if not mesh.is_valid():
                logger.error("Extracted mesh is invalid (degenerate geometry)")
                return None
            
            logger.info(
                f"Extracted mesh: {mesh.num_vertices()} vertices, "
                f"{mesh.num_faces()} faces"
            )
            
            return mesh
            
        except Exception as e:
            logger.error(f"Mesh extraction failed: {e}")
            return None
    
    def _poisson_reconstruction(
        self,
        pcd: o3d.geometry.PointCloud
    ) -> Optional[o3d.geometry.TriangleMesh]:
        """
        Poisson surface reconstruction.
        
        Args:
            pcd: Point cloud with normals
            
        Returns:
            Triangle mesh or None
        """
        try:
            depth = self.config.get('poisson_depth', 9)
            
            mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
                pcd, depth=depth
            )
            
            # Remove low-density vertices
            density_threshold = self.config.get('density_threshold', 0.01)
            densities = np.asarray(densities)
            vertices_to_remove = densities < np.quantile(densities, density_threshold)
            mesh.remove_vertices_by_mask(vertices_to_remove)
            
            return mesh
            
        except Exception as e:
            logger.error(f"Poisson reconstruction failed: {e}")
            return None
    
    def _ball_pivoting(
        self,
        pcd: o3d.geometry.PointCloud
    ) -> Optional[o3d.geometry.TriangleMesh]:
        """
        Ball pivoting algorithm.
        
        Args:
            pcd: Point cloud with normals
            
        Returns:
            Triangle mesh or None
        """
        try:
            # Estimate point cloud radius
            distances = pcd.compute_nearest_neighbor_distance()
            avg_dist = np.mean(distances)
            
            radii = [avg_dist, avg_dist * 2, avg_dist * 4]
            
            mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(
                pcd,
                o3d.utility.DoubleVector(radii)
            )
            
            return mesh
            
        except Exception as e:
            logger.error(f"Ball pivoting failed: {e}")
            return None
    
    def _alpha_shape(
        self,
        pcd: o3d.geometry.PointCloud
    ) -> Optional[o3d.geometry.TriangleMesh]:
        """
        Alpha shape reconstruction.
        
        Args:
            pcd: Point cloud
            
        Returns:
            Triangle mesh or None
        """
        try:
            alpha = self.config.get('alpha', 0.03)
            
            mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_alpha_shape(
                pcd, alpha
            )
            
            return mesh
            
        except Exception as e:
            logger.error(f"Alpha shape failed: {e}")
            return None
    
    def _convert_o3d_mesh(
        self,
        mesh_o3d: o3d.geometry.TriangleMesh
    ) -> Mesh:
        """Convert Open3D mesh to our Mesh format."""
        vertices = np.asarray(mesh_o3d.vertices)
        faces = np.asarray(mesh_o3d.triangles)
        
        normals = None
        if mesh_o3d.has_vertex_normals():
            normals = np.asarray(mesh_o3d.vertex_normals)
        
        colors = None
        if mesh_o3d.has_vertex_colors():
            colors = np.asarray(mesh_o3d.vertex_colors)
        
        return Mesh(
            vertices=vertices,
            faces=faces,
            normals=normals,
            colors=colors
        )
    
    def optimize_mesh(
        self,
        mesh: Mesh,
        target_faces: Optional[int] = None,
        smooth_iterations: int = 5
    ) -> Mesh:
        """
        Optimize mesh (simplification and smoothing).
        
        Args:
            mesh: Input mesh
            target_faces: Target number of faces for simplification
            smooth_iterations: Number of smoothing iterations
            
        Returns:
            Optimized mesh
        """
        logger.info("Optimizing mesh")
        
        try:
            # Convert to Open3D mesh
            mesh_o3d = o3d.geometry.TriangleMesh()
            mesh_o3d.vertices = o3d.utility.Vector3dVector(mesh.vertices)
            mesh_o3d.triangles = o3d.utility.Vector3iVector(mesh.faces)
            
            if mesh.normals is not None:
                mesh_o3d.vertex_normals = o3d.utility.Vector3dVector(mesh.normals)
            
            if mesh.colors is not None:
                mesh_o3d.vertex_colors = o3d.utility.Vector3dVector(mesh.colors)
            
            # Simplification
            if target_faces is not None and mesh.num_faces() > target_faces:
                logger.debug(f"Simplifying mesh from {mesh.num_faces()} to {target_faces} faces")
                mesh_o3d = mesh_o3d.simplify_quadric_decimation(target_faces)
            
            # Smoothing
            if smooth_iterations > 0:
                logger.debug(f"Smoothing mesh with {smooth_iterations} iterations")
                mesh_o3d = mesh_o3d.filter_smooth_simple(number_of_iterations=smooth_iterations)
            
            # Recompute normals
            mesh_o3d.compute_vertex_normals()
            
            # Convert back
            optimized = self._convert_o3d_mesh(mesh_o3d)
            
            logger.info(
                f"Optimized mesh: {optimized.num_vertices()} vertices, "
                f"{optimized.num_faces()} faces"
            )
            
            return optimized
            
        except Exception as e:
            logger.error(f"Mesh optimization failed: {e}")
            return mesh
    
    def validate_mesh(self, mesh: Mesh) -> Tuple[bool, str]:
        """
        Validate mesh geometry.
        
        Args:
            mesh: Mesh to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check minimum vertices
        if mesh.num_vertices() < 4:
            return False, f"Too few vertices: {mesh.num_vertices()} < 4"
        
        # Check minimum faces
        if mesh.num_faces() < 1:
            return False, "No faces"
        
        # Check for NaN/Inf
        if np.any(~np.isfinite(mesh.vertices)):
            return False, "Vertices contain NaN or Inf"
        
        # Check face indices are valid
        max_idx = np.max(mesh.faces)
        if max_idx >= mesh.num_vertices():
            return False, f"Invalid face index: {max_idx} >= {mesh.num_vertices()}"
        
        # Check for degenerate faces
        mesh_o3d = o3d.geometry.TriangleMesh()
        mesh_o3d.vertices = o3d.utility.Vector3dVector(mesh.vertices)
        mesh_o3d.triangles = o3d.utility.Vector3iVector(mesh.faces)
        
        mesh_o3d.remove_degenerate_triangles()
        mesh_o3d.remove_duplicated_triangles()
        mesh_o3d.remove_duplicated_vertices()
        mesh_o3d.remove_non_manifold_edges()
        
        cleaned_faces = len(mesh_o3d.triangles)
        if cleaned_faces < mesh.num_faces() * 0.5:
            return False, f"Too many degenerate faces: {mesh.num_faces() - cleaned_faces}"
        
        return True, "Valid"
    
    def export_to_obj(
        self,
        mesh: Mesh,
        output_path: str
    ):
        """
        Export mesh to OBJ format.
        
        Args:
            mesh: Mesh to export
            output_path: Output file path
        """
        logger.info(f"Exporting mesh to {output_path}")
        
        with open(output_path, 'w') as f:
            # Write vertices
            for v in mesh.vertices:
                f.write(f"v {v[0]} {v[1]} {v[2]}\n")
            
            # Write normals
            if mesh.normals is not None:
                for n in mesh.normals:
                    f.write(f"vn {n[0]} {n[1]} {n[2]}\n")
            
            # Write colors (as comments, OBJ doesn't have standard color support)
            if mesh.colors is not None:
                for c in mesh.colors:
                    f.write(f"# vc {c[0]} {c[1]} {c[2]}\n")
            
            # Write faces (OBJ uses 1-based indexing)
            for face in mesh.faces:
                if mesh.normals is not None:
                    f.write(f"f {face[0]+1}//{face[0]+1} {face[1]+1}//{face[1]+1} {face[2]+1}//{face[2]+1}\n")
                else:
                    f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")
        
        logger.info(f"Exported mesh with {mesh.num_vertices()} vertices and {mesh.num_faces()} faces")


def handle_extraction_failure(
    gaussians: GaussianParameters,
    fallback: str = "pure_gaussian"
) -> Dict:
    """
    Handle mesh extraction failure.
    
    Args:
        gaussians: Original Gaussian parameters
        fallback: Fallback strategy ('pure_gaussian', 'point_cloud')
        
    Returns:
        Fallback representation metadata
    """
    logger.warning(f"Mesh extraction failed, using fallback: {fallback}")
    
    if fallback == "pure_gaussian":
        return {
            'type': 'gaussian',
            'editable': False,
            'num_gaussians': len(gaussians.positions),
            'fallback_reason': 'mesh_extraction_failed'
        }
    elif fallback == "point_cloud":
        return {
            'type': 'point_cloud',
            'editable': False,
            'num_points': len(gaussians.positions),
            'fallback_reason': 'mesh_extraction_failed'
        }
    else:
        raise ValueError(f"Unknown fallback strategy: {fallback}")
