import {
  Scene,
  ArcRotateCamera,
  UniversalCamera,
  Vector3,
  Animation
} from '@babylonjs/core';

export type CameraMode = 'orbit' | 'fly';

export class CameraController {
  private scene: Scene;
  private orbitCamera: ArcRotateCamera;
  private flyCamera: UniversalCamera;
  private currentMode: CameraMode = 'orbit';

  constructor(scene: Scene, canvas: HTMLCanvasElement) {
    this.scene = scene;

    // Create orbit camera
    this.orbitCamera = new ArcRotateCamera(
      'orbitCamera',
      -Math.PI / 2,
      Math.PI / 3,
      10,
      Vector3.Zero(),
      scene
    );
    this.orbitCamera.attachControl(canvas, true);
    this.orbitCamera.minZ = 0.1;
    this.orbitCamera.maxZ = 1000;
    this.orbitCamera.wheelPrecision = 50;
    this.orbitCamera.panningSensibility = 100;

    // Create fly camera
    this.flyCamera = new UniversalCamera(
      'flyCamera',
      new Vector3(0, 5, -10),
      scene
    );
    this.flyCamera.minZ = 0.1;
    this.flyCamera.maxZ = 1000;
    this.flyCamera.speed = 0.5;
    this.flyCamera.angularSensibility = 1000;

    // Set orbit camera as active by default
    scene.activeCamera = this.orbitCamera;
  }

  setMode(mode: CameraMode): void {
    if (mode === this.currentMode) return;

    this.currentMode = mode;

    if (mode === 'orbit') {
      this.scene.activeCamera = this.orbitCamera;
      this.flyCamera.detachControl();
    } else {
      this.scene.activeCamera = this.flyCamera;
      this.orbitCamera.detachControl();
      this.flyCamera.attachControl(this.scene.getEngine().getRenderingCanvas()!, true);
    }
  }

  getMode(): CameraMode {
    return this.currentMode;
  }

  resetCamera(): void {
    if (this.currentMode === 'orbit') {
      this.orbitCamera.alpha = -Math.PI / 2;
      this.orbitCamera.beta = Math.PI / 3;
      this.orbitCamera.radius = 10;
      this.orbitCamera.target = Vector3.Zero();
    } else {
      this.flyCamera.position = new Vector3(0, 5, -10);
      this.flyCamera.setTarget(Vector3.Zero());
    }
  }

  focusOnPoint(point: Vector3, distance: number = 10): void {
    if (this.currentMode === 'orbit') {
      // Animate to new target
      Animation.CreateAndStartAnimation(
        'cameraTarget',
        this.orbitCamera,
        'target',
        30,
        30,
        this.orbitCamera.target,
        point,
        Animation.ANIMATIONLOOPMODE_CONSTANT
      );

      Animation.CreateAndStartAnimation(
        'cameraRadius',
        this.orbitCamera,
        'radius',
        30,
        30,
        this.orbitCamera.radius,
        distance,
        Animation.ANIMATIONLOOPMODE_CONSTANT
      );
    } else {
      // Move fly camera to look at point
      const direction = point.subtract(this.flyCamera.position).normalize();
      const newPosition = point.subtract(direction.scale(distance));
      
      Animation.CreateAndStartAnimation(
        'cameraPosition',
        this.flyCamera,
        'position',
        30,
        30,
        this.flyCamera.position,
        newPosition,
        Animation.ANIMATIONLOOPMODE_CONSTANT
      );

      this.flyCamera.setTarget(point);
    }
  }

  setOrbitTarget(target: Vector3): void {
    this.orbitCamera.target = target;
  }

  setOrbitRadius(radius: number): void {
    this.orbitCamera.radius = radius;
  }

  setFlySpeed(speed: number): void {
    this.flyCamera.speed = speed;
  }

  getActiveCamera(): ArcRotateCamera | UniversalCamera {
    return this.currentMode === 'orbit' ? this.orbitCamera : this.flyCamera;
  }

  dispose(): void {
    this.orbitCamera.dispose();
    this.flyCamera.dispose();
  }
}
