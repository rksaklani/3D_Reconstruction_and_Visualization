import React, { useState, useEffect } from 'react';

export interface ObjectProperties {
  objectId: number;
  label: string;
  position: [number, number, number];
  rotation: [number, number, number, number]; // Quaternion
  velocity: [number, number, number];
  angularVelocity: [number, number, number];
  mass: number;
  isStatic: boolean;
  representationType: 'staticGaussian' | 'dynamicGaussian' | 'mesh';
}

export interface ObjectInspectorProps {
  objectId: number | null;
  onClose: () => void;
  onPropertyChange?: (objectId: number, property: string, value: any) => void;
}

export const ObjectInspector: React.FC<ObjectInspectorProps> = ({
  objectId,
  onClose,
  onPropertyChange
}) => {
  const [properties, setProperties] = useState<ObjectProperties | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (objectId === null) {
      setProperties(null);
      return;
    }

    const fetchProperties = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const response = await fetch(`/api/object/${objectId}/properties`);
        if (!response.ok) {
          throw new Error(`Failed to fetch properties: ${response.statusText}`);
        }
        const data: ObjectProperties = await response.json();
        setProperties(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchProperties();
  }, [objectId]);

  if (objectId === null) {
    return null;
  }

  const formatVector = (vec: number[]): string => {
    return vec.map(v => v.toFixed(2)).join(', ');
  };

  const formatQuaternion = (q: number[]): string => {
    return `[${q.map(v => v.toFixed(3)).join(', ')}]`;
  };

  const handleMassChange = (newMass: number) => {
    if (properties && onPropertyChange) {
      onPropertyChange(properties.objectId, 'mass', newMass);
      setProperties({ ...properties, mass: newMass });
    }
  };

  return (
    <div className="bg-gray-800 bg-opacity-95 rounded-lg p-4 text-white w-80 max-h-[80vh] overflow-y-auto">
      <div className="flex justify-between items-center mb-4 border-b border-gray-700 pb-2">
        <h3 className="font-bold text-xl">Object Inspector</h3>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-white text-2xl leading-none"
        >
          ×
        </button>
      </div>

      {loading && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
          <p className="text-sm text-gray-400 mt-2">Loading properties...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-900 bg-opacity-50 border border-red-700 rounded p-3 mb-4">
          <p className="text-sm text-red-200">{error}</p>
        </div>
      )}

      {properties && !loading && (
        <div className="space-y-4">
          {/* Basic Info */}
          <div>
            <h4 className="text-sm font-semibold text-gray-400 mb-2">Basic Information</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">ID:</span>
                <span className="font-mono">{properties.objectId}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Label:</span>
                <span className="font-semibold">{properties.label}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Type:</span>
                <span className="text-xs bg-gray-700 px-2 py-1 rounded">
                  {properties.representationType}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Physics:</span>
                <span className={`text-xs px-2 py-1 rounded ${
                  properties.isStatic ? 'bg-gray-700' : 'bg-green-700'
                }`}>
                  {properties.isStatic ? 'Static' : 'Dynamic'}
                </span>
              </div>
            </div>
          </div>

          {/* Transform */}
          <div className="border-t border-gray-700 pt-4">
            <h4 className="text-sm font-semibold text-gray-400 mb-2">Transform</h4>
            <div className="space-y-2 text-sm">
              <div>
                <span className="text-gray-400 block mb-1">Position:</span>
                <span className="font-mono text-xs bg-gray-900 px-2 py-1 rounded block">
                  ({formatVector(properties.position)})
                </span>
              </div>
              <div>
                <span className="text-gray-400 block mb-1">Rotation (Quaternion):</span>
                <span className="font-mono text-xs bg-gray-900 px-2 py-1 rounded block">
                  {formatQuaternion(properties.rotation)}
                </span>
              </div>
            </div>
          </div>

          {/* Physics Properties */}
          {!properties.isStatic && (
            <div className="border-t border-gray-700 pt-4">
              <h4 className="text-sm font-semibold text-gray-400 mb-2">Physics Properties</h4>
              <div className="space-y-3 text-sm">
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-gray-400">Mass:</span>
                    <span className="font-semibold">{properties.mass.toFixed(2)} kg</span>
                  </div>
                  {onPropertyChange && (
                    <input
                      type="range"
                      min="0.1"
                      max="100"
                      step="0.1"
                      value={properties.mass}
                      onChange={(e) => handleMassChange(Number(e.target.value))}
                      className="w-full"
                    />
                  )}
                </div>
                <div>
                  <span className="text-gray-400 block mb-1">Velocity:</span>
                  <span className="font-mono text-xs bg-gray-900 px-2 py-1 rounded block">
                    ({formatVector(properties.velocity)}) m/s
                  </span>
                </div>
                <div>
                  <span className="text-gray-400 block mb-1">Angular Velocity:</span>
                  <span className="font-mono text-xs bg-gray-900 px-2 py-1 rounded block">
                    ({formatVector(properties.angularVelocity)}) rad/s
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="border-t border-gray-700 pt-4">
            <h4 className="text-sm font-semibold text-gray-400 mb-2">Actions</h4>
            <div className="space-y-2">
              <button className="w-full bg-blue-600 hover:bg-blue-700 rounded px-3 py-2 text-sm">
                Focus Camera
              </button>
              {!properties.isStatic && (
                <>
                  <button className="w-full bg-orange-600 hover:bg-orange-700 rounded px-3 py-2 text-sm">
                    Apply Impulse
                  </button>
                  <button className="w-full bg-red-600 hover:bg-red-700 rounded px-3 py-2 text-sm">
                    Reset Physics
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
