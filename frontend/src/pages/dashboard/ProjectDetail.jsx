import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Image, Cpu, Box, Download, Eye } from 'lucide-react'

function ProjectDetail() {
  const { id } = useParams()

  const project = {
    id,
    name: 'Office Scan',
    created: '2024-04-08',
    images: 45,
    status: 'completed',
    description: 'Complete 3D reconstruction of office space',
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
            <h2 className="text-2xl font-bold text-gray-900">{project.name}</h2>
            <p className="text-gray-600 mt-1">{project.description}</p>
          </div>
          <span className="px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
            {project.status}
          </span>
        </div>

        <div className="grid grid-cols-3 gap-4 mt-6">
          <div className="p-4 bg-gray-50 rounded-lg">
            <Image className="w-6 h-6 text-gray-600 mb-2" />
            <p className="text-sm text-gray-600">Images</p>
            <p className="text-2xl font-bold text-gray-900">{project.images}</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <Cpu className="w-6 h-6 text-gray-600 mb-2" />
            <p className="text-sm text-gray-600">Processing</p>
            <p className="text-2xl font-bold text-gray-900">Done</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <Box className="w-6 h-6 text-gray-600 mb-2" />
            <p className="text-sm text-gray-600">Models</p>
            <p className="text-2xl font-bold text-gray-900">3</p>
          </div>
        </div>

        <div className="mt-6 flex space-x-4">
          <Link
            to={`/app/viewer/${id}`}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Eye className="w-5 h-5" />
            <span>View 3D Model</span>
          </Link>
          <Link
            to="/app/exports"
            className="flex items-center space-x-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
          >
            <Download className="w-5 h-5" />
            <span>Export</span>
          </Link>
        </div>
      </div>
    </div>
  )
}

export default ProjectDetail
