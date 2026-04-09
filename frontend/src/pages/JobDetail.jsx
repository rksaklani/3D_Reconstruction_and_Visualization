import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { jobsApi } from '../api/client'

function JobDetail() {
  const { jobId } = useParams()
  const navigate = useNavigate()
  const [job, setJob] = useState(null)
  const [log, setLog] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchJob()
    fetchLog()
    
    const interval = setInterval(() => {
      fetchJob()
      fetchLog()
    }, 2000)
    
    return () => clearInterval(interval)
  }, [jobId])

  const fetchJob = async () => {
    try {
      const response = await jobsApi.getJob(jobId)
      // Parse HTML to extract job data
      const parser = new DOMParser()
      const doc = parser.parseFromString(response.data, 'text/html')
      
      const jobData = {
        id: jobId,
        state: doc.querySelector('[data-state]')?.dataset.state || 'unknown',
        pid: doc.querySelector('[data-pid]')?.dataset.pid,
        returncode: doc.querySelector('[data-rc]')?.dataset.rc,
        workspace: doc.querySelector('.workspace')?.textContent,
        video: doc.querySelector('.video')?.textContent,
        images_dir: doc.querySelector('.images-dir')?.textContent,
        iterations: doc.querySelector('.iterations')?.textContent,
        matcher: doc.querySelector('.matcher')?.textContent,
        overlap: doc.querySelector('.overlap')?.textContent,
        command: doc.querySelector('.command')?.textContent,
      }
      
      setJob(jobData)
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch job:', error)
      setLoading(false)
    }
  }

  const fetchLog = async () => {
    try {
      const response = await jobsApi.getJobLog(jobId)
      setLog(response.data)
    } catch (error) {
      console.error('Failed to fetch log:', error)
    }
  }

  const handleStop = async () => {
    try {
      await jobsApi.stopJob(jobId)
      fetchJob()
    } catch (error) {
      console.error('Failed to stop job:', error)
      alert('Failed to stop job: ' + (error.response?.data?.detail || error.message))
    }
  }

  const getStateColor = (state) => {
    switch (state) {
      case 'running': return 'bg-blue-100 text-blue-800'
      case 'done': return 'bg-green-100 text-green-800'
      case 'error': return 'bg-red-100 text-red-800'
      case 'stopped': return 'bg-gray-100 text-gray-800'
      case 'queued': return 'bg-yellow-100 text-yellow-800'
      default: return 'bg-gray-100 text-gray-800'
    }
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
              <h1 className="text-2xl font-bold mb-2">Job {jobId}</h1>
              <div className="flex items-center gap-3 text-sm text-gray-600">
                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStateColor(job.state)}`}>
                  {job.state}
                </span>
                {job.pid && <span>PID: {job.pid}</span>}
                {job.returncode !== undefined && <span>RC: {job.returncode}</span>}
              </div>
            </div>

            <div className="flex gap-3">
              <Link
                to="/"
                className="px-6 py-2 border border-gray-800 rounded-lg hover:bg-gray-50"
              >
                Back
              </Link>
              <button
                onClick={handleStop}
                className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
              >
                Stop
              </button>
            </div>
          </div>

          {/* Job Details */}
          <div className="space-y-2 text-sm">
            {job.workspace && (
              <div className="text-gray-600">
                <span className="font-semibold">Workspace:</span> {job.workspace}
              </div>
            )}
            {job.video && (
              <div className="text-gray-600">
                <span className="font-semibold">Video:</span> {job.video}
              </div>
            )}
            {job.images_dir && (
              <div className="text-gray-600">
                <span className="font-semibold">Images dir:</span> {job.images_dir}
              </div>
            )}
            {job.iterations && (
              <div className="text-gray-600">
                <span className="font-semibold">Iterations:</span> {job.iterations}
              </div>
            )}
            {job.matcher && (
              <div className="text-gray-600">
                <span className="font-semibold">Matcher:</span> {job.matcher}
                {job.overlap && ` (overlap=${job.overlap})`}
              </div>
            )}
          </div>

          {/* Command */}
          {job.command && (
            <details className="mt-4">
              <summary className="cursor-pointer font-semibold text-gray-700 hover:text-gray-900">
                Command
              </summary>
              <div className="mt-2 p-3 bg-gray-50 rounded-lg text-xs font-mono text-gray-700 overflow-x-auto">
                {job.command}
              </div>
            </details>
          )}
        </div>

        {/* Log Card */}
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h2 className="text-lg font-bold mb-4">Live log</h2>
          <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-auto max-h-[70vh] text-sm font-mono whitespace-pre-wrap">
            {log || 'No log output yet...'}
          </pre>
        </div>
      </div>
    </div>
  )
}

export default JobDetail
