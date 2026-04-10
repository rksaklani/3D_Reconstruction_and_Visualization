import { useState, useEffect } from 'react'
import { Download, FileText, Package } from 'lucide-react'
import { jobsApi, reconstructionApi } from '../../api/client'

function Exports() {
  const [exports, setExports] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadExports()
  }, [])

  const loadExports = async () => {
    try {
      setLoading(true)
      const response = await jobsApi.getJobs({ status: 'completed', limit: 100 })
      setExports(response.data.jobs || [])
      setError(null)
    } catch (err) {
      console.error('Failed to load exports:', err)
      setError('Failed to load exports')
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async (jobId, jobName, format = 'ply') => {
    try {
      const response = await reconstructionApi.downloadPly(jobId)
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${jobName || 'model'}_${jobId}.${format}`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Failed to download:', err)
      alert('Failed to download file')
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
          onClick={loadExports}
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
        <h2 className="text-2xl font-bold text-gray-900">Exports</h2>
        <p className="text-gray-600 mt-1">Download your 3D models in various formats</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <Package className="w-8 h-8 text-blue-600 mb-3" />
          <h3 className="font-semibold text-gray-900">GLB/GLTF</h3>
          <p className="text-sm text-gray-600 mt-1">Web-optimized format</p>
          <p className="text-xs text-gray-500 mt-2">Coming soon</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <FileText className="w-8 h-8 text-purple-600 mb-3" />
          <h3 className="font-semibold text-gray-900">OBJ</h3>
          <p className="text-sm text-gray-600 mt-1">Universal 3D format</p>
          <p className="text-xs text-gray-500 mt-2">Coming soon</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <Package className="w-8 h-8 text-green-600 mb-3" />
          <h3 className="font-semibold text-gray-900">PLY</h3>
          <p className="text-sm text-gray-600 mt-1">Point cloud format</p>
          <p className="text-xs text-green-600 mt-2">Available now</p>
        </div>
      </div>

      {exports.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <Download className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No exports available</h3>
          <p className="text-gray-600">Complete a reconstruction to generate exportable models</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Available Exports</h3>
          </div>
          <div className="divide-y divide-gray-200">
            {exports.map((exp) => (
              <div key={exp.job_id} className="p-6 hover:bg-gray-50 flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-gray-900">{exp.name || 'Untitled Project'}</h4>
                  <p className="text-sm text-gray-600 mt-1">
                    {formatBytes(exp.stats?.total_size)} • {formatDate(exp.completed_at || exp.created_at)}
                  </p>
                  {exp.description && (
                    <p className="text-sm text-gray-500 mt-1">{exp.description}</p>
                  )}
                </div>
                <div className="flex space-x-2">
                  <button 
                    onClick={() => handleDownload(exp.job_id, exp.name, 'ply')}
                    className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    <Download className="w-4 h-4" />
                    <span>PLY</span>
                  </button>
                  <button 
                    disabled
                    className="flex items-center space-x-2 px-4 py-2 bg-gray-200 text-gray-500 rounded-lg cursor-not-allowed"
                    title="Coming soon"
                  >
                    <Download className="w-4 h-4" />
                    <span>OBJ</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default Exports
