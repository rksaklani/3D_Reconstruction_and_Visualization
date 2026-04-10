import { useState, useEffect } from 'react'
import { HardDrive, Image, Box, FileText, Trash2 } from 'lucide-react'
import { jobsApi } from '../../api/client'

function Storage() {
  const [storageData, setStorageData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadStorageData()
  }, [])

  const loadStorageData = async () => {
    try {
      setLoading(true)
      const response = await jobsApi.getJobs({ limit: 100 })
      const jobs = response.data.jobs || []
      
      // Calculate storage usage
      let totalSize = 0
      let imagesSize = 0
      let modelsSize = 0
      let exportsSize = 0
      
      jobs.forEach(job => {
        if (job.stats && job.stats.total_size) {
          totalSize += job.stats.total_size
          
          // Categorize by job status/type
          if (job.status === 'completed') {
            modelsSize += job.stats.total_size * 0.6 // Estimate 60% for models
            exportsSize += job.stats.total_size * 0.1 // Estimate 10% for exports
            imagesSize += job.stats.total_size * 0.3 // Estimate 30% for images
          } else {
            imagesSize += job.stats.total_size // All input images
          }
        }
      })
      
      setStorageData({
        total: 10 * 1024 * 1024 * 1024, // 10 GB total (hardcoded for now)
        used: totalSize,
        images: imagesSize,
        models: modelsSize,
        exports: exportsSize,
        jobs: jobs
      })
      setError(null)
    } catch (err) {
      console.error('Failed to load storage data:', err)
      setError('Failed to load storage data')
    } finally {
      setLoading(false)
    }
  }

  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i]
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
          onClick={loadStorageData}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    )
  }

  const percentage = (storageData.used / storageData.total) * 100

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Storage</h2>
        <p className="text-gray-600 mt-1">Manage your storage usage</p>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Storage Usage</h3>
          <span className="text-sm text-gray-600">
            {formatBytes(storageData.used)} / {formatBytes(storageData.total)}
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-4">
          <div
            className={`h-4 rounded-full transition-all ${
              percentage > 90 ? 'bg-red-600' : percentage > 70 ? 'bg-yellow-600' : 'bg-blue-600'
            }`}
            style={{ width: `${Math.min(percentage, 100)}%` }}
          ></div>
        </div>
        <p className="text-sm text-gray-600 mt-2">{percentage.toFixed(1)}% used</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <Image className="w-8 h-8 text-blue-600 mb-3" />
          <h3 className="font-semibold text-gray-900">Images</h3>
          <p className="text-2xl font-bold text-gray-900 mt-2">{formatBytes(storageData.images)}</p>
          <p className="text-sm text-gray-600 mt-1">Source images</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <Box className="w-8 h-8 text-purple-600 mb-3" />
          <h3 className="font-semibold text-gray-900">3D Models</h3>
          <p className="text-2xl font-bold text-gray-900 mt-2">{formatBytes(storageData.models)}</p>
          <p className="text-sm text-gray-600 mt-1">Generated models</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <FileText className="w-8 h-8 text-green-600 mb-3" />
          <h3 className="font-semibold text-gray-900">Exports</h3>
          <p className="text-2xl font-bold text-gray-900 mt-2">{formatBytes(storageData.exports)}</p>
          <p className="text-sm text-gray-600 mt-1">Exported files</p>
        </div>
      </div>

      {/* Storage by Job */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Storage by Project</h3>
        </div>
        <div className="divide-y divide-gray-200">
          {storageData.jobs
            .filter(job => job.stats && job.stats.total_size > 0)
            .sort((a, b) => (b.stats?.total_size || 0) - (a.stats?.total_size || 0))
            .slice(0, 10)
            .map((job) => (
              <div key={job.job_id} className="p-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{job.name || 'Untitled Project'}</p>
                    <p className="text-sm text-gray-500">{job.num_files || 0} files</p>
                  </div>
                  <div className="flex items-center space-x-4">
                    <span className="text-sm font-medium text-gray-900">
                      {formatBytes(job.stats?.total_size || 0)}
                    </span>
                    <button
                      className="p-2 text-red-600 hover:bg-red-50 rounded"
                      title="Delete project"
                      onClick={async () => {
                        if (confirm(`Delete project "${job.name}"?`)) {
                          try {
                            await jobsApi.deleteJob(job.job_id)
                            loadStorageData()
                          } catch (err) {
                            alert('Failed to delete project')
                          }
                        }
                      }}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
        </div>
      </div>
    </div>
  )
}

export default Storage
