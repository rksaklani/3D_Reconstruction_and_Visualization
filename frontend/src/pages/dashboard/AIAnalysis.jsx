import { useState, useEffect } from 'react'
import { Zap, Target, Layers, Activity, AlertCircle } from 'lucide-react'
import { jobsApi } from '../../api/client'

function AIAnalysis() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadJobs()
  }, [])

  const loadJobs = async () => {
    try {
      setLoading(true)
      const response = await jobsApi.getJobs({ limit: 100 })
      setJobs(response.data.jobs || [])
      setError(null)
    } catch (err) {
      console.error('Failed to load jobs:', err)
      setError('Failed to load AI analysis data')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <p className="text-red-800">{error}</p>
        <button
          onClick={loadJobs}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    )
  }

  // Calculate stats from jobs
  const completedJobs = jobs.filter(j => j.status === 'completed')
  const totalObjects = completedJobs.reduce((sum, job) => sum + (job.num_files || 0), 0)

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">AI Analysis</h2>
        <p className="text-gray-600 mt-1">View AI-powered insights from your reconstructions</p>
      </div>

      {/* Info Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start space-x-3">
        <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5" />
        <div>
          <p className="text-sm font-medium text-blue-900">AI Features Coming Soon</p>
          <p className="text-sm text-blue-700 mt-1">
            Advanced AI analysis features including object detection, segmentation, and tracking are currently in development.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <Target className="w-8 h-8 text-blue-600 mb-3" />
          <h3 className="font-semibold text-gray-900">Object Detection</h3>
          <p className="text-sm text-gray-600 mt-1">YOLO-based detection</p>
          <p className="text-2xl font-bold text-gray-900 mt-3">{totalObjects} objects</p>
          <p className="text-xs text-gray-500 mt-1">From {completedJobs.length} projects</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <Layers className="w-8 h-8 text-purple-600 mb-3" />
          <h3 className="font-semibold text-gray-900">Segmentation</h3>
          <p className="text-sm text-gray-600 mt-1">SAM segmentation</p>
          <p className="text-2xl font-bold text-gray-900 mt-3">Coming Soon</p>
          <p className="text-xs text-gray-500 mt-1">In development</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <Activity className="w-8 h-8 text-green-600 mb-3" />
          <h3 className="font-semibold text-gray-900">Tracking</h3>
          <p className="text-sm text-gray-600 mt-1">Object tracking</p>
          <p className="text-2xl font-bold text-gray-900 mt-3">Coming Soon</p>
          <p className="text-xs text-gray-500 mt-1">In development</p>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Recent Projects</h3>
        </div>
        {completedJobs.length === 0 ? (
          <div className="p-12 text-center">
            <Zap className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No completed projects</h3>
            <p className="text-gray-600">Complete a reconstruction to see AI analysis</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {completedJobs.slice(0, 10).map((job) => (
              <div key={job.job_id} className="p-6 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-gray-900">{job.name || 'Untitled Project'}</h4>
                    <p className="text-sm text-gray-600 mt-1">
                      {job.num_files || 0} files processed
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-600">Status</p>
                    <p className="text-lg font-semibold text-green-600">Completed</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Feature Roadmap */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Upcoming AI Features</h3>
        <div className="space-y-3">
          <div className="flex items-start space-x-3">
            <div className="w-2 h-2 bg-blue-600 rounded-full mt-2"></div>
            <div>
              <p className="font-medium text-gray-900">YOLO Object Detection</p>
              <p className="text-sm text-gray-600">Automatic detection and classification of objects in scenes</p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <div className="w-2 h-2 bg-purple-600 rounded-full mt-2"></div>
            <div>
              <p className="font-medium text-gray-900">SAM Segmentation</p>
              <p className="text-sm text-gray-600">Precise segmentation of scene elements</p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <div className="w-2 h-2 bg-green-600 rounded-full mt-2"></div>
            <div>
              <p className="font-medium text-gray-900">Object Tracking</p>
              <p className="text-sm text-gray-600">Track objects across multiple frames</p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <div className="w-2 h-2 bg-orange-600 rounded-full mt-2"></div>
            <div>
              <p className="font-medium text-gray-900">Scene Classification</p>
              <p className="text-sm text-gray-600">Automatic scene type detection and categorization</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AIAnalysis
