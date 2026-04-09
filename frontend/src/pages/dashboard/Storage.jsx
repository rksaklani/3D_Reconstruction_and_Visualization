import { HardDrive, Image, Box, FileText } from 'lucide-react'

function Storage() {
  const usage = {
    total: 10,
    used: 2.4,
    images: 1.2,
    models: 0.8,
    exports: 0.4,
  }

  const percentage = (usage.used / usage.total) * 100

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Storage</h2>
        <p className="text-gray-600 mt-1">Manage your storage usage</p>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Storage Usage</h3>
          <span className="text-sm text-gray-600">{usage.used} GB / {usage.total} GB</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-4">
          <div
            className="bg-blue-600 h-4 rounded-full transition-all"
            style={{ width: `${percentage}%` }}
          ></div>
        </div>
        <p className="text-sm text-gray-600 mt-2">{percentage.toFixed(1)}% used</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <Image className="w-8 h-8 text-blue-600 mb-3" />
          <h3 className="font-semibold text-gray-900">Images</h3>
          <p className="text-2xl font-bold text-gray-900 mt-2">{usage.images} GB</p>
          <p className="text-sm text-gray-600 mt-1">Source images</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <Box className="w-8 h-8 text-purple-600 mb-3" />
          <h3 className="font-semibold text-gray-900">3D Models</h3>
          <p className="text-2xl font-bold text-gray-900 mt-2">{usage.models} GB</p>
          <p className="text-sm text-gray-600 mt-1">Generated models</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <FileText className="w-8 h-8 text-green-600 mb-3" />
          <h3 className="font-semibold text-gray-900">Exports</h3>
          <p className="text-2xl font-bold text-gray-900 mt-2">{usage.exports} GB</p>
          <p className="text-sm text-gray-600 mt-1">Exported files</p>
        </div>
      </div>
    </div>
  )
}

export default Storage
