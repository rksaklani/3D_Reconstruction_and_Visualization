import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Square, Eye, Trash2 } from 'lucide-react';
import { jobsApi } from '../api/client';

const PIPELINE_STAGES = [
  'Input Validation',
  'Preprocessing',
  'Feature Extraction',
  'Structure from Motion',
  'Bundle Adjustment',
  'AI Scene Understanding',
  'Hybrid Representation',
  'Physics Setup',
  'Export'
];

export const Processing = () => {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [jobStatus, setJobStatus] = useState(null);
  const [error, setError] = useState(null);
  const [ws, setWs] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

  const handleStop = async () => {
    if (!confirm('Are you sure you want to stop this job?')) {
      return;
    }

    setActionLoading(true);
    try {
      await jobsApi.stopJob(jobId);
      setTimeout(() => {
        pollStatus();
        setActionLoading(false);
      }, 1000);
    } catch (err) {
      console.error('Failed to stop job:', err);
      alert('Failed to stop job');
      setActionLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this job? This action cannot be undone.')) {
      return;
    }

    setActionLoading(true);
    try {
      await jobsApi.deleteJob(jobId);
      navigate('/app/jobs');
    } catch (err) {
      console.error('Failed to delete job:', err);
      alert('Failed to delete job');
      setActionLoading(false);
    }
  };

  const handleView = () => {
    navigate(`/app/viewer/${jobId}`);
  };

  useEffect(() => {
    if (!jobId) return;

    // Poll for status
    const pollStatus = async () => {
      try {
        const response = await fetch(`/api/status/${jobId}`);
        if (!response.ok) {
          throw new Error(`Failed to fetch status: ${response.statusText}`);
        }
        const data = await response.json();
        setJobStatus(data);

        if (data.status === 'completed') {
          setTimeout(() => navigate(`/viewer/${jobId}`), 2000);
        } else if (data.status === 'failed') {
          setError(data.error || 'Job failed');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      }
    };

    // Initial poll
    pollStatus();

    // Setup WebSocket for real-time updates
    const websocket = new WebSocket(`ws://${window.location.host}/ws/status/${jobId}`);
    
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setJobStatus(data);

      if (data.status === 'completed') {
        setTimeout(() => navigate(`/viewer/${jobId}`), 2000);
      } else if (data.status === 'failed') {
        setError(data.error || 'Job failed');
      }
    };

    websocket.onerror = () => {
      console.warn('WebSocket error, falling back to polling');
      // Fallback to polling if WebSocket fails
      const intervalId = setInterval(pollStatus, 2000);
      return () => clearInterval(intervalId);
    };

    setWs(websocket);

    return () => {
      websocket.close();
    };
  }, [jobId, navigate]);

  const formatTime = (seconds) => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${minutes}m ${secs}s`;
  };

  const getCurrentStageIndex = () => {
    if (!jobStatus) return 0;
    return PIPELINE_STAGES.findIndex(stage => 
      stage.toLowerCase() === jobStatus.currentStage.toLowerCase()
    );
  };

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100 p-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h2 className="text-2xl font-bold text-red-800 mb-4">Processing Failed</h2>
            <p className="text-red-700">{error}</p>
            <button
              onClick={() => navigate('/')}
              className="mt-4 px-6 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              Back to Home
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!jobStatus) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading job status...</p>
        </div>
      </div>
    );
  }

  const currentStageIndex = getCurrentStageIndex();

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Processing 3D Reconstruction</h1>

        <div className="bg-white rounded-lg p-6 mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Job ID: {jobId}</h2>
            <div className="flex items-center space-x-2">
              <span className={`px-4 py-2 rounded-full text-sm font-semibold ${
                jobStatus.status === 'completed' ? 'bg-green-100 text-green-800' :
                jobStatus.status === 'failed' ? 'bg-red-100 text-red-800' :
                jobStatus.status === 'processing' ? 'bg-blue-100 text-blue-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {jobStatus.status.toUpperCase()}
              </span>
              
              {/* Action Buttons */}
              {jobStatus.status === 'processing' && (
                <button
                  onClick={handleStop}
                  disabled={actionLoading}
                  className="flex items-center space-x-1 px-3 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50"
                  title="Stop Processing"
                >
                  <Square className="w-4 h-4" />
                  <span>Stop</span>
                </button>
              )}
              
              {jobStatus.status === 'completed' && (
                <button
                  onClick={handleView}
                  className="flex items-center space-x-1 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  title="View 3D Model"
                >
                  <Eye className="w-4 h-4" />
                  <span>View 3D</span>
                </button>
              )}
              
              <button
                onClick={handleDelete}
                disabled={actionLoading}
                className="flex items-center space-x-1 px-3 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
                title="Delete Job"
              >
                <Trash2 className="w-4 h-4" />
                <span>Delete</span>
              </button>
            </div>
          </div>

          <div className="mb-6">
            <div className="flex justify-between items-center mb-2">
              <span className="text-gray-700 font-medium">{jobStatus.currentStage}</span>
              <span className="text-gray-600">{Math.round(jobStatus.progress)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-4">
              <div
                className="bg-blue-600 h-4 rounded-full transition-all duration-500"
                style={{ width: `${jobStatus.progress}%` }}
              />
            </div>
          </div>

          {jobStatus.estimatedTimeRemaining && (
            <p className="text-gray-600 text-center">
              Estimated time remaining: {formatTime(jobStatus.estimatedTimeRemaining)}
            </p>
          )}
        </div>

        <div className="bg-white rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Pipeline Stages</h3>
          <div className="space-y-3">
            {PIPELINE_STAGES.map((stage, index) => (
              <div
                key={stage}
                className={`flex items-center p-3 rounded ${
                  index < currentStageIndex ? 'bg-green-50' :
                  index === currentStageIndex ? 'bg-blue-50' :
                  'bg-gray-50'
                }`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center mr-3 ${
                  index < currentStageIndex ? 'bg-green-500 text-white' :
                  index === currentStageIndex ? 'bg-blue-500 text-white' :
                  'bg-gray-300 text-gray-600'
                }`}>
                  {index < currentStageIndex ? '✓' : index + 1}
                </div>
                <span className={`font-medium ${
                  index === currentStageIndex ? 'text-blue-800' : 'text-gray-700'
                }`}>
                  {stage}
                </span>
                {index === currentStageIndex && (
                  <div className="ml-auto">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {jobStatus.status === 'completed' && (
          <div className="mt-6 bg-green-50 border border-green-200 rounded-lg p-6 text-center">
            <h3 className="text-xl font-semibold text-green-800 mb-2">Processing Complete!</h3>
            <p className="text-green-700 mb-4">Redirecting to 3D viewer...</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Processing;
