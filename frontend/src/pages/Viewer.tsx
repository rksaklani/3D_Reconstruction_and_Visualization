import React, { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import * as BABYLON from '@babylonjs/core';

export const Viewer: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [renderMode, setRenderMode] = useState<'photorealistic' | 'physics' | 'hybrid'>('photorealistic');
  const [quality, setQuality] = useState<'low' | 'medium' | 'high'>('high');
  const [cameraMode, setCameraMode] = useState<'orbit' | 'fly'>('orbit');
  const engineRef = useRef<BABYLON.Engine | null>(null);
  const sceneRef = useRef<BABYLON.Scene | null>(null);

  useEffect(() => {
    if (!canvasRef.current) return;

    const initScene = async () => {
      try {
        // Create Babylon.js engine and scene
        const engine = new BABYLON.Engine(canvasRef.current!, true);
        engineRef.current = engine;

        const scene = new BABYLON.Scene(engine);
        sceneRef.current = scene;

        // Setup camera
        const camera = new BABYLON.ArcRotateCamera(
          'camera',
          Math.PI / 2,
          Math.PI / 2,
          10,
          BABYLON.Vector3.Zero(),
          scene
        );
        camera.attachControl(canvasRef.current!, true);
        camera.wheelPrecision = 50;
        camera.minZ = 0.1;

        // Setup lighting
        const light = new BABYLON.HemisphericLight(
          'light',
          new BABYLON.Vector3(0, 1, 0),
          scene
        );
        light.intensity = 0.7;

        // Add demo content
        const sphere = BABYLON.MeshBuilder.CreateSphere('sphere', { diameter: 2 }, scene);
        sphere.position.y = 1;

        const ground = BABYLON.MeshBuilder.CreateGround('ground', { width: 10, height: 10 }, scene);

        // Materials
        const sphereMaterial = new BABYLON.StandardMaterial('sphereMat', scene);
        sphereMaterial.diffuseColor = new BABYLON.Color3(0.4, 0.6, 1);
        sphere.material = sphereMaterial;

        const groundMaterial = new BABYLON.StandardMaterial('groundMat', scene);
        groundMaterial.diffuseColor = new BABYLON.Color3(0.5, 0.5, 0.5);
        ground.material = groundMaterial;

        // Render loop
        engine.runRenderLoop(() => {
          scene.render();
        });

        // Handle resize
        window.addEventListener('resize', () => {
          engine.resize();
        });

        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to initialize 3D viewer');
        setLoading(false);
      }
    };

    initScene();

    return () => {
      sceneRef.current?.dispose();
      engineRef.current?.dispose();
    };
  }, [id]);

  const handleRenderModeChange = (mode: 'photorealistic' | 'physics' | 'hybrid') => {
    setRenderMode(mode);
    // TODO: Implement render mode switching
  };

  const handleQualityChange = (newQuality: 'low' | 'medium' | 'high') => {
    setQuality(newQuality);
    // TODO: Implement quality adjustment
  };

  const handleCameraModeChange = (mode: 'orbit' | 'fly') => {
    setCameraMode(mode);
    // TODO: Implement camera mode switching
  };

  const handleResetCamera = () => {
    if (sceneRef.current) {
      const camera = sceneRef.current.activeCamera as BABYLON.ArcRotateCamera;
      if (camera) {
        camera.alpha = Math.PI / 2;
        camera.beta = Math.PI / 2;
        camera.radius = 10;
        camera.target = BABYLON.Vector3.Zero();
      }
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-white">Loading 3D scene...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="bg-red-900 border border-red-700 rounded-lg p-6 max-w-md">
          <h2 className="text-xl font-bold text-red-200 mb-2">Error Loading Scene</h2>
          <p className="text-red-300">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full h-screen bg-gray-900">
      <canvas ref={canvasRef} className="w-full h-full" />

      {/* Controls Panel */}
      <div className="absolute top-4 right-4 bg-gray-800 bg-opacity-90 rounded-lg p-4 text-white space-y-4 w-64">
        <h3 className="font-bold text-lg mb-2">Scene Controls</h3>

        {/* Render Mode */}
        <div>
          <label className="block text-sm mb-2">Render Mode</label>
          <select
            onChange={(e) => handleRenderModeChange(e.target.value as any)}
            className="w-full bg-gray-700 rounded px-3 py-2"
          >
            <option value="photorealistic">Photorealistic</option>
            <option value="physics">Physics Debug</option>
            <option value="hybrid">Hybrid</option>
          </select>
        </div>

        {/* Quality */}
        <div>
          <label className="block text-sm mb-2">Quality</label>
          <select
            onChange={(e) => handleQualityChange(e.target.value as any)}
            className="w-full bg-gray-700 rounded px-3 py-2"
          >
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>

        {/* Camera Mode */}
        <div>
          <label className="block text-sm mb-2">Camera Mode</label>
          <select
            onChange={(e) => handleCameraModeChange(e.target.value as any)}
            className="w-full bg-gray-700 rounded px-3 py-2"
          >
            <option value="orbit">Orbit</option>
            <option value="fly">Fly</option>
          </select>
        </div>

        <button
          onClick={handleResetCamera}
          className="w-full bg-blue-600 hover:bg-blue-700 rounded px-4 py-2"
        >
          Reset Camera
        </button>
      </div>

      {/* Info */}
      <div className="absolute bottom-4 left-4 bg-gray-800 bg-opacity-90 rounded-lg p-4 text-white w-64">
        <h3 className="font-bold text-lg mb-2">3D Viewer</h3>
        <p className="text-sm text-gray-300">
          Model ID: {id || 'demo'}
        </p>
        <p className="text-xs text-gray-400 mt-2">
          Use mouse to rotate, scroll to zoom
        </p>
      </div>

      {/* Performance Stats */}
      <div className="absolute top-4 left-4 bg-gray-800 bg-opacity-90 rounded-lg p-3 text-white text-sm">
        <p>Render Mode: {renderMode}</p>
        <p>Quality: {quality}</p>
        <p>Camera: {cameraMode}</p>
      </div>
    </div>
  );
};

export default Viewer;
