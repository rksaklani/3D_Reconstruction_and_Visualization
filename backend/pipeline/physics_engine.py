"""Physics engine integration using PyBullet."""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

try:
    import pybullet as p
    import pybullet_data
    PYBULLET_AVAILABLE = True
except ImportError:
    PYBULLET_AVAILABLE = False
    logging.warning("PyBullet not installed. Physics simulation will not be available.")

from backend.pipeline.hybrid_scene import HybridScene, SceneObject
from backend.pipeline.mesh_extraction import Mesh

logger = logging.getLogger(__name__)


@dataclass
class RigidBody:
    """Rigid body in physics simulation."""
    body_id: int
    object_id: int
    label: str
    mass: float
    friction: float
    restitution: float
    is_static: bool
    
    # State
    position: np.ndarray  # (3,)
    orientation: np.ndarray  # (4,) quaternion
    linear_velocity: np.ndarray  # (3,)
    angular_velocity: np.ndarray  # (3,)


@dataclass
class PhysicsScene:
    """Physics scene containing rigid bodies."""
    scene_id: str
    rigid_bodies: List[RigidBody]
    gravity: np.ndarray  # (3,)
    time_step: float
    
    def get_body_by_object_id(self, object_id: int) -> Optional[RigidBody]:
        """Get rigid body by object ID."""
        for body in self.rigid_bodies:
            if body.object_id == object_id:
                return body
        return None


