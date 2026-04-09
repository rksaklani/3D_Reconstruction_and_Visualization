import React, { useState } from 'react';

export interface SceneControlsProps {
  onRenderModeChange: (mode: 'photorealistic' | 'physics' | 'hybrid') => void;
  onQualityChange: (quality: 'low' | 'medium' | 'high') => void;
  onCameraModeChange: (mode: 'orbit' | 'fly') => void;
  onResetCamera: () => void;
  onPhysicsDebugToggle: (enabled: boolean) => void;
  onApplyForce?: (force: [number, number, number]) => void;
}

export const SceneControls: React.FC<SceneControlsProps> = ({
  onRenderModeChange,
  onQualityChange,
  onCameraModeChange,
  onResetCamera,
  onPhysicsDebugToggle,
  onApplyForce
}) => {
  const [renderMode, setRenderMode] = useState<'photorealistic' | 'physics' | 'hybrid'>('photorealistic');
  const [quality, setQuality] = useState<'low' | 'medium' | 'high'>('high');
  const [cameraMode, setCameraMode] = useState<'orbit' | 'fly'>('orbit');
  const [physicsDebug, setPhysicsDebug] = useState(false);
  const [forceX, setForceX] = useState(0);
  const [forceY, setForceY] = useState(10);
  const [forceZ, setForceZ] = useState(0);

  const handleRenderModeChange = (mode: 'photorealistic' | 'physics' | 'hybrid') => {
    setRenderMode(mode);
    onRenderModeChange(mode);
  };

  const handleQualityChange = (q: 'low' | 'medium' | 'high') => {
    setQuality(q);
    onQualityChange(q);
  };

  const handleCameraModeChange = (mode: 'orbit' | 'fly') => {
    setCameraMode(mode);
    onCameraModeChange(mode);
  };

  const handlePhysicsDebugToggle = () => {
    const newValue = !physicsDebug;
    setPhysicsDebug(newValue);
    onPhysicsDebugToggle(newValue);
  };

  const handleApplyForce = () => {
    if (onApplyForce) {
      onApplyForce([forceX, forceY, forceZ]);
    }
  };

  return (
    <div className="bg-gray-800 bg-opacity-95 rounded-lg p-4 text-white space-y-4 w-72">
      <h3 className="font-bold text-xl mb-4 border-b border-gray-700 pb-2">Scene Controls</h3>

      {/* Render Mode */}
      <div>
        <label className="block text-sm font-semibold mb-2 text-gray-300">Render Mode</label>
        <div className="grid grid-cols-3 gap-2">
          <button
            onClick={() => handleRenderModeChange('photorealistic')}
            className={`px-3 py-2 rounded text-sm ${
              renderMode === 'photorealistic'
                ? 'bg-blue-600'
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            Photo
          </button>
          <button
            onClick={() => handleRenderModeChange('physics')}
            className={`px-3 py-2 rounded text-sm ${
              renderMode === 'physics'
                ? 'bg-blue-600'
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            Physics
          </button>
          <button
            onClick={() => handleRenderModeChange('hybrid')}
            className={`px-3 py-2 rounded text-sm ${
              renderMode === 'hybrid'
                ? 'bg-blue-600'
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            Hybrid
          </button>
        </div>
      </div>

      {/* Quality */}
      <div>
        <label className="block text-sm font-semibold mb-2 text-gray-300">Quality</label>
        <div className="grid grid-cols-3 gap-2">
          <button
            onClick={() => handleQualityChange('low')}
            className={`px-3 py-2 rounded text-sm ${
              quality === 'low'
                ? 'bg-green-600'
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            Low
          </button>
          <button
            onClick={() => handleQualityChange('medium')}
            className={`px-3 py-2 rounded text-sm ${
              quality === 'medium'
                ? 'bg-green-600'
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            Medium
          </button>
          <button
            onClick={() => handleQualityChange('high')}
            className={`px-3 py-2 rounded text-sm ${
              quality === 'high'
                ? 'bg-green-600'
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            High
          </button>
        </div>
      </div>

      {/* Camera Mode */}
      <div>
        <label className="block text-sm font-semibold mb-2 text-gray-300">Camera Mode</label>
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => handleCameraModeChange('orbit')}
            className={`px-3 py-2 rounded text-sm ${
              cameraMode === 'orbit'
                ? 'bg-purple-600'
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            Orbit
          </button>
          <button
            onClick={() => handleCameraModeChange('fly')}
            className={`px-3 py-2 rounded text-sm ${
              cameraMode === 'fly'
                ? 'bg-purple-600'
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            Fly
          </button>
        </div>
      </div>

      {/* Physics Debug */}
      <div>
        <label className="flex items-center space-x-2 cursor-pointer">
          <input
            type="checkbox"
            checked={physicsDebug}
            onChange={handlePhysicsDebugToggle}
            className="w-4 h-4"
          />
          <span className="text-sm font-semibold text-gray-300">Physics Debug Mode</span>
        </label>
      </div>

      {/* Force Application */}
      {onApplyForce && (
        <div className="border-t border-gray-700 pt-4">
          <label className="block text-sm font-semibold mb-2 text-gray-300">Apply Force</label>
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <span className="text-xs w-6">X:</span>
              <input
                type="range"
                min="-50"
                max="50"
                value={forceX}
                onChange={(e) => setForceX(Number(e.target.value))}
                className="flex-1"
              />
              <span className="text-xs w-12 text-right">{forceX}</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-xs w-6">Y:</span>
              <input
                type="range"
                min="-50"
                max="50"
                value={forceY}
                onChange={(e) => setForceY(Number(e.target.value))}
                className="flex-1"
              />
              <span className="text-xs w-12 text-right">{forceY}</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-xs w-6">Z:</span>
              <input
                type="range"
                min="-50"
                max="50"
                value={forceZ}
                onChange={(e) => setForceZ(Number(e.target.value))}
                className="flex-1"
              />
              <span className="text-xs w-12 text-right">{forceZ}</span>
            </div>
            <button
              onClick={handleApplyForce}
              className="w-full bg-orange-600 hover:bg-orange-700 rounded px-4 py-2 text-sm"
            >
              Apply Force
            </button>
          </div>
        </div>
      )}

      {/* Camera Reset */}
      <button
        onClick={onResetCamera}
        className="w-full bg-blue-600 hover:bg-blue-700 rounded px-4 py-2 font-semibold"
      >
        Reset Camera
      </button>
    </div>
  );
};
