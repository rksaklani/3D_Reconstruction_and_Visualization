import { Link } from 'react-router-dom'
import { Box, Eye, Download, Calendar } from 'lucide-react'

function Models() {
  const models = [
    { id: '1', name: 'Office Scan - Gaussian Splat', type: 'gaussian', size: '45 MB', created: '2024-04-08' },
    { id: '2', name: 'Product Demo - Mesh', type: 'mesh', size: '12 MB', created: '2024-04-07' },
    { id: '3', name: 'Room - Point Cloud', type: 'pointcloud', size: '89 MB', created: '2024-04-06' },
  ]

  const getTypeColor = (type) => {
    switch (type) {
      case 'gaussian': return 'bg-blue-100 text-blue-800'
      case 'mesh': return 'bg-purple-100 text-purple-800'
      case 'pointcloud': return 'bg-green-100 text-green-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">3D Models</h2>
        <p className="text-gray-600 mt-1">Browse and manage your 3D models</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {models.map((model) => (
          <div key={model.id} className="bg-white rounded-lg shadow">
            <div className="h-48 bg-gradient-to-br from-gray-700 to-gray-900 rounded-t-lg flex items-center justify-center">
              <Box className="w-16 h-16 text-white opacity-50" />
            </div>
            <div className="p-4">
              <h3 className="font-semibold text-gray-900">{model.name}</h3>
              <div className="mt-2 space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Size</span>
                  <span className="font-medium text-gray-900">{model.size}</span>
                </div>
                <div className="flex items-center text-sm text-gray-600">
                  <Calendar className="w-4 h-4 mr-2" />
                  <span>{model.created}</span>
                </div>
              </div>
              <div className="mt-3">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getTypeColor(model.type)}`}>
                  {model.type}
                </span>
              </div>
              <div className="mt-4 flex space-x-2">
                <Link
                  to={`/app/viewer/${model.id}`}
                  className="flex-1 flex items-center justify-center space-x-1 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
                >
                  <Eye className="w-4 h-4" />
                  <span>View</span>
                </Link>
                <button className="flex items-center justify-center px-3 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50">
                  <Download className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default Models
