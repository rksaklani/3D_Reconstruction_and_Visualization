import {
  Scene,
  ShaderMaterial,
  VertexBuffer,
  Buffer,
  VertexData,
  Mesh,
  Vector3,
  Color4,
  Quaternion
} from '@babylonjs/core';

export interface Gaussian3D {
  position: [number, number, number];
  scale: [number, number, number];
  rotation: [number, number, number, number]; // Quaternion [x, y, z, w]
  color: [number, number, number, number]; // RGBA
  opacity: number;
}

export class GaussianRenderer {
  private scene: Scene;
  private material: ShaderMaterial;
  private mesh: Mesh | null = null;

  constructor(scene: Scene) {
    this.scene = scene;
    this.material = this.createGaussianMaterial();
  }

  private createGaussianMaterial(): ShaderMaterial {
    const material = new ShaderMaterial(
      'gaussianMaterial',
      this.scene,
      {
        vertexSource: this.getVertexShader(),
        fragmentSource: this.getFragmentShader()
      },
      {
        attributes: ['position', 'color', 'scale', 'rotation', 'opacity'],
        uniforms: [
          'worldViewProjection',
          'world',
          'view',
          'projection',
          'cameraPosition'
        ]
      }
    );

    material.backFaceCulling = false;
    material.alphaMode = 2; // ALPHA_BLEND
    material.needDepthPrePass = true;

    return material;
  }

  private getVertexShader(): string {
    // In production, load from file
    return `
      precision highp float;
      attribute vec3 position;
      attribute vec4 color;
      attribute vec3 scale;
      attribute vec4 rotation;
      attribute float opacity;
      
      uniform mat4 worldViewProjection;
      uniform mat4 world;
      uniform mat4 view;
      uniform mat4 projection;
      
      varying vec4 vColor;
      varying float vOpacity;
      varying mat3 vCov2D;
      
      mat3 quaternionToMatrix(vec4 q) {
          float x = q.x, y = q.y, z = q.z, w = q.w;
          return mat3(
              1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - w * z), 2.0 * (x * z + w * y),
              2.0 * (x * y + w * z), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - w * x),
              2.0 * (x * z - w * y), 2.0 * (y * z + w * x), 1.0 - 2.0 * (x * x + y * y)
          );
      }
      
      void main() {
          mat3 R = quaternionToMatrix(rotation);
          mat3 S = mat3(scale.x, 0.0, 0.0, 0.0, scale.y, 0.0, 0.0, 0.0, scale.z);
          mat3 M = R * S;
          mat3 Cov3D = M * transpose(M);
          
          vec4 worldPos = world * vec4(position, 1.0);
          gl_Position = worldViewProjection * vec4(position, 1.0);
          
          float focal = projection[0][0];
          vec3 t = (view * worldPos).xyz;
          
          mat3 J = mat3(
              focal / t.z, 0.0, -(focal * t.x) / (t.z * t.z),
              0.0, focal / t.z, -(focal * t.y) / (t.z * t.z),
              0.0, 0.0, 0.0
          );
          
          mat3 W = mat3(view);
          mat3 T = W * J;
          mat3 Cov2D = transpose(T) * Cov3D * T;
          Cov2D[0][0] += 0.3;
          Cov2D[1][1] += 0.3;
          
          vCov2D = Cov2D;
          vColor = color;
          vOpacity = opacity;
          gl_PointSize = 2.0 * sqrt(max(Cov2D[0][0], Cov2D[1][1]));
      }
    `;
  }

  private getFragmentShader(): string {
    return `
      precision highp float;
      varying vec4 vColor;
      varying float vOpacity;
      varying mat3 vCov2D;
      
      void main() {
          vec2 d = gl_PointCoord * 2.0 - 1.0;
          float det = vCov2D[0][0] * vCov2D[1][1] - vCov2D[0][1] * vCov2D[1][0];
          if (det == 0.0) discard;
          
          float invDet = 1.0 / det;
          mat2 covInv = mat2(
              vCov2D[1][1] * invDet, -vCov2D[0][1] * invDet,
              -vCov2D[1][0] * invDet, vCov2D[0][0] * invDet
          );
          
          vec2 covD = covInv * d;
          float power = -0.5 * dot(d, covD);
          if (power > 0.0) discard;
          
          float alpha = min(0.99, vOpacity * exp(power));
          if (alpha < 0.01) discard;
          
          gl_FragColor = vec4(vColor.rgb, alpha);
      }
    `;
  }

  loadGaussians(gaussians: Gaussian3D[]): void {
    if (this.mesh) {
      this.mesh.dispose();
    }

    const positions: number[] = [];
    const colors: number[] = [];
    const scales: number[] = [];
    const rotations: number[] = [];
    const opacities: number[] = [];

    for (const g of gaussians) {
      positions.push(...g.position);
      colors.push(...g.color);
      scales.push(...g.scale);
      rotations.push(...g.rotation);
      opacities.push(g.opacity);
    }

    // Create mesh
    this.mesh = new Mesh('gaussianSplats', this.scene);
    
    // Set vertex data
    const vertexData = new VertexData();
    vertexData.positions = positions;
    vertexData.applyToMesh(this.mesh);

    // Set custom attributes
    this.mesh.setVerticesBuffer(
      new VertexBuffer(this.scene.getEngine(), colors, 'color', false, false, 4, false, 0, 4)
    );
    this.mesh.setVerticesBuffer(
      new VertexBuffer(this.scene.getEngine(), scales, 'scale', false, false, 3, false, 0, 3)
    );
    this.mesh.setVerticesBuffer(
      new VertexBuffer(this.scene.getEngine(), rotations, 'rotation', false, false, 4, false, 0, 4)
    );
    this.mesh.setVerticesBuffer(
      new VertexBuffer(this.scene.getEngine(), opacities, 'opacity', false, false, 1, false, 0, 1)
    );

    this.mesh.material = this.material;
  }

  dispose(): void {
    if (this.mesh) {
      this.mesh.dispose();
    }
    this.material.dispose();
  }
}
