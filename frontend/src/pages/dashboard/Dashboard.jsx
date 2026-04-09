import { Link } from 'react-router-dom'
import { FolderOpen, Upload, Cpu, Box, TrendingUp, Clock } from 'lucide-react'

function Dashboard() {
  const stats = [
    { name: 'Total Projects', value: '12', icon: FolderOpen, color: 'blue' },
    { name: 'Active Jobs', value: '3', icon: Cpu, color: 'purple' },
    { name: '3D Models', value: '24', icon: Box, color: 'green' },
    { name: 'Storage Used', value: '2.4 GB', icon: TrendingUp, color: 'orange' },
  ]

  const recentProjects = [
    { id: '1', name: 'Office Scan', status: 'completed', date: '2 hours ago' },
    { id: '2', name: 'Product Demo', status: 'processing', date: '5 hours ago' },
    { id: '3', name: 'Room Reconstruction', status: 'completed', date: '1 day ago' },
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
        {stats.map((stat) => {
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
        <div className="divide-y divide-gray-200">
          {recentProjects.map((project) => (
            <Link
              key={project.id}
              to={`/app/projects/${project.id}`}
              className="p-6 hover:bg-gray-50 flex items-center justify-between"
            >
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                  <FolderOpen className="w-6 h-6 text-gray-600" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">{project.name}</p>
                  <div className="flex items-center space-x-2 mt-1">
                    <Clock className="w-4 h-4 text-gray-400" />
                    <span className="text-sm text-gray-500">{project.date}</span>
                  </div>
                </div>
              </div>
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                project.status === 'completed'
                  ? 'bg-green-100 text-green-800'
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                {project.status}
              </span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}

export default Dashboard
