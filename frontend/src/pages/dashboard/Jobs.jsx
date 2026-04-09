import { Link } from 'react-router-dom'
import { Cpu, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react'

function Jobs() {
  const jobs = [
    { id: '1', name: 'Office Scan Processing', status: 'running', progress: 65, created: '2 hours ago' },
    { id: '2', name: 'Product Demo Reconstruction', status: 'completed', progress: 100, created: '5 hours ago' },
    { id: '3', name: 'Room Scan Analysis', status: 'failed', progress: 45, created: '1 day ago' },
    { id: '4', name: 'Outdoor Scene Processing', status: 'queued', progress: 0, created: '3 hours ago' },
  ]

  const getStatusIcon = (status) => {
    switch (status) {
      case 'running': return <Cpu className="w-5 h-5 text-blue-600 animate-spin" />
      case 'completed': return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'failed': return <XCircle className="w-5 h-5 text-red-600" />
      case 'queued': return <Clock className="w-5 h-5 text-gray-600" />
      default: return <AlertCircle className="w-5 h-5 text-gray-600" />
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return 'bg-blue-100 text-blue-800'
      case 'completed': return 'bg-green-100 text-green-800'
      case 'failed': return 'bg-red-100 text-red-800'
      case 'queued': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Processing Jobs</h2>
          <p className="text-gray-600 mt-1">Monitor your reconstruction jobs</p>
        </div>
        <Link
          to="/app/upload"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          New Job
        </Link>
      </div>

      <div className="bg-white rounded-lg shadow divide-y divide-gray-200">
        {jobs.map((job) => (
          <Link
            key={job.id}
            to={`/app/jobs/${job.id}`}
            className="p-6 hover:bg-gray-50 block"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4 flex-1">
                {getStatusIcon(job.status)}
                <div className="flex-1">
                  <h3 className="font-medium text-gray-900">{job.name}</h3>
                  <p className="text-sm text-gray-500 mt-1">{job.created}</p>
                  {job.status === 'running' && (
                    <div className="mt-2">
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all"
                          style={{ width: `${job.progress}%` }}
                        ></div>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">{job.progress}% complete</p>
                    </div>
                  )}
                </div>
              </div>
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(job.status)}`}>
                {job.status}
              </span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}

export default Jobs
