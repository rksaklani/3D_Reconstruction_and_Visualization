import {
  Scene,
  Mesh,
  VertexData,
  Vector3,
  PBRMaterial,
  Texture,
  Color3
} from '@babylonjs/core';
import { HybridSceneObject } from './scene_loader';

export interface PhysicsState {
  objectId: number;
  position: [number, number, number];
  rotation: [number, number, number, number]; // Quaternion
  velocity: [number, number, number];
  angularVelocity: [number, number, number];
}

export class MeshRenderer {
  private scene: Scene;
  private meshes: Map<number, Mesh> = new Map();

  constructor(scene: Scene) {
    this.scene = scene;
  }

  loadMesh(obj: HybridSceneObject): Mesh | null {
    if (!obj.meshRep) {
      console.warn(`Object ${obj.objectId} has no mesh representation`);
      return null;
    }

    const mesh = new Mesh(`mesh_${obj.objectId}`, this.scene);
    
    // Create vertex data
    const vertexData = new VertexData();
    
    // Flatten vertices
    const positions: number[] = [];
    for (const v of obj.meshRep.vertices) {
      positions.push(v[0], v[1], v[2]);
    }
    vertexData.positions = positions;

    // Flatten indices
    const indices: number[] = [];
    for (const f of obj.meshRep.faces) {
      indices.push(f[0], f[1], f[2]);
    }
    vertexData.indices = indices;

    // Flatten normals
    if (obj.meshRep.normals && obj.meshRep.normals.length > 0) {
      const normals: number[] = [];
      for (const n of obj.meshRep.normals) {
        normals.push(n[0], n[1], n[2]);
      }
      vertexData.normals = normals;
    } else {
      // Compute normals if not provided
      VertexData.ComputeNormals(positions, indices, vertexData.normals || []);
    }

    // UV coordinates
    if (obj.meshRep.uvCoords && obj.meshRep.uvCoords.length > 0) {
      const uvs: number[] = [];
      for (const uv of obj.meshRep.uvCoords) {
        uvs.push(uv[0], uv[1]);
      }
      vertexData.uvs = uvs;
    }

    vertexData.applyToMesh(mesh);

    // Create PBR material
    const material = new PBRMaterial(`material_${obj.objectId}`, this.scene);
    material.metallic = 0.0;
    material.roughness = 0.8;
    material.albedoColor = new Color3(0.8, 0.8, 0.8);

    // Load texture if available
    if (obj.meshRep.texture) {
      try {
        material.albedoTexture = new Texture(obj.meshRep.texture, this.scene);
      } catch (error) {
        console.warn(`Failed to load texture for object ${obj.objectId}:`, error);
      }
    }

    mesh.material = material;
    mesh.metadata = { objectId: obj.objectId, label: obj.label };

    this.meshes.set(obj.objectId, mesh);
    return mesh;
  }

  updatePhysicsState(state: PhysicsState): void {
    const mesh = this.meshes.get(state.objectId);
    if (!mesh) {
      console.warn(`Mesh not found for object ${state.objectId}`);
      return;
    }

    // Update position
    mesh.position = new Vector3(state.position[0], state.position[1], state.position[2]);

    // Update rotation from quaternion
    const q = state.rotation;
    mesh.rotationQuaternion = new BABYLON.Quaternion(q[0], q[1], q[2], q[3]);
  }

  updatePhysicsStates(states: PhysicsState[]): void {
    for (const state of states) {
      this.updatePhysicsState(state);
    }
  }

  getMesh(objectId: number): Mesh | undefined {
    return this.meshes.get(objectId);
  }

  dispose(): void {
    for (const mesh of this.meshes.values()) {
      mesh.dispose();
    }
    this.meshes.clear();
  }
}
