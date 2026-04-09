import React, { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  BabylonSceneManager,
  GaussianRenderer,
  SceneLoader,
  MeshRenderer,
  PhysicsSynchronizer,
  PhysicsDebugVisualizer,
  InteractionSystem,
  CameraController,
  RenderPipeline
} from '../../../rendering/splat-renderer/src';

export const Viewer: React.FC = () => {
  const { jobId } = useParams<{ jobId: string }>();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [sceneManager, setSceneManager] = useState<BabylonSceneManager | null>(null);
  const [renderPipeline, setRenderPipeline] = useState<RenderPipeline | null>(null);
  const [cameraController, setCameraController] = useState<CameraController | null>(null);
  const [interactionSystem, setInteractionSystem] = useState<InteractionSystem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedObject, setSelectedObject] = useState<{ id: number; label: string } | null>(null);

  useEffect(() => {
    if (!canvasRef.current || !jobId) return;

    const initScene = async () => {
      try {
        // Initialize Babylon.js scene
        const manager = new BabylonSceneManager(canvasRef.current!);
        setSceneManager(manager);

        const scene = manager.getScene();

        // Load scene data
        const loader = new SceneLoader();
        const sceneData = await loader.loadFromMinIO(
          window.location.origin,
          '3d-pipeline',
          jobId
        );

        if (!loader.validateSceneData(sceneData)) {
          throw new Error('Invalid scene data');
        }

        // Initialize renderers
        const gaussianRenderer = new GaussianRenderer(scene);
        const meshRenderer = new MeshRenderer(scene);
        const physicsDebug = new PhysicsDebugVisualizer(scene);

        // Load objects
        for (const obj of sceneData.objects) {
          if (obj.representationType === 'staticGaussian' && obj.staticRep) {
            gaussianRenderer.loadGaussians(obj.staticRep.gaussians);
          } else if (obj.representationType === 'mesh' && obj.meshRep) {
            meshRenderer.loadMesh(obj);
          }
        }

        // Setup physics synchronization
        const physicsSync = new PhysicsSynchronizer(
          scene,
          meshRenderer,
          `/api/physics/${jobId}`
        );
        physicsSync.startSync();

        // Setup interaction
        const interaction = new InteractionSystem(scene, physicsSync);
        interaction.onObjectPicked((objectId, label) => {
          setSelectedObject({ id: objectId, label });
        });
        setInteractionSystem(interaction);

        // Setup camera controls
        const camera = new CameraController(scene, canvasRef.current!);
        setCameraController(camera);

        // Setup render pipeline
        const pipeline = new RenderPipeline(
          scene,
          gaussianRenderer,
          meshRenderer,
          physicsDebug
        );
        setRenderPipeline(pipeline);

        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load scene');
        setLoading(false);
      }
    };

    initScene();

    return () => {
      sceneManager?.dispose();
    };
  }, [jobId]);

  const handleRenderModeChange = (mode: 'photorealistic' | 'physics' | 'hybrid') => {
    renderPipeline?.setRenderMode(mode);
  };

  const handleQualityChange = (quality: 'low' | 'medium' | 'high') => {
    renderPipeline?.setRenderQuality(quality);
  };

  const handleCameraModeChange = (mode: 'orbit' | 'fly') => {
    cameraController?.setMode(mode);
  };

  const handleResetCamera = () => {
    cameraController?.resetCamera();
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

      {/* Object Inspector */}
      {selectedObject && (
        <div className="absolute bottom-4 left-4 bg-gray-800 bg-opacity-90 rounded-lg p-4 text-white w-64">
          <h3 className="font-bold text-lg mb-2">Selected Object</h3>
          <p className="text-sm">
            <span className="text-gray-400">ID:</span> {selectedObject.id}
          </p>
          <p className="text-sm">
            <span className="text-gray-400">Label:</span> {selectedObject.label}
          </p>
          <button
            onClick={() => setSelectedObject(null)}
            className="mt-3 w-full bg-gray-700 hover:bg-gray-600 rounded px-4 py-2 text-sm"
          >
            Deselect
          </button>
        </div>
      )}

      {/* Performance Stats */}
      <div className="absolute top-4 left-4 bg-gray-800 bg-opacity-90 rounded-lg p-3 text-white text-sm">
        <p>FPS: {renderPipeline?.getPerformanceMetrics().fps.toFixed(1) || '0'}</p>
      </div>
    </div>
  );
};
