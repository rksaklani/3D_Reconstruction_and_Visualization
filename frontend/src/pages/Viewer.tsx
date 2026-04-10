import React, { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import * as BABYLON from '@babylonjs/core';
import { GaussianRenderer, Gaussian3D } from '../renderer/gaussian_renderer';
import { RenderPipeline, RenderMode, RenderQuality } from '../renderer/render_pipeline';
import { MeshRenderer } from '../renderer/mesh_renderer';
import { PhysicsDebugVisualizer } from '../renderer/physics_debug';
import { SceneLoader } from '../renderer/scene_loader';
import apiClient from '../api/client';

export const Viewer: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loadingStatus, setLoadingStatus] = useState<string>('Initializing...');
  const [renderMode, setRenderMode] = useState<RenderMode>('photorealistic');
  const [quality, setQuality] = useState<RenderQuality>('high');
  const [cameraMode, setCameraMode] = useState<'orbit' | 'fly'>('orbit');
  const [fps, setFps] = useState(0);
  
  const engineRef = useRef<BABYLON.Engine | null>(null);
  const sceneRef = useRef<BABYLON.Scene | null>(null);
  const pipelineRef = useRef<RenderPipeline | null>(null);
  const gaussianRendererRef = useRef<GaussianRenderer | null>(null);
  const sceneLoaderRef = useRef<SceneLoader | null>(null);

  useEffect(() => {
    if (!canvasRef.current) return;

    const initScene = async () => {
      try {
        // Create Babylon.js engine and scene
        const engine = new BABYLON.Engine(canvasRef.current!, true, {
          preserveDrawingBuffer: true,
          stencil: true,
          antialias: true
        });
        engineRef.current = engine;

        const scene = new BABYLON.Scene(engine);
        sceneRef.current = scene;
        scene.clearColor = new BABYLON.Color4(0.1, 0.1, 0.15, 1);

        // Setup camera
        const camera = new BABYLON.ArcRotateCamera(
          'camera',
          Math.PI / 2,
          Math.PI / 3,
          15,
          BABYLON.Vector3.Zero(),
          scene
        );
        camera.attachControl(canvasRef.current!, true);
        camera.wheelPrecision = 50;
        camera.minZ = 0.1;
        camera.maxZ = 1000;
        camera.lowerRadiusLimit = 1;
        camera.upperRadiusLimit = 100;

        // Setup lighting
        const light = new BABYLON.HemisphericLight(
          'light',
          new BABYLON.Vector3(0, 1, 0),
          scene
        );
        light.intensity = 0.8;

        // Initialize renderers
        const gaussianRenderer = new GaussianRenderer(scene);
        gaussianRendererRef.current = gaussianRenderer;

        const meshRenderer = new MeshRenderer(scene);
        const physicsDebug = new PhysicsDebugVisualizer(scene);

        // Initialize render pipeline
        const pipeline = new RenderPipeline(
          scene,
          gaussianRenderer,
          meshRenderer,
          physicsDebug
        );
        pipelineRef.current = pipeline;

        // Initialize scene loader
        const sceneLoader = new SceneLoader(scene, gaussianRenderer, meshRenderer);
        sceneLoaderRef.current = sceneLoader;

        // Load scene data if job ID is provided
        if (id) {
          await loadSceneData(id, sceneLoader);
        } else {
          // Load demo scene
          loadDemoScene(gaussianRenderer);
        }

        // Render loop with FPS tracking
        let lastTime = performance.now();
        let frameCount = 0;
        
        engine.runRenderLoop(() => {
          scene.render();
          
          frameCount++;
          const currentTime = performance.now();
          if (currentTime - lastTime >= 1000) {
            setFps(Math.round(frameCount * 1000 / (currentTime - lastTime)));
            frameCount = 0;
            lastTime = currentTime;
          }
        });

        // Handle resize
        const handleResize = () => engine.resize();
        window.addEventListener('resize', handleResize);

        setLoading(false);

        return () => {
          window.removeEventListener('resize', handleResize);
        };
      } catch (err) {
        console.error('Scene initialization error:', err);
        setError(err instanceof Error ? err.message : 'Failed to initialize 3D viewer');
        setLoading(false);
      }
    };

    initScene();

    return () => {
      gaussianRendererRef.current?.dispose();
      pipelineRef.current?.dispose();
      sceneRef.current?.dispose();
      engineRef.current?.dispose();
    };
  }, [id]);

  const loadSceneData = async (jobId: string, sceneLoader: SceneLoader) => {
    try {
      setLoadingStatus('Fetching job status...');
      
      // Fetch job status
      const response = await apiClient.get(`/jobs/${jobId}`);
      const job = response.data;

      console.log('Job data:', job);

      if (job.status !== 'completed') {
        setError(`Reconstruction not completed yet (status: ${job.status})`);
        return;
      }

      setLoadingStatus('Loading 3D reconstruction...');
      
      // Load Gaussian splats from backend API
      const apiBaseUrl = import.meta.env.VITE_API_URL || '/api';
      console.log('API Base URL:', apiBaseUrl);
      console.log('Loading from:', `${apiBaseUrl}/reconstruction/${jobId}/points`);
      
      await sceneLoader.loadFromAPI(apiBaseUrl, jobId);
      
      setLoadingStatus('Scene loaded successfully');
      console.log('Successfully loaded scene from backend');
    } catch (err) {
      console.error('Failed to load scene data:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to load scene data';
      setError(errorMessage);
      
      // Fall back to demo scene
      if (gaussianRendererRef.current) {
        console.log('Falling back to demo scene');
        setLoadingStatus('Loading demo scene...');
        loadDemoScene(gaussianRendererRef.current);
        setError(null); // Clear error since we're showing demo
      }
    }
  };

  const loadDemoScene = (gaussianRenderer: GaussianRenderer) => {
    // Create demo Gaussian splats
    const demoGaussians: Gaussian3D[] = [];
    const gridSize = 5;
    
    for (let x = -gridSize; x <= gridSize; x++) {
      for (let y = -gridSize; y <= gridSize; y++) {
        for (let z = -gridSize; z <= gridSize; z++) {
          if (Math.random() > 0.7) {
            demoGaussians.push({
              position: [x * 0.5, y * 0.5, z * 0.5],
              scale: [0.1, 0.1, 0.1],
              rotation: [0, 0, 0, 1],
              color: [
                Math.random() * 0.5 + 0.5,
                Math.random() * 0.5 + 0.5,
                Math.random() * 0.5 + 0.5,
                1
              ],
              opacity: 0.8
            });
          }
        }
      }
    }

    gaussianRenderer.loadGaussians(demoGaussians);
  };

  const handleRenderModeChange = (mode: RenderMode) => {
    setRenderMode(mode);
    pipelineRef.current?.setRenderMode(mode);
  };

  const handleQualityChange = (newQuality: RenderQuality) => {
    setQuality(newQuality);
    pipelineRef.current?.setRenderQuality(newQuality);
  };

  const handleCameraModeChange = (mode: 'orbit' | 'fly') => {
    setCameraMode(mode);
    
    if (sceneRef.current) {
      const currentCamera = sceneRef.current.activeCamera as BABYLON.ArcRotateCamera;
      const position = currentCamera.position.clone();
      const target = currentCamera.target.clone();

      if (mode === 'fly') {
        const flyCamera = new BABYLON.FreeCamera('flyCamera', position, sceneRef.current);
        flyCamera.setTarget(target);
        flyCamera.attachControl(canvasRef.current!, true);
        flyCamera.speed = 0.5;
        sceneRef.current.activeCamera = flyCamera;
        currentCamera.dispose();
      } else {
        const orbitCamera = new BABYLON.ArcRotateCamera(
          'orbitCamera',
          Math.PI / 2,
          Math.PI / 3,
          position.length(),
          target,
          sceneRef.current
        );
        orbitCamera.attachControl(canvasRef.current!, true);
        sceneRef.current.activeCamera = orbitCamera;
        currentCamera.dispose();
      }
    }
  };

  const handleResetCamera = () => {
    if (sceneRef.current && cameraMode === 'orbit') {
      const camera = sceneRef.current.activeCamera as BABYLON.ArcRotateCamera;
      if (camera) {
        camera.alpha = Math.PI / 2;
        camera.beta = Math.PI / 3;
        camera.radius = 15;
        camera.target = BABYLON.Vector3.Zero();
      }
    }
  };

  const handleDownloadPLY = async () => {
    if (!id) return;
    
    try {
      const apiBaseUrl = import.meta.env.VITE_API_URL || '/api';
      const response = await fetch(`${apiBaseUrl}/reconstruction/${id}/download/ply`);
      
      if (!response.ok) {
        throw new Error('Failed to download PLY');
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${id}_pointcloud.ply`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Failed to download PLY:', err);
      alert('Failed to download PLY file');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-white text-lg">{loadingStatus}</p>
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
            value={renderMode}
            onChange={(e) => handleRenderModeChange(e.target.value as RenderMode)}
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
            value={quality}
            onChange={(e) => handleQualityChange(e.target.value as RenderQuality)}
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
            value={cameraMode}
            onChange={(e) => handleCameraModeChange(e.target.value as 'orbit' | 'fly')}
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

        {id && (
          <button
            onClick={handleDownloadPLY}
            className="w-full bg-green-600 hover:bg-green-700 rounded px-4 py-2"
          >
            Download PLY
          </button>
        )}
      </div>

      {/* Info */}
      <div className="absolute bottom-4 left-4 bg-gray-800 bg-opacity-90 rounded-lg p-4 text-white w-64">
        <h3 className="font-bold text-lg mb-2">Gaussian Splat Viewer</h3>
        <p className="text-sm text-gray-300">
          Job ID: {id || 'demo'}
        </p>
        <p className="text-xs text-gray-400 mt-2">
          {cameraMode === 'orbit' ? 'Mouse: rotate, scroll: zoom' : 'WASD: move, Mouse: look'}
        </p>
      </div>

      {/* Performance Stats */}
      <div className="absolute top-4 left-4 bg-gray-800 bg-opacity-90 rounded-lg p-3 text-white text-sm space-y-1">
        <p>FPS: {fps}</p>
        <p>Mode: {renderMode}</p>
        <p>Quality: {quality}</p>
        <p>Camera: {cameraMode}</p>
      </div>
    </div>
  );
};

export default Viewer;
