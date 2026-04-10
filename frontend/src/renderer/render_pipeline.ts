import { Scene } from '@babylonjs/core';
import { GaussianRenderer } from './gaussian_renderer';
import { MeshRenderer } from './mesh_renderer';
import { PhysicsDebugVisualizer } from './physics_debug';

export type RenderMode = 'photorealistic' | 'physics' | 'hybrid';
export type RenderQuality = 'low' | 'medium' | 'high';

export interface RenderConfig {
  mode: RenderMode;
  quality: RenderQuality;
  maxFPS: number;
  enableLOD: boolean;
}

export class RenderPipeline {
  private scene: Scene;
  private gaussianRenderer: GaussianRenderer;
  private meshRenderer: MeshRenderer;
  private physicsDebugVisualizer: PhysicsDebugVisualizer;
  private config: RenderConfig;

  constructor(
    scene: Scene,
    gaussianRenderer: GaussianRenderer,
    meshRenderer: MeshRenderer,
    physicsDebugVisualizer: PhysicsDebugVisualizer
  ) {
    this.scene = scene;
    this.gaussianRenderer = gaussianRenderer;
    this.meshRenderer = meshRenderer;
    this.physicsDebugVisualizer = physicsDebugVisualizer;

    // Default configuration
    this.config = {
      mode: 'photorealistic',
      quality: 'high',
      maxFPS: 60,
      enableLOD: true
    };

    this.applyConfig();
  }

  setRenderMode(mode: RenderMode): void {
    this.config.mode = mode;
    this.applyConfig();
  }

  setRenderQuality(quality: RenderQuality): void {
    this.config.quality = quality;
    this.applyQualitySettings();
  }

  setMaxFPS(fps: number): void {
    this.config.maxFPS = fps;
    const engine = this.scene.getEngine();
    
    if (fps > 0) {
      const targetFrameTime = 1000 / fps;
      let lastFrameTime = performance.now();

      engine.runRenderLoop(() => {
        const now = performance.now();
        const elapsed = now - lastFrameTime;

        if (elapsed >= targetFrameTime) {
          this.scene.render();
          lastFrameTime = now;
        }
      });
    } else {
      // Unlimited FPS
      engine.runRenderLoop(() => {
        this.scene.render();
      });
    }
  }

  setLODEnabled(enabled: boolean): void {
    this.config.enableLOD = enabled;
    // LOD implementation would go here
  }

  getConfig(): RenderConfig {
    return { ...this.config };
  }

  private applyConfig(): void {
    switch (this.config.mode) {
      case 'photorealistic':
        // Show Gaussians and meshes, hide physics debug
        this.setGaussiansVisible(true);
        this.setMeshesVisible(true);
        this.physicsDebugVisualizer.setEnabled(false);
        break;

      case 'physics':
        // Hide Gaussians and meshes, show physics debug
        this.setGaussiansVisible(false);
        this.setMeshesVisible(false);
        this.physicsDebugVisualizer.setEnabled(true);
        break;

      case 'hybrid':
        // Show everything
        this.setGaussiansVisible(true);
        this.setMeshesVisible(true);
        this.physicsDebugVisualizer.setEnabled(true);
        break;
    }
  }

  private applyQualitySettings(): void {
    const engine = this.scene.getEngine();

    switch (this.config.quality) {
      case 'low':
        engine.setHardwareScalingLevel(2.0); // Render at 50% resolution
        this.scene.particlesEnabled = false;
        this.scene.postProcessesEnabled = false;
        break;

      case 'medium':
        engine.setHardwareScalingLevel(1.5); // Render at ~67% resolution
        this.scene.particlesEnabled = true;
        this.scene.postProcessesEnabled = false;
        break;

      case 'high':
        engine.setHardwareScalingLevel(1.0); // Full resolution
        this.scene.particlesEnabled = true;
        this.scene.postProcessesEnabled = true;
        break;
    }
  }

  private setGaussiansVisible(visible: boolean): void {
    // Gaussian visibility would be controlled through the GaussianRenderer
    // This is a placeholder for the actual implementation
    console.log(`Gaussians visibility set to: ${visible}`);
  }

  private setMeshesVisible(visible: boolean): void {
    // Iterate through all meshes and set visibility
    this.scene.meshes.forEach(mesh => {
      if (mesh.metadata && mesh.metadata.objectId !== undefined) {
        mesh.isVisible = visible;
      }
    });
  }

  enableFrustumCulling(): void {
    this.scene.meshes.forEach(mesh => {
      mesh.alwaysSelectAsActiveMesh = false;
    });
  }

  disableFrustumCulling(): void {
    this.scene.meshes.forEach(mesh => {
      mesh.alwaysSelectAsActiveMesh = true;
    });
  }

  getPerformanceMetrics(): {
    fps: number;
    drawCalls: number;
    totalVertices: number;
    activeMeshes: number;
  } {
    const engine = this.scene.getEngine();
    
    return {
      fps: engine.getFps(),
      drawCalls: this.scene.getEngine().drawCalls,
      totalVertices: this.scene.getTotalVertices(),
      activeMeshes: this.scene.getActiveMeshes().length
    };
  }

  dispose(): void {
    // Cleanup if needed
  }
}
