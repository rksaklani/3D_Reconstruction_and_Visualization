import { Scene } from '@babylonjs/core';
import { MeshRenderer, PhysicsState } from './mesh_renderer';

export interface PhysicsSceneData {
  objects: PhysicsObjectData[];
  gravity: [number, number, number];
  timeStep: number;
}

export interface PhysicsObjectData {
  objectId: number;
  position: [number, number, number];
  rotation: [number, number, number, number];
  velocity: [number, number, number];
  angularVelocity: [number, number, number];
  mass: number;
  isStatic: boolean;
}

export class PhysicsSynchronizer {
  private scene: Scene;
  private meshRenderer: MeshRenderer;
  private physicsEndpoint: string;
  private updateInterval: number = 16; // ~60 FPS
  private intervalId: number | null = null;

  constructor(scene: Scene, meshRenderer: MeshRenderer, physicsEndpoint: string) {
    this.scene = scene;
    this.meshRenderer = meshRenderer;
    this.physicsEndpoint = physicsEndpoint;
  }

  async fetchPhysicsState(): Promise<PhysicsState[]> {
    try {
      const response = await fetch(`${this.physicsEndpoint}/state`);
      if (!response.ok) {
        throw new Error(`Physics state fetch failed: ${response.statusText}`);
      }
      const data: PhysicsSceneData = await response.json();
      return data.objects.map(obj => ({
        objectId: obj.objectId,
        position: obj.position,
        rotation: obj.rotation,
        velocity: obj.velocity,
        angularVelocity: obj.angularVelocity
      }));
    } catch (error) {
      console.error('Failed to fetch physics state:', error);
      return [];
    }
  }

  startSync(): void {
    if (this.intervalId !== null) {
      console.warn('Physics sync already running');
      return;
    }

    this.intervalId = window.setInterval(async () => {
      const states = await this.fetchPhysicsState();
      this.meshRenderer.updatePhysicsStates(states);
    }, this.updateInterval);

    console.log('Physics synchronization started');
  }

  stopSync(): void {
    if (this.intervalId !== null) {
      window.clearInterval(this.intervalId);
      this.intervalId = null;
      console.log('Physics synchronization stopped');
    }
  }

  setUpdateRate(fps: number): void {
    this.updateInterval = 1000 / fps;
    if (this.intervalId !== null) {
      this.stopSync();
      this.startSync();
    }
  }

  async applyForce(objectId: number, force: [number, number, number]): Promise<void> {
    try {
      await fetch(`${this.physicsEndpoint}/apply_force`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ objectId, force })
      });
    } catch (error) {
      console.error('Failed to apply force:', error);
    }
  }

  async applyImpulse(objectId: number, impulse: [number, number, number]): Promise<void> {
    try {
      await fetch(`${this.physicsEndpoint}/apply_impulse`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ objectId, impulse })
      });
    } catch (error) {
      console.error('Failed to apply impulse:', error);
    }
  }
}
