import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { jobsApi } from '../api/client'

function JobList() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const response = await jobsApi.getJobs()
        // Parse HTML response to extract job data
        const parser = new DOMParser()
        const doc = parser.parseFromString(response.data, 'text/html')
        const jobElements = doc.querySelectorAll('.job-item')
        
        const jobsData = Array.from(jobElements).map(el => ({
          id: el.dataset.jobId,
          state: el.dataset.state,
          workspace: el.querySelector('.workspace')?.textContent,
          created: el.querySelector('.created')?.textContent,
        }))
        
        setJobs(jobsData)
      } catch (error) {
        console.error('Failed to fetch jobs:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchJobs()
    const interval = setInterval(fetchJobs, 2000)
    return () => clearInterval(interval)
  }, [])

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
    return <div className="text-center py-8 text-gray-500">Loading jobs...</div>
  }

  if (jobs.length === 0) {
    return <div className="text-center py-8 text-gray-500">No jobs yet</div>
  }

  return (
    <div className="space-y-3">
      {jobs.map(job => (
        <Link
          key={job.id}
          to={`/job/${job.id}`}
          className="block p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:shadow-md transition"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="font-mono text-sm text-gray-600">{job.id}</span>
            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStateColor(job.state)}`}>
              {job.state}
            </span>
          </div>
          {job.workspace && (
            <div className="text-sm text-gray-600 truncate">{job.workspace}</div>
          )}
          {job.created && (
            <div className="text-xs text-gray-400 mt-1">{job.created}</div>
          )}
        </Link>
      ))}
    </div>
  )
}

export default JobList
