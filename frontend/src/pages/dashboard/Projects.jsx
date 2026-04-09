import { Link } from 'react-router-dom'
import { FolderOpen, Plus, Calendar, Image } from 'lucide-react'

function Projects() {
  const projects = [
    { id: '1', name: 'Office Scan', images: 45, created: '2024-04-08', status: 'completed' },
    { id: '2', name: 'Product Demo', images: 32, created: '2024-04-07', status: 'processing' },
    { id: '3', name: 'Room Reconstruction', images: 67, created: '2024-04-06', status: 'completed' },
    { id: '4', name: 'Outdoor Scene', images: 89, created: '2024-04-05', status: 'completed' },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Projects</h2>
          <p className="text-gray-600 mt-1">Manage your 3D reconstruction projects</p>
        </div>
        <Link
          to="/app/upload"
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-5 h-5" />
          <span>New Project</span>
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {projects.map((project) => (
          <Link
            key={project.id}
            to={`/app/projects/${project.id}`}
            className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow"
          >
            <div className="h-48 bg-gradient-to-br from-blue-500 to-purple-600 rounded-t-lg flex items-center justify-center">
              <FolderOpen className="w-16 h-16 text-white opacity-50" />
            </div>
            <div className="p-4">
              <h3 className="font-semibold text-gray-900">{project.name}</h3>
              <div className="mt-2 space-y-1">
                <div className="flex items-center text-sm text-gray-600">
                  <Image className="w-4 h-4 mr-2" />
                  <span>{project.images} images</span>
                </div>
                <div className="flex items-center text-sm text-gray-600">
                  <Calendar className="w-4 h-4 mr-2" />
                  <span>{project.created}</span>
                </div>
              </div>
              <div className="mt-3">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  project.status === 'completed'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {project.status}
                </span>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}

export default Projects
