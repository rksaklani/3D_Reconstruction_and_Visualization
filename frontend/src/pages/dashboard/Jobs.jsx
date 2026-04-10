import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Cpu, Clock, CheckCircle, XCircle, AlertCircle, RefreshCw, Trash2, Play, Square, Eye, AlertTriangle } from 'lucide-react'
import { jobsApi } from '../../api/client'

function Jobs() {
  const navigate = useNavigate()
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filter, setFilter] = useState('all') // all, processing, completed, failed
  const [actionLoading, setActionLoading] = useState({})

  useEffect(() => {
    loadJobs()
  }, [filter]) // Only reload when filter changes

  useEffect(() => {
    // Auto-refresh every 5 seconds if there are active jobs
    const hasActiveJobs = jobs.some(j => j.status === 'processing' || j.status === 'queued')
    
    if (!hasActiveJobs) {
      return // No active jobs, no need to auto-refresh
    }

    const interval = setInterval(() => {
      loadJobs()
    }, 5000)
    
    return () => clearInterval(interval)
  }, [jobs]) // This effect depends on jobs to check for active jobs

  const loadJobs = async () => {
    try {
      setLoading(true)
      const params = filter !== 'all' ? { status: filter } : {}
      const response = await jobsApi.getJobs({ ...params, limit: 100 })
      setJobs(response.data.jobs || [])
      setError(null)
    } catch (err) {
      console.error('Failed to load jobs:', err)
      setError('Failed to load jobs')
    } finally {
      setLoading(false)
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'processing': return <Cpu className="w-5 h-5 text-blue-600 animate-pulse" />
      case 'completed': return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'failed': return <XCircle className="w-5 h-5 text-red-600" />
      case 'queued': return <Clock className="w-5 h-5 text-yellow-600" />
      default: return <AlertCircle className="w-5 h-5 text-gray-600" />
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'processing': return 'bg-blue-100 text-blue-800'
      case 'completed': return 'bg-green-100 text-green-800'
      case 'failed': return 'bg-red-100 text-red-800'
      case 'queued': return 'bg-yellow-100 text-yellow-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`
    if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`
    if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`
    return date.toLocaleDateString()
  }

  const handleDelete = async (e, jobId, jobName) => {
    e.preventDefault()
    e.stopPropagation()
    
    if (!confirm(`Are you sure you want to delete "${jobName}"? This action cannot be undone.`)) {
      return
    }

    setActionLoading(prev => ({ ...prev, [jobId]: 'deleting' }))
    try {
      await jobsApi.deleteJob(jobId)
      loadJobs()
    } catch (err) {
      console.error('Failed to delete job:', err)
      alert('Failed to delete job. Please try again.')
    } finally {
      setActionLoading(prev => {
        const newState = { ...prev }
        delete newState[jobId]
        return newState
      })
    }
  }

  const handleStart = async (e, jobId, jobName) => {
    e.preventDefault()
    e.stopPropagation()
    
    setActionLoading(prev => ({ ...prev, [jobId]: 'starting' }))
    try {
      await jobsApi.startProcessing(jobId)
      // Wait a moment then reload to see updated status
      setTimeout(() => {
        loadJobs()
        setActionLoading(prev => {
          const newState = { ...prev }
          delete newState[jobId]
          return newState
        })
      }, 1000)
    } catch (err) {
      console.error('Failed to start job:', err)
      alert('Failed to start job. Please try again.')
      setActionLoading(prev => {
        const newState = { ...prev }
        delete newState[jobId]
        return newState
      })
    }
  }

  const handleStop = async (e, jobId, jobName) => {
    e.preventDefault()
    e.stopPropagation()
    
    if (!confirm(`Are you sure you want to stop "${jobName}"?`)) {
      return
    }

    setActionLoading(prev => ({ ...prev, [jobId]: 'stopping' }))
    try {
      await jobsApi.stopJob(jobId)
      // Wait a moment then reload to see updated status
      setTimeout(() => {
        loadJobs()
        setActionLoading(prev => {
          const newState = { ...prev }
          delete newState[jobId]
          return newState
        })
      }, 1000)
    } catch (err) {
      console.error('Failed to stop job:', err)
      alert('Failed to stop job. Please try again.')
      setActionLoading(prev => {
        const newState = { ...prev }
        delete newState[jobId]
        return newState
      })
    }
  }

  const handleView = (e, jobId) => {
    e.preventDefault()
    e.stopPropagation()
    navigate(`/app/viewer/${jobId}`)
  }

  const filteredJobs = filter === 'all' 
    ? jobs 
    : jobs.filter(job => job.status === filter)

  if (loading && jobs.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Processing Jobs</h2>
          <p className="text-gray-600 mt-1">Monitor your reconstruction jobs</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={loadJobs}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg"
            title="Refresh"
          >
            <RefreshCw className="w-5 h-5" />
          </button>
          <Link
            to="/app/upload"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            New Job
          </Link>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex space-x-2 border-b border-gray-200">
        {['all', 'processing', 'completed', 'failed'].map((status) => (
          <button
            key={status}
            onClick={() => setFilter(status)}
            className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
              filter === status
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            {status.charAt(0).toUpperCase() + status.slice(1)}
            {status !== 'all' && (
              <span className="ml-2 px-2 py-0.5 bg-gray-100 rounded-full text-xs">
                {jobs.filter(j => j.status === status).length}
              </span>
            )}
          </button>
        ))}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {filteredJobs.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <Cpu className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No jobs found</h3>
          <p className="text-gray-600 mb-6">
            {filter === 'all' 
              ? 'Start by uploading images to create your first job'
              : `No ${filter} jobs at the moment`
            }
          </p>
          {filter === 'all' && (
            <Link
              to="/app/upload"
              className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Create First Job
            </Link>
          )}
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow divide-y divide-gray-200">
          {filteredJobs.map((job) => {
            const isLoading = actionLoading[job.job_id]
            const canStart = ['created', 'uploaded', 'failed'].includes(job.status)
            const canStop = ['processing', 'queued'].includes(job.status)
            const canView = job.status === 'completed'
            
            return (
              <div key={job.job_id} className="group relative">
                <Link
                  to={`/app/jobs/${job.job_id}`}
                  className="p-6 hover:bg-gray-50 block"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4 flex-1">
                      {getStatusIcon(job.status)}
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900">{job.name || 'Untitled Job'}</h3>
                        <p className="text-sm text-gray-500 mt-1">
                          {formatDate(job.created_at)}
                          {job.num_files > 0 && ` • ${job.num_files} files`}
                        </p>
                        {(job.status === 'processing' || job.status === 'queued') && (
                          <div className="mt-2">
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-blue-600 h-2 rounded-full transition-all"
                                style={{ width: `${job.progress || 0}%` }}
                              ></div>
                            </div>
                            <p className="text-xs text-gray-500 mt-1">
                              {Math.round(job.progress || 0)}% complete
                              {job.stage && ` • ${job.stage}`}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(job.status)}`}>
                        {job.status}
                      </span>
                      
                      {/* Warning for completed jobs without 3D data */}
                      {job.status === 'completed' && job.output_files?.sparse_warning && (
                        <div className="flex items-center space-x-1 text-yellow-600" title="No 3D reconstruction data">
                          <AlertTriangle className="w-4 h-4" />
                        </div>
                      )}
                      
                      {/* Action Buttons - visible on hover */}
                      <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        {/* View Button - for completed jobs with 3D data */}
                        {canView && !job.output_files?.sparse_warning && (
                          <button
                            onClick={(e) => handleView(e, job.job_id)}
                            className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                            title="View 3D Model"
                            disabled={isLoading}
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                        )}
                        
                        {/* Warning icon for completed jobs without 3D data */}
                        {canView && job.output_files?.sparse_warning && (
                          <div 
                            className="p-2 text-yellow-600"
                            title="No 3D reconstruction data available"
                          >
                            <AlertTriangle className="w-4 h-4" />
                          </div>
                        )}
                        
                        {/* Start Button - for created/uploaded/failed jobs */}
                        {canStart && (
                          <button
                            onClick={(e) => handleStart(e, job.job_id, job.name || 'Untitled Job')}
                            className="p-2 text-green-600 hover:bg-green-50 rounded-lg disabled:opacity-50"
                            title="Start Processing"
                            disabled={isLoading}
                          >
                            {isLoading === 'starting' ? (
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-green-600"></div>
                            ) : (
                              <Play className="w-4 h-4" />
                            )}
                          </button>
                        )}
                        
                        {/* Stop Button - for processing/queued jobs */}
                        {canStop && (
                          <button
                            onClick={(e) => handleStop(e, job.job_id, job.name || 'Untitled Job')}
                            className="p-2 text-orange-600 hover:bg-orange-50 rounded-lg disabled:opacity-50"
                            title="Stop Processing"
                            disabled={isLoading}
                          >
                            {isLoading === 'stopping' ? (
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-orange-600"></div>
                            ) : (
                              <Square className="w-4 h-4" />
                            )}
                          </button>
                        )}
                        
                        {/* Delete Button - always available */}
                        <button
                          onClick={(e) => handleDelete(e, job.job_id, job.name || 'Untitled Job')}
                          className="p-2 text-red-600 hover:bg-red-50 rounded-lg disabled:opacity-50"
                          title="Delete Job"
                          disabled={isLoading}
                        >
                          {isLoading === 'deleting' ? (
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-red-600"></div>
                          ) : (
                            <Trash2 className="w-4 h-4" />
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                </Link>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default Jobs
