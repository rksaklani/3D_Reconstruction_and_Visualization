import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'

function ViewerDebug() {
  const { id } = useParams()
  const [jobData, setJobData] = useState(null)
  const [sceneData, setSceneData] = useState(null)
  const [pointsData, setPointsData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [errors, setErrors] = useState({})

  useEffect(() => {
    if (id) {
      loadDebugData()
    }
  }, [id])

  const loadDebugData = async () => {
    setLoading(true)
    const newErrors = {}

    // 1. Check job status
    try {
      const response = await fetch(`/api/jobs/${id}`)
      if (response.ok) {
        const data = await response.json()
        setJobData(data)
      } else {
        newErrors.job = `HTTP ${response.status}: ${response.statusText}`
      }
    } catch (err) {
      newErrors.job = err.message
    }

    // 2. Check scene data
    try {
      const response = await fetch(`/api/reconstruction/${id}/scene`)
      if (response.ok) {
        const data = await response.json()
        setSceneData(data)
      } else {
        newErrors.scene = `HTTP ${response.status}: ${response.statusText}`
      }
    } catch (err) {
      newErrors.scene = err.message
    }

    // 3. Check points data
    try {
      const response = await fetch(`/api/reconstruction/${id}/points?limit=10`)
      if (response.ok) {
        const data = await response.json()
        setPointsData(data)
      } else {
        newErrors.points = `HTTP ${response.status}: ${response.statusText}`
      }
    } catch (err) {
      newErrors.points = err.message
    }

    setErrors(newErrors)
    setLoading(false)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 p-8">
        <div className="max-w-4xl mx-auto">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="text-center mt-4">Loading debug information...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <Link to="/app/jobs" className="flex items-center text-blue-600 hover:text-blue-700">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Jobs
        </Link>

        <h1 className="text-3xl font-bold">3D Viewer Debug - Job {id}</h1>

        {/* Job Status */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">1. Job Status</h2>
          {errors.job ? (
            <div className="bg-red-50 border border-red-200 rounded p-4">
              <p className="text-red-800 font-medium">Error loading job:</p>
              <p className="text-red-600 text-sm mt-1">{errors.job}</p>
            </div>
          ) : jobData ? (
            <div className="space-y-2">
              <div className="flex justify-between py-2 border-b">
                <span className="font-medium">Status:</span>
                <span className={`px-2 py-1 rounded text-sm ${
                  jobData.status === 'completed' ? 'bg-green-100 text-green-800' :
                  jobData.status === 'processing' ? 'bg-blue-100 text-blue-800' :
                  jobData.status === 'failed' ? 'bg-red-100 text-red-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {jobData.status}
                </span>
              </div>
              <div className="flex justify-between py-2 border-b">
                <span className="font-medium">Name:</span>
                <span>{jobData.name || 'N/A'}</span>
              </div>
              <div className="flex justify-between py-2 border-b">
                <span className="font-medium">Files:</span>
                <span>{jobData.num_files || 0}</span>
              </div>
              <div className="flex justify-between py-2 border-b">
                <span className="font-medium">Progress:</span>
                <span>{jobData.progress || 0}%</span>
              </div>
              {jobData.status !== 'completed' && (
                <div className="bg-yellow-50 border border-yellow-200 rounded p-4 mt-4">
                  <p className="text-yellow-800 font-medium">⚠️ Job not completed</p>
                  <p className="text-yellow-700 text-sm mt-1">
                    The 3D viewer requires a completed reconstruction. Current status: {jobData.status}
                  </p>
                </div>
              )}
            </div>
          ) : (
            <p className="text-gray-500">No job data available</p>
          )}
        </div>

        {/* Scene Data */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">2. Scene Data (COLMAP Output)</h2>
          {errors.scene ? (
            <div className="bg-red-50 border border-red-200 rounded p-4">
              <p className="text-red-800 font-medium">Error loading scene:</p>
              <p className="text-red-600 text-sm mt-1">{errors.scene}</p>
              <p className="text-red-600 text-sm mt-2">
                This usually means COLMAP reconstruction files are missing or not accessible.
              </p>
            </div>
          ) : sceneData ? (
            <div className="space-y-2">
              <div className="flex justify-between py-2 border-b">
                <span className="font-medium">Cameras:</span>
                <span>{sceneData.num_cameras || 0}</span>
              </div>
              <div className="flex justify-between py-2 border-b">
                <span className="font-medium">Images:</span>
                <span>{sceneData.num_images || 0}</span>
              </div>
              <div className="flex justify-between py-2 border-b">
                <span className="font-medium">3D Points:</span>
                <span>{sceneData.num_points || 0}</span>
              </div>
              {sceneData.num_points === 0 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded p-4 mt-4">
                  <p className="text-yellow-800 font-medium">⚠️ No 3D points found</p>
                  <p className="text-yellow-700 text-sm mt-1">
                    COLMAP reconstruction produced no 3D points. The scene might be empty or reconstruction failed.
                  </p>
                </div>
              )}
            </div>
          ) : (
            <p className="text-gray-500">No scene data available</p>
          )}
        </div>

        {/* Points Data */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">3. Gaussian Splat Data</h2>
          {errors.points ? (
            <div className="bg-red-50 border border-red-200 rounded p-4">
              <p className="text-red-800 font-medium">Error loading points:</p>
              <p className="text-red-600 text-sm mt-1">{errors.points}</p>
            </div>
          ) : pointsData ? (
            <div className="space-y-2">
              <div className="flex justify-between py-2 border-b">
                <span className="font-medium">Total Gaussians:</span>
                <span>{pointsData.num_gaussians || 0}</span>
              </div>
              <div className="flex justify-between py-2 border-b">
                <span className="font-medium">Sample (first 10):</span>
                <span>{pointsData.gaussians?.length || 0} loaded</span>
              </div>
              {pointsData.gaussians && pointsData.gaussians.length > 0 && (
                <div className="mt-4">
                  <p className="font-medium mb-2">First Gaussian:</p>
                  <pre className="bg-gray-50 p-3 rounded text-xs overflow-auto">
                    {JSON.stringify(pointsData.gaussians[0], null, 2)}
                  </pre>
                </div>
              )}
              {pointsData.num_gaussians > 0 && (
                <div className="bg-green-50 border border-green-200 rounded p-4 mt-4">
                  <p className="text-green-800 font-medium">✓ Data ready for visualization</p>
                  <p className="text-green-700 text-sm mt-1">
                    {pointsData.num_gaussians} Gaussian splats are available for rendering.
                  </p>
                </div>
              )}
            </div>
          ) : (
            <p className="text-gray-500">No points data available</p>
          )}
        </div>

        {/* Actions */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Actions</h2>
          <div className="space-y-3">
            <button
              onClick={loadDebugData}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Refresh Debug Data
            </button>
            {jobData?.status === 'completed' && pointsData?.num_gaussians > 0 && (
              <Link
                to={`/app/viewer/${id}`}
                className="block w-full px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-center"
              >
                Open 3D Viewer
              </Link>
            )}
            <Link
              to={`/app/jobs/${id}`}
              className="block w-full px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 text-center"
            >
              View Job Details
            </Link>
          </div>
        </div>

        {/* Troubleshooting */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4 text-blue-900">Troubleshooting</h2>
          <div className="space-y-3 text-sm text-blue-800">
            <div>
              <p className="font-medium">If job status is not "completed":</p>
              <p className="ml-4">→ Wait for the reconstruction to finish or check job logs for errors</p>
            </div>
            <div>
              <p className="font-medium">If scene data shows 0 points:</p>
              <p className="ml-4">→ COLMAP reconstruction failed or produced no output</p>
              <p className="ml-4">→ Check if COLMAP files exist in MinIO storage</p>
              <p className="ml-4">→ Verify input images are valid</p>
            </div>
            <div>
              <p className="font-medium">If API errors occur:</p>
              <p className="ml-4">→ Check backend server is running</p>
              <p className="ml-4">→ Verify MinIO connection</p>
              <p className="ml-4">→ Check browser console for detailed errors</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ViewerDebug
