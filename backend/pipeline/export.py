"""Export functionality for various 3D formats."""

import numpy as np
import json
import struct
from pathlib import Path
from typing import Dict, List, Optional
import logging
import zipfile

from backend.pipeline.gaussian_splatting import GaussianParameters
from backend.pipeline.mesh_extraction import Mesh
from backend.pipeline.hybrid_scene import HybridScene
from backend.pipeline.physics_engine import PhysicsScene

logger = logging.getLogger(__name__)


class PLYExporter:
    """Export Gaussian Splatting to PLY format."""
    
    @staticmethod
    def export(
        gaussians: GaussianParameters,
        output_path: str,
        format: str = "binary"
    ):
        """
        Export Gaussians to PLY format.
        
        Args:
            gaussians: Gaussian parameters
            output_path: Output file path
            format: "ascii" or "binary"
        """
        n = len(gaussians.positions)
        
        # Validate parameters
        if not (0 <= gaussians.opacities.min() and gaussians.opacities.max() <= 1):
            logger.warning("Opacity values outside [0,1] range")
        
        # Create PLY header
        header = f"""ply
format {format}_little_endian 1.0
comment Gaussian Splatting Export
element vertex {n}
property float x
property float y
property float z
property float nx
property float ny
property float nz
property uchar red
property uchar green
property uchar blue
property float opacity
property float scale_0
property float scale_1
property float scale_2
property float rot_0
property float rot_1
property float rot_2
property float rot_3
end_header
"""
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'wb' if format == 'binary' else 'w') as f:
            if format == 'ascii':
                f.write(header)
                
                # Write vertices
                for i in range(n):
                    x, y, z = gaussians.positions[i]
                    r, g, b = (gaussians.colors[i] * 255).astype(np.uint8)
                    opacity = gaussians.opacities[i, 0]
                    scale = gaussians.scales[i]
                    rot = gaussians.rotations[i]
                    
                    # Use zero normals (not used for Gaussians)
                    f.write(
                        f"{x} {y} {z} 0 0 0 {r} {g} {b} {opacity} "
                        f"{scale[0]} {scale[1]} {scale[2]} "
                        f"{rot[0]} {rot[1]} {rot[2]} {rot[3]}\n"
                    )
            else:
                # Binary format
                f.write(header.encode('ascii'))
                
                # Write binary data
                for i in range(n):
                    x, y, z = gaussians.positions[i]
                    r, g, b = (gaussians.colors[i] * 255).astype(np.uint8)
                    opacity = gaussians.opacities[i, 0]
                    scale = gaussians.scales[i]
                    rot = gaussians.rotations[i]
                    
                    # Pack as binary
                    data = struct.pack('fff', x, y, z)  # position
                    data += struct.pack('fff', 0, 0, 0)  # normals (unused)
                    data += struct.pack('BBB', r, g, b)  # colors
                    data += struct.pack('f', opacity)  # opacity
                    data += struct.pack('fff', scale[0], scale[1], scale[2])  # scales
                    data += struct.pack('ffff', rot[0], rot[1], rot[2], rot[3])  # rotation
                    
                    f.write(data)
        
        logger.info(f"Exported {n} Gaussians to PLY: {output_path}")
    
    @staticmethod
    def validate_export(output_path: str) -> bool:
        """Validate exported PLY file."""
        try:
            with open(output_path, 'rb') as f:
                header = f.read(1000).decode('ascii', errors='ignore')
                
                if not header.startswith('ply'):
                    logger.error("Invalid PLY header")
                    return False
                
                # Check vertex count
                if 'element vertex' not in header:
                    logger.error("Missing vertex element")
                    return False
                
                return True
        except Exception as e:
            logger.error(f"PLY validation failed: {e}")
            return False