class PhysicsEngine:
    """Physics engine using PyBullet."""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize physics engine.
        
        Args:
            config: Configuration dictionary
        """
        if not PYBULLET_AVAILABLE:
            raise ImportError("PyBullet not installed. Install with: pip install pybullet")
        
        self.config = config or {}
        self.client_id = None
        self.rigid_bodies = []
    
    def initialize(self, gui: bool = False):
        """
        Initialize PyBullet physics engine.
        
        Args:
            gui: Whether to use GUI mode
        """
        if gui:
            self.client_id = p.connect(p.GUI)
        else:
            self.client_id = p.connect(p.DIRECT)
        
        # Set additional search path for URDF files
        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        
        # Configure gravity
        gravity = self.config.get('engine', {}).get('gravity', [0.0, -9.81, 0.0])
        p.setGravity(*gravity, physicsClientId=self.client_id)
        
        # Configure time step
        time_step = self.config.get('engine', {}).get('time_step', 1.0/60.0)
        p.setTimeStep(time_step, physicsClientId=self.client_id)
        
        # Configure solver
        solver_iterations = self.config.get('engine', {}).get('solver_iterations', 10)
        p.setPhysicsEngineParameter(
            numSolverIterations=solver_iterations,
            physicsClientId=self.client_id
        )
        
        logger.info(f"Physics engine initialized (GUI={gui})")
    
    def shutdown(self):
        """Shutdown physics engine."""
        if self.client_id is not None:
            p.disconnect(physicsClientId=self.client_id)
            self.client_id = None
            logger.info("Physics engine shutdown")
    
    def create_physics_scene(
        self,
        hybrid_scene: HybridScene
    ) -> PhysicsScene:
        """
        Create physics scene from hybrid scene.
        
        Args:
            hybrid_scene: Hybrid scene with objects
            
        Returns:
            Physics scene
        """
        logger.info(f"Creating physics scene from hybrid scene: {hybrid_scene.scene_id}")
        
        physics_scene = PhysicsScene(
            scene_id=hybrid_scene.scene_id,
            rigid_bodies=[],
            gravity=np.array(self.config.get('engine', {}).get('gravity', [0.0, -9.81, 0.0])),
            time_step=self.config.get('engine', {}).get('time_step', 1.0/60.0)
        )
        
        # Create rigid bodies for each object
        for obj in hybrid_scene.objects:
            rigid_body = self._create_rigid_body(obj)
            if rigid_body is not None:
                physics_scene.rigid_bodies.append(rigid_body)
                self.rigid_bodies.append(rigid_body)
        
        logger.info(f"Created physics scene with {len(physics_scene.rigid_bodies)} rigid bodies")
        
        return physics_scene
    
    def _create_rigid_body(
        self,
        scene_object: SceneObject
    ) -> Optional[RigidBody]:
        """
        Create rigid body from scene object.
        
        Args:
            scene_object: Scene object
            
        Returns:
            Rigid body or None if creation failed
        """
        try:
            # Generate collision mesh
            collision_shape_id = self._create_collision_shape(scene_object)
            
            if collision_shape_id is None:
                logger.error(f"Failed to create collision shape for object {scene_object.object_id}")
                return None
            
            # Determine mass and properties
            mass, friction, restitution = self._get_physical_properties(scene_object)
            
            # Create multi-body
            if scene_object.bbox_min is not None:
                position = (scene_object.bbox_min + scene_object.bbox_max) / 2
            else:
                position = np.array([0.0, 0.0, 0.0])
            
            orientation = np.array([0.0, 0.0, 0.0, 1.0])  # Identity quaternion
            
            body_id = p.createMultiBody(
                baseMass=mass,
                baseCollisionShapeIndex=collision_shape_id,
                basePosition=position.tolist(),
                baseOrientation=orientation.tolist(),
                physicsClientId=self.client_id
            )
            
            # Set friction and restitution
            p.changeDynamics(
                body_id,
                -1,  # Base link
                lateralFriction=friction,
                restitution=restitution,
                physicsClientId=self.client_id
            )
            
            # Validate mass for dynamic objects
            if not scene_object.is_static and mass <= 0:
                logger.error(f"Dynamic object {scene_object.object_id} has non-positive mass: {mass}")
                mass = 1.0  # Default mass
                p.changeDynamics(body_id, -1, mass=mass, physicsClientId=self.client_id)
            
            rigid_body = RigidBody(
                body_id=body_id,
                object_id=scene_object.object_id,
                label=scene_object.label,
                mass=mass,
                friction=friction,
                restitution=restitution,
                is_static=scene_object.is_static,
                position=position,
                orientation=orientation,
                linear_velocity=np.zeros(3),
                angular_velocity=np.zeros(3)
            )
            
            logger.debug(
                f"Created rigid body: object_id={scene_object.object_id}, "
                f"mass={mass:.2f}, static={scene_object.is_static}"
            )
            
            return rigid_body
            
        except Exception as e:
            logger.error(f"Failed to create rigid body: {e}")
            return None
    
    def _create_collision_shape(
        self,
        scene_object: SceneObject
    ) -> Optional[int]:
        """
        Create collision shape from scene object.
        
        Args:
            scene_object: Scene object
            
        Returns:
            Collision shape ID or None
        """
        # Use mesh if available
        if scene_object.mesh is not None:
            return self._create_mesh_collision_shape(scene_object.mesh)
        
        # Use bounding box as fallback
        if scene_object.bbox_min is not None and scene_object.bbox_max is not None:
            return self._create_box_collision_shape(
                scene_object.bbox_min,
                scene_object.bbox_max
            )
        
        logger.error(f"Cannot create collision shape for object {scene_object.object_id}")
        return None
    
    def _create_mesh_collision_shape(
        self,
        mesh: Mesh,
        simplify: bool = True
    ) -> Optional[int]:
        """
        Create collision shape from mesh.
        
        Args:
            mesh: Triangle mesh
            simplify: Whether to simplify mesh
            
        Returns:
            Collision shape ID or None
        """
        try:
            vertices = mesh.vertices.flatten().tolist()
            indices = mesh.faces.flatten().tolist()
            
            # Create convex hull (simpler and faster)
            if self.config.get('collision_meshes', {}).get('use_convex_decomposition', True):
                collision_shape_id = p.createCollisionShape(
                    shapeType=p.GEOM_MESH,
                    vertices=vertices,
                    indices=indices,
                    meshScale=[1, 1, 1],
                    physicsClientId=self.client_id
                )
            else:
                # Use full mesh (slower)
                collision_shape_id = p.createCollisionShape(
                    shapeType=p.GEOM_MESH,
                    vertices=vertices,
                    indices=indices,
                    physicsClientId=self.client_id
                )
            
            return collision_shape_id
            
        except Exception as e:
            logger.error(f"Failed to create mesh collision shape: {e}")
            return None
    
    def _create_box_collision_shape(
        self,
        bbox_min: np.ndarray,
        bbox_max: np.ndarray
    ) -> int:
        """Create box collision shape from bounding box."""
        half_extents = (bbox_max - bbox_min) / 2
        
        collision_shape_id = p.createCollisionShape(
            shapeType=p.GEOM_BOX,
            halfExtents=half_extents.tolist(),
            physicsClientId=self.client_id
        )
        
        return collision_shape_id
    
    def _get_physical_properties(
        self,
        scene_object: SceneObject
    ) -> Tuple[float, float, float]:
        """
        Get physical properties for object.
        
        Args:
            scene_object: Scene object
            
        Returns:
            Tuple of (mass, friction, restitution)
        """
        # Static objects have zero mass
        if scene_object.is_static:
            mass = 0.0
            friction = self.config.get('rigid_bodies', {}).get('static_friction', 0.7)
            restitution = self.config.get('rigid_bodies', {}).get('static_restitution', 0.1)
        else:
            # Calculate mass from volume and density
            if self.config.get('rigid_bodies', {}).get('auto_calculate_mass', True):
                volume = self._estimate_volume(scene_object)
                density = self._get_material_density(scene_object.label)
                mass = volume * density
            else:
                mass = self.config.get('rigid_bodies', {}).get('default_mass', 1.0)
            
            # Get material properties
            friction, restitution = self._get_material_properties(scene_object.label)
        
        # Ensure positive mass for dynamic objects
        if not scene_object.is_static and mass <= 0:
            mass = 1.0
        
        return mass, friction, restitution
    
    def _estimate_volume(self, scene_object: SceneObject) -> float:
        """Estimate object volume from bounding box."""
        if scene_object.bbox_min is None or scene_object.bbox_max is None:
            return 1.0
        
        dimensions = scene_object.bbox_max - scene_object.bbox_min
        volume = np.prod(dimensions)
        
        return max(volume, 0.001)  # Minimum volume
    
    def _get_material_density(self, label: str) -> float:
        """Get material density based on object label."""
        materials = self.config.get('materials', {})
        
        # Simple heuristic based on label
        if 'wood' in label.lower() or 'chair' in label.lower() or 'table' in label.lower():
            return materials.get('wood', {}).get('density', 600.0)
        elif 'metal' in label.lower():
            return materials.get('metal', {}).get('density', 7850.0)
        elif 'plastic' in label.lower():
            return materials.get('plastic', {}).get('density', 950.0)
        elif 'glass' in label.lower():
            return materials.get('glass', {}).get('density', 2500.0)
        else:
            return self.config.get('rigid_bodies', {}).get('default_density', 1000.0)
    
    def _get_material_properties(self, label: str) -> Tuple[float, float]:
        """Get friction and restitution based on object label."""
        materials = self.config.get('materials', {})
        
        # Simple heuristic
        if 'wood' in label.lower():
            mat = materials.get('wood', {})
        elif 'metal' in label.lower():
            mat = materials.get('metal', {})
        elif 'rubber' in label.lower():
            mat = materials.get('rubber', {})
        elif 'glass' in label.lower():
            mat = materials.get('glass', {})
        else:
            mat = {}
        
        friction = mat.get('friction', self.config.get('rigid_bodies', {}).get('default_friction', 0.5))
        restitution = mat.get('restitution', self.config.get('rigid_bodies', {}).get('default_restitution', 0.3))
        
        return friction, restitution
    
    def step_simulation(self):
        """Step physics simulation forward by one time step."""
        p.stepSimulation(physicsClientId=self.client_id)
        
        # Update rigid body states
        for body in self.rigid_bodies:
            pos, orn = p.getBasePositionAndOrientation(
                body.body_id,
                physicsClientId=self.client_id
            )
            lin_vel, ang_vel = p.getBaseVelocity(
                body.body_id,
                physicsClientId=self.client_id
            )
            
            body.position = np.array(pos)
            body.orientation = np.array(orn)
            body.linear_velocity = np.array(lin_vel)
            body.angular_velocity = np.array(ang_vel)
    
    def apply_force(
        self,
        body_id: int,
        force: np.ndarray,
        position: Optional[np.ndarray] = None
    ):
        """
        Apply force to rigid body.
        
        Args:
            body_id: Body ID
            force: Force vector (3,)
            position: Position to apply force (world coordinates)
        """
        if position is None:
            p.applyExternalForce(
                body_id,
                -1,  # Base link
                force.tolist(),
                [0, 0, 0],  # Center of mass
                p.WORLD_FRAME,
                physicsClientId=self.client_id
            )
        else:
            p.applyExternalForce(
                body_id,
                -1,
                force.tolist(),
                position.tolist(),
                p.WORLD_FRAME,
                physicsClientId=self.client_id
            )
    
    def apply_torque(self, body_id: int, torque: np.ndarray):
        """Apply torque to rigid body."""
        p.applyExternalTorque(
            body_id,
            -1,
            torque.tolist(),
            p.WORLD_FRAME,
            physicsClientId=self.client_id
        )
    
    def get_contact_points(self) -> List[Dict]:
        """Get all contact points in the simulation."""
        contacts = p.getContactPoints(physicsClientId=self.client_id)
        
        contact_list = []
        for contact in contacts:
            contact_list.append({
                'body_a': contact[1],
                'body_b': contact[2],
                'position': np.array(contact[5]),
                'normal': np.array(contact[7]),
                'distance': contact[8],
                'force': contact[9]
            })
        
        return contact_list


# Add PyBullet to requirements
def add_pybullet_dependency():
    """Helper to document PyBullet dependency."""
    return "pybullet>=3.2.5"
