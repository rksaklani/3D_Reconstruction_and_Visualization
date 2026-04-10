import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { jobsApi } from '../api/client'
import JobMonitor from './JobMonitor'

function JobList() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedJob, setSelectedJob] = useState(null)

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const response = await jobsApi.getJobs()
        setJobs(response.data.jobs || [])
      } catch (error) {
        console.error('Failed to fetch jobs:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchJobs()
    const interval = setInterval(fetchJobs, 3000)
    return () => clearInterval(interval)
  }, [])

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

  const handleMonitor = (e, jobId) => {
    e.preventDefault()
    setSelectedJob(jobId)
  }

  if (loading) {
    return <div className="text-center py-8 text-gray-500">Loading jobs...</div>
  }

  if (jobs.length === 0) {
    return <div className="text-center py-8 text-gray-500">No jobs yet</div>
  }

  return (
    <>
      <div className="space-y-3">
        {jobs.map(job => (
          <div
            key={job.job_id}
            className="block p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:shadow-md transition"
          >
            <div className="flex items-center justify-between mb-2">
              <Link to={`/job/${job.job_id}`} className="font-semibold text-gray-800 hover:text-blue-600">
                {job.name || job.job_id}
              </Link>
              <div className="flex items-center gap-2">
                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStateColor(job.status)}`}>
                  {job.status}
                </span>
                {job.status === 'completed' && (
                  <Link
                    to={`/viewer/${job.job_id}`}
                    className="px-3 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700"
                  >
                    View 3D
                  </Link>
                )}
                {job.status === 'processing' && (
                  <button
                    onClick={(e) => handleMonitor(e, job.job_id)}
                    className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
                  >
                    Monitor
                  </button>
                )}
              </div>
            </div>
            <div className="flex items-center gap-4 text-sm text-gray-600">
              {job.stage && <span>Stage: {job.stage}</span>}
              {job.progress !== undefined && job.progress > 0 && (
                <span>{Math.round(job.progress * 100)}%</span>
              )}
              {job.num_files > 0 && <span>{job.num_files} files</span>}
            </div>
            {job.created_at && (
              <div className="text-xs text-gray-400 mt-1">
                Created: {new Date(job.created_at).toLocaleString()}
              </div>
            )}
          </div>
        ))}
      </div>

      {selectedJob && (
        <JobMonitor
          jobId={selectedJob}
          onClose={() => setSelectedJob(null)}
        />
      )}
    </>
  )
}

export default JobList