class SplatExporter:
    """Export to Splat format (complete Gaussian parameters)."""
    
    @staticmethod
    def export(
        gaussians: GaussianParameters,
        output_path: str,
        include_sh: bool = True
    ):
        """
        Export to Splat format.
        
        Args:
            gaussians: Gaussian parameters
            output_path: Output file path
            include_sh: Include spherical harmonics coefficients
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create Splat data structure
        splat_data = {
            'version': '1.0',
            'num_gaussians': len(gaussians.positions),
            'sh_degree': gaussians.sh_degree,
            'positions': gaussians.positions.tolist(),
            'opacities': gaussians.opacities.tolist(),
            'scales': gaussians.scales.tolist(),
            'rotations': gaussians.rotations.tolist(),
            'colors': gaussians.colors.tolist()
        }
        
        # Save as JSON (or binary format for production)
        with open(output_file, 'w') as f:
            json.dump(splat_data, f, indent=2)
        
        logger.info(f"Exported Splat format: {output_path}")


class MeshExporter:
    """Export meshes to OBJ format."""
    
    @staticmethod
    def export(
        mesh: Mesh,
        output_path: str
    ):
        """
        Export mesh to OBJ format.
        
        Args:
            mesh: Triangle mesh
            output_path: Output file path
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            # Write header
            f.write("# OBJ file exported from 3D Reconstruction Pipeline\n")
            f.write(f"# Vertices: {mesh.num_vertices()}\n")
            f.write(f"# Faces: {mesh.num_faces()}\n\n")
            
            # Write vertices
            for v in mesh.vertices:
                f.write(f"v {v[0]} {v[1]} {v[2]}\n")
            
            # Write normals
            if mesh.normals is not None:
                f.write("\n")
                for n in mesh.normals:
                    f.write(f"vn {n[0]} {n[1]} {n[2]}\n")
            
            # Write colors (as comments, OBJ doesn't have standard color support)
            if mesh.colors is not None:
                f.write("\n")
                for c in mesh.colors:
                    f.write(f"# vc {c[0]} {c[1]} {c[2]}\n")
            
            # Write faces (OBJ uses 1-based indexing)
            f.write("\n")
            for face in mesh.faces:
                if mesh.normals is not None:
                    f.write(
                        f"f {face[0]+1}//{face[0]+1} "
                        f"{face[1]+1}//{face[1]+1} "
                        f"{face[2]+1}//{face[2]+1}\n"
                    )
                else:
                    f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")
        
        logger.info(f"Exported mesh to OBJ: {output_path}")


class PhysicsExporter:
    """Export physics scene data."""
    
    @staticmethod
    def export(
        physics_scene: PhysicsScene,
        output_path: str
    ):
        """
        Export physics scene to JSON.
        
        Args:
            physics_scene: Physics scene
            output_path: Output file path
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create physics data structure
        physics_data = {
            'scene_id': physics_scene.scene_id,
            'gravity': physics_scene.gravity.tolist(),
            'time_step': physics_scene.time_step,
            'rigid_bodies': [
                {
                    'body_id': body.body_id,
                    'object_id': body.object_id,
                    'label': body.label,
                    'mass': body.mass,
                    'friction': body.friction,
                    'restitution': body.restitution,
                    'is_static': body.is_static,
                    'position': body.position.tolist(),
                    'orientation': body.orientation.tolist(),
                    'linear_velocity': body.linear_velocity.tolist(),
                    'angular_velocity': body.angular_velocity.tolist()
                }
                for body in physics_scene.rigid_bodies
            ]
        }
        
        with open(output_file, 'w') as f:
            json.dump(physics_data, f, indent=2)
        
        logger.info(f"Exported physics scene: {output_path}")


class HybridScenePackager:
    """Package hybrid scene with all representations."""
    
    @staticmethod
    def package(
        hybrid_scene: HybridScene,
        physics_scene: Optional[PhysicsScene],
        output_path: str
    ):
        """
        Package hybrid scene into single archive.
        
        Args:
            hybrid_scene: Hybrid scene
            physics_scene: Physics scene (optional)
            output_path: Output archive path (.zip)
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Packaging hybrid scene to {output_path}")
        
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Export scene metadata
            metadata_path = Path("scene_metadata.json")
            hybrid_scene.export_metadata(str(metadata_path))
            zipf.write(metadata_path, "scene_metadata.json")
            metadata_path.unlink()
            
            # Export each object
            for obj in hybrid_scene.objects:
                obj_prefix = f"objects/object_{obj.object_id}"
                
                # Export Gaussians
                if obj.gaussians is not None:
                    ply_path = Path(f"temp_gaussian_{obj.object_id}.ply")
                    PLYExporter.export(obj.gaussians, str(ply_path), format="binary")
                    zipf.write(ply_path, f"{obj_prefix}/gaussians.ply")
                    ply_path.unlink()
                
                # Export mesh
                if obj.mesh is not None:
                    obj_path = Path(f"temp_mesh_{obj.object_id}.obj")
                    MeshExporter.export(obj.mesh, str(obj_path))
                    zipf.write(obj_path, f"{obj_prefix}/mesh.obj")
                    obj_path.unlink()
                
                # Export dynamic Gaussians metadata
                if obj.dynamic_gaussians is not None:
                    dynamic_data = {
                        'track_id': obj.dynamic_gaussians.track_id,
                        'label': obj.dynamic_gaussians.label,
                        'num_timesteps': obj.dynamic_gaussians.num_timesteps,
                        'timestamps': obj.dynamic_gaussians.timestamps,
                        'is_rigid': obj.dynamic_gaussians.is_rigid
                    }
                    
                    dynamic_path = Path(f"temp_dynamic_{obj.object_id}.json")
                    with open(dynamic_path, 'w') as f:
                        json.dump(dynamic_data, f, indent=2)
                    zipf.write(dynamic_path, f"{obj_prefix}/dynamic.json")
                    dynamic_path.unlink()
            
            # Export background
            if hybrid_scene.background_gaussians is not None:
                bg_path = Path("temp_background.ply")
                PLYExporter.export(
                    hybrid_scene.background_gaussians,
                    str(bg_path),
                    format="binary"
                )
                zipf.write(bg_path, "background/gaussians.ply")
                bg_path.unlink()
            
            # Export physics scene
            if physics_scene is not None:
                physics_path = Path("temp_physics.json")
                PhysicsExporter.export(physics_scene, str(physics_path))
                zipf.write(physics_path, "physics/scene.json")
                physics_path.unlink()
        
        logger.info(f"Packaged hybrid scene: {output_file.stat().st_size / 1024 / 1024:.2f} MB")


