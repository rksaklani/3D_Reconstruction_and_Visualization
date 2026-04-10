import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { jobsApi } from '../api/client'

function JobDetail() {
  const { id } = useParams()  // Changed from jobId to id to match route
  const [job, setJob] = useState(null)
  const [log, setLog] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) {
      console.error('No job ID provided')
      setLoading(false)
      return
    }
    
    fetchJob()
    fetchLog()
    
    const interval = setInterval(() => {
      fetchJob()
      fetchLog()
    }, 2000)
    
    return () => clearInterval(interval)
  }, [id])

  const fetchJob = async () => {
    try {
      const response = await jobsApi.getJob(id)
      setJob(response.data)
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch job:', error)
      setLoading(false)
    }
  }

  const fetchLog = async () => {
    try {
      const response = await jobsApi.getJobLog(id)
      // The new endpoint returns plain text directly
      setLog(response.data || '')
    } catch (error) {
      console.error('Failed to fetch log:', error)
      // Don't show error if log doesn't exist yet
      if (error.response?.status !== 404) {
        setLog('Error loading log: ' + error.message)
      }
    }
  }

  const handleStartProcessing = async () => {
    try {
      await jobsApi.startProcessing(id)
      fetchJob()
    } catch (error) {
      console.error('Failed to start processing:', error)
      alert('Failed to start processing: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleStop = async () => {
    try {
      await jobsApi.stopJob(id)  // Changed from jobId to id
      fetchJob()
    } catch (error) {
      console.error('Failed to stop job:', error)
      alert('Failed to stop job: ' + (error.response?.data?.detail || error.message))
    }
  }

  const getStateColor = (state) => {
    switch (state) {
      case 'processing': return 'bg-blue-100 text-blue-800'
      case 'completed': return 'bg-green-100 text-green-800'
      case 'failed': return 'bg-red-100 text-red-800'
      case 'stopped': return 'bg-orange-100 text-orange-800'
      case 'uploaded': return 'bg-purple-100 text-purple-800'
      case 'created': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getStageDisplay = (stage) => {
    const stageNames = {
      'preprocessing': 'Preprocessing',
      'sfm': 'Structure from Motion',
      'ai_analysis': 'AI Scene Understanding',
      'gaussian_training': 'Gaussian Splatting',
      'export': 'Export',
      'complete': 'Complete',
      'initializing': 'Initializing'
    }
    return stageNames[stage] || stage
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">Loading job...</div>
      </div>
    )
  }

  if (!job) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-gray-500 mb-4">Job not found</div>
          <Link to="/" className="text-blue-600 hover:underline">
            Back to home
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Job Info Card */}
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold mb-2">{job.name || `Job ${id}`}</h1>
              <div className="flex items-center gap-3 text-sm text-gray-600">
                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStateColor(job.status)}`}>
                  {job.status}
                </span>
                {job.stage && (
                  <span className="px-3 py-1 bg-gray-100 rounded-full text-xs font-semibold">
                    {getStageDisplay(job.stage)}
                  </span>
                )}
                {job.progress !== undefined && job.progress > 0 && (
                  <span className="px-3 py-1 bg-blue-50 rounded-full text-xs font-semibold text-blue-700">
                    {Math.round(job.progress * 100)}%
                  </span>
                )}
                {job.pid && (
                  <span className="px-3 py-1 bg-gray-100 rounded-full text-xs font-mono">
                    PID: {job.pid}
                  </span>
                )}
              </div>
            </div>

            <div className="flex gap-3">
              <Link
                to="/app/jobs"
                className="px-6 py-2 border border-gray-800 rounded-lg hover:bg-gray-50"
              >
                Back
              </Link>
              {job.status === 'completed' && (
                <Link
                  to={`/viewer/${job.job_id}`}
                  className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                >
                  View 3D
                </Link>
              )}
              {job.status === 'uploaded' && (
                <button
                  onClick={() => handleStartProcessing()}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Start Processing
                </button>
              )}
              {job.status === 'processing' && (
                <button
                  onClick={handleStop}
                  className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                >
                  Stop Processing
                </button>
              )}
            </div>
          </div>

          {/* Job Details */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="font-semibold text-gray-700">Input Type:</span>
              <p className="text-gray-600">{job.input_type || 'N/A'}</p>
            </div>
            <div>
              <span className="font-semibold text-gray-700">Files:</span>
              <p className="text-gray-600">{job.num_files || 0}</p>
            </div>
            <div>
              <span className="font-semibold text-gray-700">Created:</span>
              <p className="text-gray-600">{new Date(job.created_at).toLocaleString()}</p>
            </div>
            <div>
              <span className="font-semibold text-gray-700">Updated:</span>
              <p className="text-gray-600">{new Date(job.updated_at).toLocaleString()}</p>
            </div>
          </div>

          {/* Error Display */}
          {job.error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <h3 className="font-semibold text-red-800 mb-2">Error</h3>
              <p className="text-red-700 text-sm">{job.error}</p>
              {job.error_details && (
                <details className="mt-2">
                  <summary className="cursor-pointer text-red-600 text-xs hover:text-red-800">
                    Show details
                  </summary>
                  <pre className="mt-2 p-2 bg-red-100 rounded text-xs overflow-auto max-h-40">
                    {job.error_details}
                  </pre>
                </details>
              )}
            </div>
          )}

          {/* Configuration */}
          {job.config && (
            <details className="mt-4">
              <summary className="cursor-pointer font-semibold text-gray-700 hover:text-gray-900">
                Configuration
              </summary>
              <div className="mt-2 p-3 bg-gray-50 rounded-lg text-xs">
                <div className="grid grid-cols-2 gap-2">
                  <div><span className="font-semibold">Workspace:</span> {job.config.workspace}</div>
                  <div><span className="font-semibold">GS Repo:</span> {job.config.gs_repo}</div>
                  <div><span className="font-semibold">Matcher:</span> {job.config.matcher}</div>
                  <div><span className="font-semibold">FPS:</span> {job.config.fps}</div>
                  <div><span className="font-semibold">Overlap:</span> {job.config.overlap}</div>
                  <div><span className="font-semibold">Iterations:</span> {job.config.gs_iterations}</div>
                </div>
              </div>
            </details>
          )}
        </div>

        {/* Log Card */}
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold">Real-Time Processing Log</h2>
            <div className="flex items-center gap-2">
              {job.status === 'processing' && (
                <span className="flex items-center gap-2 text-sm text-blue-600">
                  <span className="relative flex h-3 w-3">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-500"></span>
                  </span>
                  Live
                </span>
              )}
              <button
                onClick={fetchLog}
                className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50"
              >
                Refresh
              </button>
            </div>
          </div>
          <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-auto max-h-[70vh] text-sm font-mono whitespace-pre-wrap">
            {log || (job.status === 'processing' ? 'Waiting for log output...' : 'No log available')}
          </pre>
        </div>
      </div>
    </div>
  )
}

export default JobDetail
