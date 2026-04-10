import { useState, useEffect, useRef } from 'react'
import { jobsApi } from '../api/client'

function JobMonitor({ jobId, onClose }) {
  const [job, setJob] = useState(null)
  const [log, setLog] = useState('')
  const [autoScroll, setAutoScroll] = useState(true)
  const logRef = useRef(null)

  useEffect(() => {
    if (!jobId) return

    fetchJob()
    fetchLog()

    const interval = setInterval(() => {
      fetchJob()
      fetchLog()
    }, 2000)

    return () => clearInterval(interval)
  }, [jobId])

  useEffect(() => {
    if (autoScroll && logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight
    }
  }, [log, autoScroll])

  const fetchJob = async () => {
    try {
      const response = await jobsApi.getJob(jobId)
      setJob(response.data)
    } catch (error) {
      console.error('Failed to fetch job:', error)
    }
  }

  const fetchLog = async () => {
    try {
      const response = await jobsApi.getJobLog(jobId)
      setLog(response.data || '')
    } catch (error) {
      console.error('Failed to fetch log:', error)
    }
  }

  const handleStop = async () => {
    if (!confirm('Are you sure you want to stop this job?')) return
    
    try {
      await jobsApi.stopJob(jobId)
      fetchJob()
    } catch (error) {
      console.error('Failed to stop job:', error)
      alert('Failed to stop job: ' + (error.response?.data?.detail || error.message))
    }
  }

  const getProgressColor = (progress) => {
    if (progress < 0.3) return 'bg-blue-500'
    if (progress < 0.7) return 'bg-indigo-500'
    return 'bg-green-500'
  }

  if (!job) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-6xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold">{job.name || `Job ${jobId}`}</h2>
              <div className="flex items-center gap-2 mt-2">
                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                  job.status === 'processing' ? 'bg-blue-100 text-blue-800' :
                  job.status === 'completed' ? 'bg-green-100 text-green-800' :
                  job.status === 'failed' ? 'bg-red-100 text-red-800' :
                  job.status === 'stopped' ? 'bg-orange-100 text-orange-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {job.status}
                </span>
                {job.stage && (
                  <span className="text-sm text-gray-600">
                    {job.stage}
                  </span>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              {job.status === 'processing' && (
                <button
                  onClick={handleStop}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                >
                  Stop
                </button>
              )}
              <button
                onClick={onClose}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Close
              </button>
            </div>
          </div>

          {/* Progress Bar */}
          {job.progress !== undefined && (
            <div className="mt-4">
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Progress</span>
                <span>{Math.round(job.progress * 100)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all duration-500 ${getProgressColor(job.progress)}`}
                  style={{ width: `${job.progress * 100}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Log Viewer */}
        <div className="flex-1 p-6 overflow-hidden flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-700">Live Log</h3>
            <div className="flex items-center gap-3">
              <label className="flex items-center gap-2 text-sm text-gray-600">
                <input
                  type="checkbox"
                  checked={autoScroll}
                  onChange={(e) => setAutoScroll(e.target.checked)}
                  className="rounded"
                />
                Auto-scroll
              </label>
              {job.status === 'processing' && (
                <span className="flex items-center gap-2 text-sm text-green-600">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                  </span>
                  Live
                </span>
              )}
            </div>
          </div>
          <pre
            ref={logRef}
            className="flex-1 bg-gray-900 text-gray-100 p-4 rounded-lg overflow-auto text-xs font-mono whitespace-pre-wrap"
          >
            {log || 'Waiting for log output...'}
          </pre>
        </div>
      </div>
    </div>
  )
}

export default JobMonitor