class ExportManager:
    """Manage all export operations."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize export manager."""
        self.config = config or {}
    
    def export_all(
        self,
        hybrid_scene: HybridScene,
        physics_scene: Optional[PhysicsScene],
        output_dir: str
    ):
        """
        Export all formats.
        
        Args:
            hybrid_scene: Hybrid scene
            physics_scene: Physics scene
            output_dir: Output directory
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Exporting all formats to {output_dir}")
        
        # Export PLY for each object
        for obj in hybrid_scene.objects:
            if obj.gaussians is not None:
                ply_path = output_path / f"object_{obj.object_id}_gaussians.ply"
                PLYExporter.export(obj.gaussians, str(ply_path))
        
        # Export background
        if hybrid_scene.background_gaussians is not None:
            bg_path = output_path / "background_gaussians.ply"
            PLYExporter.export(hybrid_scene.background_gaussians, str(bg_path))
        
        # Export meshes
        for obj in hybrid_scene.objects:
            if obj.mesh is not None:
                mesh_path = output_path / f"object_{obj.object_id}_mesh.obj"
                MeshExporter.export(obj.mesh, str(mesh_path))
        
        # Export physics
        if physics_scene is not None:
            physics_path = output_path / "physics_scene.json"
            PhysicsExporter.export(physics_scene, str(physics_path))
        
        # Export metadata
        metadata_path = output_path / "scene_metadata.json"
        hybrid_scene.export_metadata(str(metadata_path))
        
        # Create packaged archive
        archive_path = output_path / f"{hybrid_scene.scene_id}_complete.zip"
        HybridScenePackager.package(hybrid_scene, physics_scene, str(archive_path))
        
        logger.info("Export complete")
    
    def validate_exports(self, output_dir: str) -> Dict[str, bool]:
        """Validate all exported files."""
        output_path = Path(output_dir)
        
        validation_results = {}
        
        # Validate PLY files
        for ply_file in output_path.glob("*.ply"):
            is_valid = PLYExporter.validate_export(str(ply_file))
            validation_results[str(ply_file)] = is_valid
        
        # Validate archive
        archive_files = list(output_path.glob("*_complete.zip"))
        if archive_files:
            archive_path = archive_files[0]
            try:
                with zipfile.ZipFile(archive_path, 'r') as zipf:
                    # Test archive integrity
                    bad_file = zipf.testzip()
                    validation_results[str(archive_path)] = bad_file is None
            except Exception as e:
                logger.error(f"Archive validation failed: {e}")
                validation_results[str(archive_path)] = False
        
        return validation_results
