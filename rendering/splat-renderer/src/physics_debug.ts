import {
  Scene,
  Mesh,
  MeshBuilder,
  StandardMaterial,
  Color3,
  Vector3,
  LinesMesh
} from '@babylonjs/core';
import { PhysicsObjectData } from './physics_sync';

export interface CollisionMeshData {
  objectId: number;
  vertices: [number, number, number][];
  faces: [number, number, number][];
}

export interface ContactPoint {
  position: [number, number, number];
  normal: [number, number, number];
  penetrationDepth: number;
}

export class PhysicsDebugVisualizer {
  private scene: Scene;
  private collisionMeshes: Map<number, Mesh> = new Map();
  private contactPointMeshes: Mesh[] = [];
  private contactNormalLines: LinesMesh[] = [];
  private enabled: boolean = false;

  constructor(scene: Scene) {
    this.scene = scene;
  }

  setEnabled(enabled: boolean): void {
    this.enabled = enabled;
    
    if (!enabled) {
      this.hideAll();
    } else {
      this.showAll();
    }
  }

  isEnabled(): boolean {
    return this.enabled;
  }

  loadCollisionMesh(data: CollisionMeshData): void {
    // Remove existing collision mesh if any
    const existing = this.collisionMeshes.get(data.objectId);
    if (existing) {
      existing.dispose();
    }

    // Create wireframe mesh
    const mesh = new Mesh(`collision_${data.objectId}`, this.scene);
    
    const positions: number[] = [];
    for (const v of data.vertices) {
      positions.push(v[0], v[1], v[2]);
    }

    const indices: number[] = [];
    for (const f of data.faces) {
      indices.push(f[0], f[1], f[2]);
    }

    const vertexData = new BABYLON.VertexData();
    vertexData.positions = positions;
    vertexData.indices = indices;
    vertexData.applyToMesh(mesh);

    // Create wireframe material
    const material = new StandardMaterial(`collision_mat_${data.objectId}`, this.scene);
    material.wireframe = true;
    material.emissiveColor = new Color3(0, 1, 0); // Green wireframe
    material.alpha = 0.5;

    mesh.material = material;
    mesh.isVisible = this.enabled;

    this.collisionMeshes.set(data.objectId, mesh);
  }

  updateCollisionMeshTransform(objectId: number, position: [number, number, number], rotation: [number, number, number, number]): void {
    const mesh = this.collisionMeshes.get(objectId);
    if (!mesh) return;

    mesh.position = new Vector3(position[0], position[1], position[2]);
    mesh.rotationQuaternion = new BABYLON.Quaternion(rotation[0], rotation[1], rotation[2], rotation[3]);
  }

  visualizeContactPoints(contacts: ContactPoint[]): void {
    // Clear existing visualizations
    this.clearContactVisualizations();

    if (!this.enabled) return;

    for (const contact of contacts) {
      // Create sphere at contact point
      const sphere = MeshBuilder.CreateSphere(
        'contact_point',
        { diameter: 0.1 },
        this.scene
      );
      sphere.position = new Vector3(contact.position[0], contact.position[1], contact.position[2]);

      const material = new StandardMaterial('contact_mat', this.scene);
      material.emissiveColor = new Color3(1, 0, 0); // Red
      sphere.material = material;

      this.contactPointMeshes.push(sphere);

      // Create line for contact normal
      const start = new Vector3(contact.position[0], contact.position[1], contact.position[2]);
      const end = start.add(
        new Vector3(contact.normal[0], contact.normal[1], contact.normal[2]).scale(0.5)
      );

      const line = MeshBuilder.CreateLines(
        'contact_normal',
        { points: [start, end] },
        this.scene
      );
      line.color = new Color3(1, 1, 0); // Yellow

      this.contactNormalLines.push(line);
    }
  }

  private clearContactVisualizations(): void {
    for (const mesh of this.contactPointMeshes) {
      mesh.dispose();
    }
    this.contactPointMeshes = [];

    for (const line of this.contactNormalLines) {
      line.dispose();
    }
    this.contactNormalLines = [];
  }

  private hideAll(): void {
    for (const mesh of this.collisionMeshes.values()) {
      mesh.isVisible = false;
    }
    this.clearContactVisualizations();
  }

  private showAll(): void {
    for (const mesh of this.collisionMeshes.values()) {
      mesh.isVisible = true;
    }
  }

  dispose(): void {
    for (const mesh of this.collisionMeshes.values()) {
      mesh.dispose();
    }
    this.collisionMeshes.clear();
    this.clearContactVisualizations();
  }
}
