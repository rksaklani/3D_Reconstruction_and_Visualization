import {
  Engine,
  Scene,
  ArcRotateCamera,
  HemisphericLight,
  Vector3,
  Color4
} from '@babylonjs/core';

export interface SceneConfig {
  clearColor?: Color4;
  ambientColor?: Color4;
  enablePhysics?: boolean;
}

export class BabylonSceneManager {
  private engine: Engine;
  private scene: Scene;
  private camera: ArcRotateCamera;
  private light: HemisphericLight;

  constructor(canvas: HTMLCanvasElement, config: SceneConfig = {}) {
    // Initialize Babylon.js engine
    this.engine = new Engine(canvas, true, {
      preserveDrawingBuffer: true,
      stencil: true
    });

    // Create scene
    this.scene = new Scene(this.engine);
    this.scene.clearColor = config.clearColor || new Color4(0.1, 0.1, 0.15, 1.0);
    if (config.ambientColor) {
      this.scene.ambientColor = config.ambientColor.toColor3();
    }

    // Setup camera
    this.camera = new ArcRotateCamera(
      'camera',
      -Math.PI / 2,
      Math.PI / 3,
      10,
      Vector3.Zero(),
      this.scene
    );
    this.camera.attachControl(canvas, true);
    this.camera.minZ = 0.1;
    this.camera.maxZ = 1000;

    // Setup lighting
    this.light = new HemisphericLight('light', new Vector3(0, 1, 0), this.scene);
    this.light.intensity = 0.7;

    // Start render loop
    this.engine.runRenderLoop(() => {
      this.scene.render();
    });

    // Handle window resize
    window.addEventListener('resize', () => {
      this.engine.resize();
    });
  }

  getScene(): Scene {
    return this.scene;
  }

  getCamera(): ArcRotateCamera {
    return this.camera;
  }

  getEngine(): Engine {
    return this.engine;
  }

  dispose(): void {
    this.scene.dispose();
    this.engine.dispose();
  }
}
