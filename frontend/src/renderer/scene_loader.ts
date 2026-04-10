import { Scene } from '@babylonjs/core';
import { GaussianRenderer, Gaussian3D } from './gaussian_renderer';
import { MeshRenderer } from './mesh_renderer';

export interface SceneData {
  job_id: string;
  cameras: CameraData[];
  images: ImageData[];
  points: Point3D[];
  num_cameras: number;
  num_images: number;
  num_points: number;
}

export interface CameraData {
  camera_id: number;
  model_id: number;
  width: number;
  height: number;
  params: number[]; // [fx, fy, cx, cy] for PINHOLE model
}

export interface ImageData {
  image_id: number;
  qvec: number[]; // Quaternion [qw, qx, qy, qz]
  tvec: number[]; // Translation [tx, ty, tz]
  camera_id: number;
  name: string;
}

export interface Point3D {
  point_id: number;
  xyz: number[];
  rgb: number[];
  error: number;
}

export interface GaussianData {
  job_id: string;
  gaussians: Gaussian3D[];
  num_gaussians: number;
}

export class SceneLoader {
  private scene: Scene;
  private gaussianRenderer: GaussianRenderer;
  private meshRenderer: MeshRenderer;

  constructor(
    scene: Scene,
    gaussianRenderer: GaussianRenderer,
    meshRenderer: MeshRenderer
  ) {
    this.scene = scene;
    this.gaussianRenderer = gaussianRenderer;
    this.meshRenderer = meshRenderer;
  }

  async loadFromAPI(apiBaseUrl: string, jobId: string): Promise<void> {
    try {
      // Fetch Gaussian splat data from backend
      const response = await fetch(`${apiBaseUrl}/reconstruction/${jobId}/points`);
      
      if (!response.ok) {
        throw new Error(`Failed to load scene: ${response.statusText}`);
      }

      const data: GaussianData = await response.json();
      
      console.log(`Loading ${data.num_gaussians} Gaussian splats for job ${jobId}`);
      
      // Load Gaussians into renderer
      this.gaussianRenderer.loadGaussians(data.gaussians);
      
      return;
    } catch (error) {
      console.error('Failed to load scene from API:', error);
      throw error;
    }
  }

  async loadSceneData(apiBaseUrl: string, jobId: string): Promise<SceneData> {
    try {
      const response = await fetch(`${apiBaseUrl}/reconstruction/${jobId}/scene`);
      
      if (!response.ok) {
        throw new Error(`Failed to load scene data: ${response.statusText}`);
      }

      const data: SceneData = await response.json();
      
      console.log(`Loaded scene data: ${data.num_cameras} cameras, ${data.num_images} images, ${data.num_points} points`);
      
      return data;
    } catch (error) {
      console.error('Failed to load scene data:', error);
      throw error;
    }
  }

  async loadCameras(apiBaseUrl: string, jobId: string): Promise<{ cameras: CameraData[], images: ImageData[] }> {
    try {
      const response = await fetch(`${apiBaseUrl}/reconstruction/${jobId}/cameras`);
      
      if (!response.ok) {
        throw new Error(`Failed to load cameras: ${response.statusText}`);
      }

      const data = await response.json();
      
      console.log(`Loaded ${data.cameras.length} cameras and ${data.images.length} images`);
      
      return data;
    } catch (error) {
      console.error('Failed to load cameras:', error);
      throw error;
    }
  }

  convertPointsToGaussians(points: Point3D[]): Gaussian3D[] {
    return points.map(point => ({
      position: point.xyz as [number, number, number],
      scale: [0.02, 0.02, 0.02], // Small uniform scale
      rotation: [0, 0, 0, 1], // Identity quaternion
      color: [...point.rgb, 1.0] as [number, number, number, number], // Add alpha
      opacity: 0.9
    }));
  }

  parseGaussianData(data: any): Gaussian3D[] {
    if (!Array.isArray(data)) {
      throw new Error('Invalid Gaussian data format');
    }

    return data.map((g: any) => ({
      position: g.position || [0, 0, 0],
      scale: g.scale || [0.02, 0.02, 0.02],
      rotation: g.rotation || [0, 0, 0, 1],
      color: g.color || [1, 1, 1, 1],
      opacity: g.opacity !== undefined ? g.opacity : 0.9
    }));
  }

  async downloadPLY(apiBaseUrl: string, jobId: string): Promise<Blob> {
    try {
      const response = await fetch(`${apiBaseUrl}/reconstruction/${jobId}/download/ply`);
      
      if (!response.ok) {
        throw new Error(`Failed to download PLY: ${response.statusText}`);
      }

      return await response.blob();
    } catch (error) {
      console.error('Failed to download PLY:', error);
      throw error;
    }
  }

  clear(): void {
    // Clear all loaded data
    this.gaussianRenderer.loadGaussians([]);
  }
}
