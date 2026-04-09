import {
  Scene,
  Mesh,
  Vector3,
  Ray,
  PointerEventTypes,
  PointerInfo,
  AbstractMesh
} from '@babylonjs/core';
import { PhysicsSynchronizer } from './physics_sync';

export type ObjectPickCallback = (objectId: number, label: string) => void;
export type ObjectDragCallback = (objectId: number, delta: Vector3) => void;

export class InteractionSystem {
  private scene: Scene;
  private physicsSynchronizer: PhysicsSynchronizer;
  private pickCallback: ObjectPickCallback | null = null;
  private dragCallback: ObjectDragCallback | null = null;
  private isDragging: boolean = false;
  private draggedObjectId: number | null = null;
  private lastPointerPosition: Vector3 | null = null;

  constructor(scene: Scene, physicsSynchronizer: PhysicsSynchronizer) {
    this.scene = scene;
    this.physicsSynchronizer = physicsSynchronizer;
    this.setupPointerObservable();
  }

  private setupPointerObservable(): void {
    this.scene.onPointerObservable.add((pointerInfo: PointerInfo) => {
      switch (pointerInfo.type) {
        case PointerEventTypes.POINTERDOWN:
          this.handlePointerDown(pointerInfo);
          break;
        case PointerEventTypes.POINTERMOVE:
          this.handlePointerMove(pointerInfo);
          break;
        case PointerEventTypes.POINTERUP:
          this.handlePointerUp(pointerInfo);
          break;
      }
    });
  }

  private handlePointerDown(pointerInfo: PointerInfo): void {
    const pickResult = this.scene.pick(
      this.scene.pointerX,
      this.scene.pointerY,
      (mesh) => mesh.metadata && mesh.metadata.objectId !== undefined
    );

    if (pickResult && pickResult.hit && pickResult.pickedMesh) {
      const mesh = pickResult.pickedMesh;
      const objectId = mesh.metadata.objectId;
      const label = mesh.metadata.label || 'Unknown';

      // Trigger pick callback
      if (this.pickCallback) {
        this.pickCallback(objectId, label);
      }

      // Start dragging
      this.isDragging = true;
      this.draggedObjectId = objectId;
      this.lastPointerPosition = pickResult.pickedPoint;
    }
  }

  private handlePointerMove(pointerInfo: PointerInfo): void {
    if (!this.isDragging || this.draggedObjectId === null || !this.lastPointerPosition) {
      return;
    }

    const pickResult = this.scene.pick(
      this.scene.pointerX,
      this.scene.pointerY
    );

    if (pickResult && pickResult.hit && pickResult.pickedPoint) {
      const delta = pickResult.pickedPoint.subtract(this.lastPointerPosition);
      
      // Apply force based on drag delta
      const force: [number, number, number] = [delta.x * 10, delta.y * 10, delta.z * 10];
      this.physicsSynchronizer.applyForce(this.draggedObjectId, force);

      // Trigger drag callback
      if (this.dragCallback) {
        this.dragCallback(this.draggedObjectId, delta);
      }

      this.lastPointerPosition = pickResult.pickedPoint;
    }
  }

  private handlePointerUp(pointerInfo: PointerInfo): void {
    this.isDragging = false;
    this.draggedObjectId = null;
    this.lastPointerPosition = null;
  }

  onObjectPicked(callback: ObjectPickCallback): void {
    this.pickCallback = callback;
  }

  onObjectDragged(callback: ObjectDragCallback): void {
    this.dragCallback = callback;
  }

  async applyForceToObject(objectId: number, force: Vector3): Promise<void> {
    await this.physicsSynchronizer.applyForce(objectId, [force.x, force.y, force.z]);
  }

  async applyImpulseToObject(objectId: number, impulse: Vector3): Promise<void> {
    await this.physicsSynchronizer.applyImpulse(objectId, [impulse.x, impulse.y, impulse.z]);
  }

  pickObjectAtScreenPosition(x: number, y: number): { objectId: number; label: string } | null {
    const pickResult = this.scene.pick(
      x,
      y,
      (mesh) => mesh.metadata && mesh.metadata.objectId !== undefined
    );

    if (pickResult && pickResult.hit && pickResult.pickedMesh) {
      const mesh = pickResult.pickedMesh;
      return {
        objectId: mesh.metadata.objectId,
        label: mesh.metadata.label || 'Unknown'
      };
    }

    return null;
  }

  dispose(): void {
    this.pickCallback = null;
    this.dragCallback = null;
  }
}
