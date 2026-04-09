precision highp float;

// Varyings from vertex shader
varying vec4 vColor;
varying vec2 vUV;
varying float vOpacity;
varying mat3 vCov2D;

void main() {
    // Compute pixel offset from splat center
    vec2 d = gl_PointCoord * 2.0 - 1.0;
    
    // Compute inverse of 2D covariance
    float det = vCov2D[0][0] * vCov2D[1][1] - vCov2D[0][1] * vCov2D[1][0];
    if (det == 0.0) discard;
    
    float invDet = 1.0 / det;
    mat2 covInv = mat2(
        vCov2D[1][1] * invDet, -vCov2D[0][1] * invDet,
        -vCov2D[1][0] * invDet, vCov2D[0][0] * invDet
    );
    
    // Compute Gaussian weight
    vec2 covD = covInv * d;
    float power = -0.5 * dot(d, covD);
    
    if (power > 0.0) discard;
    
    float alpha = min(0.99, vOpacity * exp(power));
    
    if (alpha < 0.01) discard;
    
    // Output color with alpha
    gl_FragColor = vec4(vColor.rgb, alpha);
}
