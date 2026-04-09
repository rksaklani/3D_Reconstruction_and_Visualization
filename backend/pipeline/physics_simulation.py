"""Physics simulation and collision resolution."""

import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

try:
    import pybullet as p
    PYBULLET_AVAILABLE = True
except ImportError:
    PYBULLET_AVAILABLE = False

from backend.pipeline.physics_engine import PhysicsEngine, PhysicsScene, RigidBody

logger = logging.getLogger(__name__)


class PhysicsSimulator:
    """Physics simulator with collision detection and resolution."""
    
    def __init__(
        self,
        physics_engine: PhysicsEngine,
        config: Optional[Dict] = None
    ):
        """
        Initialize physics simulator.
        
        Args:
            physics_engine: Physics engine instance
            config: Configuration dictionary
        """
        self.engine = physics_engine
        self.config = config or {}
        self.simulation_time = 0.0
    
    def simulate_step(
        self,
        physics_scene: PhysicsScene
    ) -> Dict:
        """
        Simulate one physics step.
        
        Args:
            physics_scene: Physics scene
            
        Returns:
            Simulation statistics
        """
        # Step simulation
        self.engine.step_simulation()
        self.simulation_time += physics_scene.time_step
        
        # Detect collisions
        contacts = self.engine.get_contact_points()
        
        # Validate simulation
        is_valid, error_msg = self.validate_simulation(physics_scene)
        
        if not is_valid:
            logger.warning(f"Simulation validation failed: {error_msg}")
        
        stats = {
            'time': self.simulation_time,
            'num_contacts': len(contacts),
            'is_valid': is_valid,
            'error_message': error_msg if not is_valid else None
        }
        
        return stats
    
    def validate_simulation(
        self,
        physics_scene: PhysicsScene
    ) -> Tuple[bool, str]:
        """
        Validate physics simulation state.
        
        Args:
            physics_scene: Physics scene
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for NaN/Inf in positions and velocities
        for body in physics_scene.rigid_bodies:
            if not np.all(np.isfinite(body.position)):
                return False, f"Body {body.body_id} has invalid position"
            
            if not np.all(np.isfinite(body.linear_velocity)):
                return False, f"Body {body.body_id} has invalid velocity"
            
            if not np.all(np.isfinite(body.angular_velocity)):
                return False, f"Body {body.body_id} has invalid angular velocity"
        
        # Check penetration depths
        contacts = self.engine.get_contact_points()
        max_penetration = 0.0
        
        for contact in contacts:
            penetration = -contact['distance']  # Negative distance = penetration
            if penetration > max_penetration:
                max_penetration = penetration
        
        penetration_tolerance = self.config.get('simulation', {}).get(
            'max_penetration_recovery', 0.2
        )
        
        if max_penetration > penetration_tolerance:
            return False, f"Excessive penetration: {max_penetration:.4f} > {penetration_tolerance}"
        
        # Check static objects haven't moved
        for body in physics_scene.rigid_bodies:
            if body.is_static:
                # Static objects should have zero velocity
                if np.linalg.norm(body.linear_velocity) > 1e-6:
                    return False, f"Static body {body.body_id} is moving"
                
                if np.linalg.norm(body.angular_velocity) > 1e-6:
                    return False, f"Static body {body.body_id} is rotating"
        
        return True, "Valid"
    
    def compute_energy(
        self,
        physics_scene: PhysicsScene
    ) -> Dict[str, float]:
        """
        Compute total mechanical energy.
        
        Args:
            physics_scene: Physics scene
            
        Returns:
            Dictionary with kinetic, potential, and total energy
        """
        kinetic_energy = 0.0
        potential_energy = 0.0
        
        gravity = physics_scene.gravity
        g_magnitude = np.linalg.norm(gravity)
        
        for body in physics_scene.rigid_bodies:
            if body.is_static or body.mass <= 0:
                continue
            
            # Kinetic energy: 0.5 * m * v^2
            v_squared = np.dot(body.linear_velocity, body.linear_velocity)
            kinetic_energy += 0.5 * body.mass * v_squared
            
            # Rotational kinetic energy (simplified, assumes sphere)
            omega_squared = np.dot(body.angular_velocity, body.angular_velocity)
            I = 0.4 * body.mass * 1.0  # Moment of inertia (simplified)
            kinetic_energy += 0.5 * I * omega_squared
            
            # Potential energy: m * g * h
            height = body.position[1]  # Assuming y is up
            potential_energy += body.mass * g_magnitude * height
        
        total_energy = kinetic_energy + potential_energy
        
        return {
            'kinetic': kinetic_energy,
            'potential': potential_energy,
            'total': total_energy
        }
    
    def check_energy_conservation(
        self,
        initial_energy: float,
        current_energy: float,
        tolerance: float = 0.1
    ) -> bool:
        """
        Check if energy is conserved within tolerance.
        
        Args:
            initial_energy: Initial total energy
            current_energy: Current total energy
            tolerance: Relative tolerance (0.1 = 10%)
            
        Returns:
            True if energy is conserved
        """
        if initial_energy == 0:
            return True
        
        relative_change = abs(current_energy - initial_energy) / abs(initial_energy)
        
        is_conserved = relative_change <= tolerance
        
        if not is_conserved:
            logger.warning(
                f"Energy not conserved: {relative_change*100:.2f}% change "
                f"(initial={initial_energy:.2f}, current={current_energy:.2f})"
            )
        
        return is_conserved
    
    def resolve_collisions(
        self,
        physics_scene: PhysicsScene
    ):
        """
        Resolve collisions and apply impulses.
        
        Note: PyBullet handles this automatically, but we can add custom logic here.
        
        Args:
            physics_scene: Physics scene
        """
        contacts = self.engine.get_contact_points()
        
        for contact in contacts:
            body_a_id = contact['body_a']
            body_b_id = contact['body_b']
            
            # Find rigid bodies
            body_a = None
            body_b = None
            
            for body in physics_scene.rigid_bodies:
                if body.body_id == body_a_id:
                    body_a = body
                if body.body_id == body_b_id:
                    body_b = body
            
            if body_a is None or body_b is None:
                continue
            
            # Ensure static objects remain stationary
            if body_a.is_static:
                # Reset velocity if somehow moving
                if np.linalg.norm(body_a.linear_velocity) > 1e-6:
                    p.resetBaseVelocity(
                        body_a.body_id,
                        [0, 0, 0],
                        [0, 0, 0],
                        physicsClientId=self.engine.client_id
                    )
            
            if body_b.is_static:
                if np.linalg.norm(body_b.linear_velocity) > 1e-6:
                    p.resetBaseVelocity(
                        body_b.body_id,
                        [0, 0, 0],
                        [0, 0, 0],
                        physicsClientId=self.engine.client_id
                    )
    
    def handle_instability(
        self,
        physics_scene: PhysicsScene,
        last_stable_state: Optional[Dict] = None
    ) -> bool:
        """
        Handle physics instability.
        
        Args:
            physics_scene: Physics scene
            last_stable_state: Last known stable state
            
        Returns:
            True if recovery successful
        """
        logger.warning("Physics instability detected, attempting recovery")
        
        # Check for NaN/Inf values
        has_nan = False
        
        for body in physics_scene.rigid_bodies:
            if not np.all(np.isfinite(body.position)):
                has_nan = True
                logger.error(f"Body {body.body_id} has NaN/Inf position")
            
            if not np.all(np.isfinite(body.linear_velocity)):
                has_nan = True
                logger.error(f"Body {body.body_id} has NaN/Inf velocity")
        
        if has_nan:
            if last_stable_state is not None:
                logger.info("Restoring from last stable state")
                self._restore_state(physics_scene, last_stable_state)
                return True
            else:
                logger.error("No stable state to restore from")
                return False
        
        # Apply velocity damping
        damping_factor = 0.5
        logger.info(f"Applying velocity damping: {damping_factor}")
        
        for body in physics_scene.rigid_bodies:
            if not body.is_static:
                damped_velocity = body.linear_velocity * damping_factor
                damped_angular = body.angular_velocity * damping_factor
                
                p.resetBaseVelocity(
                    body.body_id,
                    damped_velocity.tolist(),
                    damped_angular.tolist(),
                    physicsClientId=self.engine.client_id
                )
        
        return True
    
    def _restore_state(
        self,
        physics_scene: PhysicsScene,
        state: Dict
    ):
        """Restore physics state from saved state."""
        for body in physics_scene.rigid_bodies:
            body_state = state.get(body.body_id)
            
            if body_state is not None:
                p.resetBasePositionAndOrientation(
                    body.body_id,
                    body_state['position'].tolist(),
                    body_state['orientation'].tolist(),
                    physicsClientId=self.engine.client_id
                )
                
                p.resetBaseVelocity(
                    body.body_id,
                    body_state['linear_velocity'].tolist(),
                    body_state['angular_velocity'].tolist(),
                    physicsClientId=self.engine.client_id
                )
    
    def save_state(
        self,
        physics_scene: PhysicsScene
    ) -> Dict:
        """Save current physics state."""
        state = {}
        
        for body in physics_scene.rigid_bodies:
            state[body.body_id] = {
                'position': body.position.copy(),
                'orientation': body.orientation.copy(),
                'linear_velocity': body.linear_velocity.copy(),
                'angular_velocity': body.angular_velocity.copy()
            }
        
        return state
    
    def run_simulation(
        self,
        physics_scene: PhysicsScene,
        duration: float,
        callback: Optional[callable] = None
    ) -> List[Dict]:
        """
        Run simulation for specified duration.
        
        Args:
            physics_scene: Physics scene
            duration: Simulation duration in seconds
            callback: Optional callback function called each step
            
        Returns:
            List of simulation statistics for each step
        """
        num_steps = int(duration / physics_scene.time_step)
        stats_history = []
        
        # Compute initial energy
        initial_energy = self.compute_energy(physics_scene)['total']
        last_stable_state = self.save_state(physics_scene)
        
        logger.info(f"Running simulation for {duration}s ({num_steps} steps)")
        
        for step in range(num_steps):
            # Simulate step
            stats = self.simulate_step(physics_scene)
            stats_history.append(stats)
            
            # Check energy conservation (every 60 steps = 1 second)
            if step % 60 == 0:
                current_energy = self.compute_energy(physics_scene)['total']
                energy_conserved = self.check_energy_conservation(
                    initial_energy,
                    current_energy,
                    tolerance=0.2  # 20% tolerance
                )
                
                if not energy_conserved:
                    logger.warning(f"Energy conservation violated at step {step}")
            
            # Handle instability
            if not stats['is_valid']:
                success = self.handle_instability(physics_scene, last_stable_state)
                if not success:
                    logger.error("Failed to recover from instability, stopping simulation")
                    break
            else:
                # Save stable state
                if step % 10 == 0:
                    last_stable_state = self.save_state(physics_scene)
            
            # Resolve collisions
            self.resolve_collisions(physics_scene)
            
            # Callback
            if callback is not None:
                callback(step, physics_scene, stats)
        
        logger.info(f"Simulation complete: {len(stats_history)} steps")
        
        return stats_history
