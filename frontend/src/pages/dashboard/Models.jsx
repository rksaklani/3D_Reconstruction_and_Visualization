import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Box, Eye, Download, Calendar, FileText, Trash2 } from 'lucide-react'
import { jobsApi, reconstructionApi } from '../../api/client'

function Models() {
  const [models, setModels] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadModels()
  }, [])

  const loadModels = async () => {
    try {
      setLoading(true)
      // Get all completed jobs (these have models)
      const response = await jobsApi.getJobs({ status: 'completed', limit: 100 })
      setModels(response.data.jobs || [])
      setError(null)
    } catch (err) {
      console.error('Failed to load models:', err)
      setError('Failed to load models')
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString()
  }

  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return 'N/A'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
  }

  const getModelType = (job) => {
    // Determine model type based on output files
    if (job.output_files) {
      if (job.output_files.gaussian_splat) return 'gaussian'
      if (job.output_files.mesh) return 'mesh'
      if (job.output_files.point_cloud) return 'pointcloud'
    }
    return 'reconstruction'
  }

  const getTypeColor = (type) => {
    switch (type) {
      case 'gaussian': return 'bg-blue-100 text-blue-800'
      case 'mesh': return 'bg-purple-100 text-purple-800'
      case 'pointcloud': return 'bg-green-100 text-green-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const handleDownload = async (jobId, e) => {
    e.preventDefault()
    e.stopPropagation()
    
    try {
      const response = await reconstructionApi.downloadPly(jobId)
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `model_${jobId}.ply`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Failed to download model:', err)
      alert('Failed to download model')
    }
  }

  const handleDelete = async (e, modelId, modelName) => {
    e.preventDefault()
    e.stopPropagation()
    
    if (!confirm(`Are you sure you want to delete "${modelName}"? This will delete all associated files and cannot be undone.`)) {
      return
    }

    try {
      await jobsApi.deleteJob(modelId)
      // Reload models after deletion
      loadModels()
    } catch (err) {
      console.error('Failed to delete model:', err)
      alert('Failed to delete model. Please try again.')
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
          onClick={loadModels}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">3D Models</h2>
        <p className="text-gray-600 mt-1">Browse and manage your 3D models</p>
      </div>

      {models.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <Box className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No models yet</h3>
          <p className="text-gray-600 mb-6">Complete a reconstruction job to generate your first 3D model</p>
          <Link
            to="/app/upload"
            className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Start Reconstruction
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {models.map((model) => {
            const modelType = getModelType(model)
            return (
              <div key={model.job_id} className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow relative group">
                <div className="h-48 bg-gradient-to-br from-gray-700 to-gray-900 rounded-t-lg flex items-center justify-center relative">
                  <Box className="w-16 h-16 text-white opacity-50" />
                  {/* Delete button - shows on hover */}
                  <button
                    onClick={(e) => handleDelete(e, model.job_id, model.name || 'Untitled Model')}
                    className="absolute top-3 right-3 p-2 bg-red-600 text-white rounded-lg opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-700 z-10"
                    title="Delete model"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                <div className="p-4">
                  <h3 className="font-semibold text-gray-900">{model.name || 'Untitled Model'}</h3>
                  {model.description && (
                    <p className="text-sm text-gray-600 mt-1 line-clamp-2">{model.description}</p>
                  )}
                  <div className="mt-2 space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Files</span>
                      <span className="font-medium text-gray-900">{model.num_files || 0}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Size</span>
                      <span className="font-medium text-gray-900">
                        {formatBytes(model.stats?.total_size)}
                      </span>
                    </div>
                    <div className="flex items-center text-sm text-gray-600">
                      <Calendar className="w-4 h-4 mr-2" />
                      <span>{formatDate(model.completed_at || model.created_at)}</span>
                    </div>
                  </div>
                  <div className="mt-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getTypeColor(modelType)}`}>
                      {modelType}
                    </span>
                  </div>
                  <div className="mt-4 flex space-x-2">
                    <Link
                      to={`/app/viewer/${model.job_id}`}
                      className="flex-1 flex items-center justify-center space-x-1 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
                    >
                      <Eye className="w-4 h-4" />
                      <span>View</span>
                    </Link>
                    <button 
                      onClick={(e) => handleDownload(model.job_id, e)}
                      className="flex items-center justify-center px-3 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                      title="Download PLY"
                    >
                      <Download className="w-4 h-4" />
                    </button>
                    <Link
                      to={`/app/jobs/${model.job_id}`}
                      className="flex items-center justify-center px-3 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                      title="View Details"
                    >
                      <FileText className="w-4 h-4" />
                    </Link>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default Models
