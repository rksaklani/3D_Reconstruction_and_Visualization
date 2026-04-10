import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { FolderOpen, Upload, Cpu, Box, TrendingUp, Clock } from 'lucide-react'
import { statsApi } from '../../api/client'

function Dashboard() {
  const [stats, setStats] = useState(null)
  const [recentProjects, setRecentProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      const [dashboardStats, recent] = await Promise.all([
        statsApi.getDashboardStats(),
        statsApi.getRecentProjects(5)
      ])
      
      setStats(dashboardStats)
      setRecentProjects(recent)
      setError(null)
    } catch (err) {
      console.error('Failed to load dashboard data:', err)
      setError('Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
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
          onClick={loadDashboardData}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    )
  }

  const dashboardStats = [
    { 
      name: 'Total Projects', 
      value: stats?.totalProjects || 0, 
      icon: FolderOpen, 
      color: 'blue' 
    },
    { 
      name: 'Active Jobs', 
      value: stats?.activeJobs || 0, 
      icon: Cpu, 
      color: 'purple' 
    },
    { 
      name: '3D Models', 
      value: stats?.totalModels || 0, 
      icon: Box, 
      color: 'green' 
    },
    { 
      name: 'Storage Used', 
      value: formatBytes(stats?.storageUsed || 0), 
      icon: TrendingUp, 
      color: 'orange' 
    },
  ]

  return (
    <div className="space-y-6">
      {/* Welcome */}
      <div>
        <h2 className="text-3xl font-bold text-gray-900">Welcome back!</h2>
        <p className="text-gray-600 mt-1">Here's what's happening with your projects</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {dashboardStats.map((stat) => {
          const Icon = stat.icon
          return (
            <div key={stat.name} className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">{stat.name}</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">{stat.value}</p>
                </div>
                <div className={`w-12 h-12 bg-${stat.color}-100 rounded-lg flex items-center justify-center`}>
                  <Icon className={`w-6 h-6 text-${stat.color}-600`} />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/app/upload"
            className="flex items-center space-x-3 p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
          >
            <Upload className="w-6 h-6 text-blue-600" />
            <div>
              <p className="font-medium text-gray-900">Upload Images</p>
              <p className="text-sm text-gray-500">Start new reconstruction</p>
            </div>
          </Link>

          <Link
            to="/app/projects"
            className="flex items-center space-x-3 p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-colors"
          >
            <FolderOpen className="w-6 h-6 text-purple-600" />
            <div>
              <p className="font-medium text-gray-900">View Projects</p>
              <p className="text-sm text-gray-500">Browse all projects</p>
            </div>
          </Link>

          <Link
            to="/app/jobs"
            className="flex items-center space-x-3 p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-green-500 hover:bg-green-50 transition-colors"
          >
            <Cpu className="w-6 h-6 text-green-600" />
            <div>
              <p className="font-medium text-gray-900">Processing Jobs</p>
              <p className="text-sm text-gray-500">Monitor progress</p>
            </div>
          </Link>
        </div>
      </div>

      {/* Recent Projects */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">Recent Projects</h3>
            <Link to="/app/projects" className="text-sm text-blue-600 hover:text-blue-700">
              View all
            </Link>
          </div>
        </div>
        {recentProjects.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            <p>No projects yet. Start by uploading images!</p>
            <Link
              to="/app/upload"
              className="mt-4 inline-block px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Upload Images
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {recentProjects.map((project) => (
              <Link
                key={project.job_id}
                to={`/app/jobs/${project.job_id}`}
                className="p-6 hover:bg-gray-50 flex items-center justify-between"
              >
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                    <FolderOpen className="w-6 h-6 text-gray-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{project.name || 'Untitled Project'}</p>
                    <div className="flex items-center space-x-2 mt-1">
                      <Clock className="w-4 h-4 text-gray-400" />
                      <span className="text-sm text-gray-500">{formatDate(project.created_at)}</span>
                    </div>
                  </div>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                  project.status === 'completed'
                    ? 'bg-green-100 text-green-800'
                    : project.status === 'processing'
                    ? 'bg-blue-100 text-blue-800'
                    : project.status === 'failed'
                    ? 'bg-red-100 text-red-800'
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {project.status}
                </span>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard
