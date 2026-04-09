import { Gaussian3D } from './gaussian_renderer';

export interface HybridSceneData {
  objects: HybridSceneObject[];
  cameras: CameraData[];
  globalBounds: {
    min: [number, number, number];
    max: [number, number, number];
  };
}

export interface HybridSceneObject {
  objectId: number;
  label: string;
  representationType: 'staticGaussian' | 'dynamicGaussian' | 'mesh';
  staticRep?: {
    gaussians: Gaussian3D[];
    bounds: {
      min: [number, number, number];
      max: [number, number, number];
    };
  };
  dynamicRep?: {
    gaussians: Gaussian3D[];
    timeSteps: number[];
    velocities: [number, number, number][];
  };
  meshRep?: {
    vertices: [number, number, number][];
    faces: [number, number, number][];
    normals: [number, number, number][];
    uvCoords?: [number, number][];
    texture?: string; // Base64 or URL
  };
  isEditable: boolean;
}

export interface CameraData {
  intrinsics: {
    focalLength: [number, number];
    principalPoint: [number, number];
    distortion: number[];
  };
  extrinsics: {
    rotation: number[]; // 3x3 matrix
    translation: [number, number, number];
  };
}

export class SceneLoader {
  async loadFromURL(url: string): Promise<HybridSceneData> {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to load scene from ${url}: ${response.statusText}`);
    }
    return await response.json();
  }

  async loadFromMinIO(
    minioEndpoint: string,
    bucket: string,
    jobId: string
  ): Promise<HybridSceneData> {
    const url = `${minioEndpoint}/${bucket}/exports/${jobId}/hybrid_scene.json`;
    return this.loadFromURL(url);
  }

  parseGaussianData(data: any): Gaussian3D[] {
    if (!Array.isArray(data)) {
      throw new Error('Invalid Gaussian data format');
    }

    return data.map((g: any) => ({
      position: g.position || [0, 0, 0],
      scale: g.scale || [1, 1, 1],
      rotation: g.rotation || [0, 0, 0, 1],
      color: g.color || [1, 1, 1, 1],
      opacity: g.opacity !== undefined ? g.opacity : 1.0
    }));
  }

  validateSceneData(data: HybridSceneData): boolean {
    if (!data.objects || !Array.isArray(data.objects)) {
      console.error('Invalid scene data: missing objects array');
      return false;
    }

    if (!data.globalBounds || !data.globalBounds.min || !data.globalBounds.max) {
      console.error('Invalid scene data: missing global bounds');
      return false;
    }

    for (const obj of data.objects) {
      if (!obj.representationType) {
        console.error(`Object ${obj.objectId} missing representation type`);
        return false;
      }

      switch (obj.representationType) {
        case 'staticGaussian':
          if (!obj.staticRep || !obj.staticRep.gaussians) {
            console.error(`Object ${obj.objectId} missing static Gaussian data`);
            return false;
          }
          break;
        case 'dynamicGaussian':
          if (!obj.dynamicRep || !obj.dynamicRep.gaussians) {
            console.error(`Object ${obj.objectId} missing dynamic Gaussian data`);
            return false;
          }
          break;
        case 'mesh':
          if (!obj.meshRep || !obj.meshRep.vertices || !obj.meshRep.faces) {
            console.error(`Object ${obj.objectId} missing mesh data`);
            return false;
          }
          break;
      }
    }

    return true;
  }
}
