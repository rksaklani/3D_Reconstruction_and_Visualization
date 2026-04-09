precision highp float;

// Attributes
attribute vec3 position;
attribute vec4 color;
attribute vec3 scale;
attribute vec4 rotation;  // Quaternion
attribute float opacity;

// Uniforms
uniform mat4 worldViewProjection;
uniform mat4 world;
uniform mat4 view;
uniform mat4 projection;
uniform vec3 cameraPosition;

// Varyings
varying vec4 vColor;
varying vec2 vUV;
varying float vOpacity;
varying mat3 vCov2D;

// Convert quaternion to rotation matrix
mat3 quaternionToMatrix(vec4 q) {
    float x = q.x, y = q.y, z = q.z, w = q.w;
    return mat3(
        1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - w * z), 2.0 * (x * z + w * y),
        2.0 * (x * y + w * z), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - w * x),
        2.0 * (x * z - w * y), 2.0 * (y * z + w * x), 1.0 - 2.0 * (x * x + y * y)
    );
}

void main() {
    // Compute 3D covariance matrix from scale and rotation
    mat3 R = quaternionToMatrix(rotation);
    mat3 S = mat3(
        scale.x, 0.0, 0.0,
        0.0, scale.y, 0.0,
        0.0, 0.0, scale.z
    );
    mat3 M = R * S;
    mat3 Cov3D = M * transpose(M);
    
    // Transform to world space
    vec4 worldPos = world * vec4(position, 1.0);
    
    // Project to screen space
    vec4 clipPos = worldViewProjection * vec4(position, 1.0);
    gl_Position = clipPos;
    
    // Compute 2D covariance in screen space (Jacobian of projection)
    float focal = projection[0][0];
    vec3 t = (view * worldPos).xyz;
    float limx = 1.3 * tan(0.5);
    float limy = 1.3 * tan(0.5);
    float txtz = t.x / t.z;
    float tytz = t.y / t.z;
    t.x = min(limx, max(-limx, txtz)) * t.z;
    t.y = min(limy, max(-limy, tytz)) * t.z;
    
    mat3 J = mat3(
        focal / t.z, 0.0, -(focal * t.x) / (t.z * t.z),
        0.0, focal / t.z, -(focal * t.y) / (t.z * t.z),
        0.0, 0.0, 0.0
    );
    
    mat3 W = mat3(view);
    mat3 T = W * J;
    mat3 Cov2D = transpose(T) * Cov3D * T;
    
    // Add small value to diagonal for numerical stability
    Cov2D[0][0] += 0.3;
    Cov2D[1][1] += 0.3;
    
    vCov2D = Cov2D;
    vColor = color;
    vOpacity = opacity;
    vUV = vec2(0.0);  // Will be computed in fragment shader
    
    // Point size for splatting
    gl_PointSize = 2.0 * sqrt(max(Cov2D[0][0], Cov2D[1][1]));
}
