import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Image, Cpu, Box, Download, Eye, Calendar } from 'lucide-react'
import { jobsApi, reconstructionApi } from '../../api/client'

function ProjectDetail() {
  const { id } = useParams()
  const [project, setProject] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadProject()
  }, [id])

  const loadProject = async () => {
    try {
      setLoading(true)
      const response = await jobsApi.getJob(id)
      setProject(response.data)
      setError(null)
    } catch (err) {
      console.error('Failed to load project:', err)
      setError('Failed to load project')
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async () => {
    try {
      const response = await reconstructionApi.downloadPly(id)
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${project.name || 'model'}_${id}.ply`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Failed to download:', err)
      alert('Failed to download model')
    }
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error || !project) {
    return (
      <div className="space-y-6">
        <Link to="/app/projects" className="flex items-center text-blue-600 hover:text-blue-700">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Projects
        </Link>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <p className="text-red-800">{error || 'Project not found'}</p>
          <button
            onClick={loadProject}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <Link to="/app/projects" className="flex items-center text-blue-600 hover:text-blue-700">
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Projects
      </Link>

      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{project.name || 'Untitled Project'}</h2>
            {project.description && (
              <p className="text-gray-600 mt-1">{project.description}</p>
            )}
            <div className="flex items-center text-sm text-gray-500 mt-2">
              <Calendar className="w-4 h-4 mr-1" />
              <span>Created {formatDate(project.created_at)}</span>
            </div>
          </div>
          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
            project.status === 'completed' ? 'bg-green-100 text-green-800' :
            project.status === 'processing' ? 'bg-blue-100 text-blue-800' :
            project.status === 'failed' ? 'bg-red-100 text-red-800' :
            'bg-gray-100 text-gray-800'
          }`}>
            {project.status}
          </span>
        </div>

        <div className="grid grid-cols-3 gap-4 mt-6">
          <div className="p-4 bg-gray-50 rounded-lg">
            <Image className="w-6 h-6 text-gray-600 mb-2" />
            <p className="text-sm text-gray-600">Files</p>
            <p className="text-2xl font-bold text-gray-900">{project.num_files || 0}</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <Cpu className="w-6 h-6 text-gray-600 mb-2" />
            <p className="text-sm text-gray-600">Progress</p>
            <p className="text-2xl font-bold text-gray-900">{Math.round(project.progress || 0)}%</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <Box className="w-6 h-6 text-gray-600 mb-2" />
            <p className="text-sm text-gray-600">Stage</p>
            <p className="text-lg font-bold text-gray-900">{project.stage || 'N/A'}</p>
          </div>
        </div>

        {project.status === 'completed' && (
          <div className="mt-6 flex space-x-4">
            {project.output_files?.sparse_warning ? (
              <div className="flex-1 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-yellow-800 font-medium">⚠️ No 3D Reconstruction Data</p>
                <p className="text-yellow-700 text-sm mt-1">
                  COLMAP reconstruction did not generate 3D points. The 3D viewer will not work for this job.
                </p>
                <p className="text-yellow-600 text-xs mt-2">
                  This can happen if the video has insufficient features, poor lighting, or not enough camera movement.
                </p>
              </div>
            ) : (
              <>
                <Link
                  to={`/app/viewer/${id}`}
                  className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  <Eye className="w-5 h-5" />
                  <span>View 3D Model</span>
                </Link>
                <button
                  onClick={handleDownload}
                  className="flex items-center space-x-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  <Download className="w-5 h-5" />
                  <span>Download PLY</span>
                </button>
              </>
            )}
          </div>
        )}

        {project.status === 'processing' && (
          <div className="mt-6">
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className="bg-blue-600 h-3 rounded-full transition-all"
                style={{ width: `${project.progress || 0}%` }}
              ></div>
            </div>
            <p className="text-sm text-gray-600 mt-2">
              Processing: {project.stage || 'Starting...'}
            </p>
          </div>
        )}

        {project.status === 'failed' && project.error && (
          <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-sm font-medium text-red-800">Error:</p>
            <p className="text-sm text-red-700 mt-1">{project.error}</p>
          </div>
        )}
      </div>

      {/* Configuration Details */}
      {project.config && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Configuration</h3>
          <div className="grid grid-cols-2 gap-4">
            {Object.entries(project.config).slice(0, 8).map(([key, value]) => (
              <div key={key} className="flex justify-between py-2 border-b border-gray-100">
                <span className="text-sm text-gray-600">{key.replace(/_/g, ' ')}</span>
                <span className="text-sm font-medium text-gray-900">
                  {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* View Full Details */}
      <div className="bg-white rounded-lg shadow p-6">
        <Link
          to={`/app/jobs/${id}`}
          className="text-blue-600 hover:text-blue-700 font-medium"
        >
          View Full Job Details →
        </Link>
      </div>
    </div>
  )
}

export default ProjectDetail
