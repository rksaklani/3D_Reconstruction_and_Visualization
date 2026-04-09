import { Download, FileText, Package } from 'lucide-react'

function Exports() {
  const exports = [
    { id: '1', name: 'Office Scan - GLB', format: 'glb', size: '45 MB', date: '2024-04-08' },
    { id: '2', name: 'Product Demo - OBJ', format: 'obj', size: '12 MB', date: '2024-04-07' },
    { id: '3', name: 'Room - PLY', format: 'ply', size: '89 MB', date: '2024-04-06' },
  ]

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
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <FileText className="w-8 h-8 text-purple-600 mb-3" />
          <h3 className="font-semibold text-gray-900">OBJ</h3>
          <p className="text-sm text-gray-600 mt-1">Universal 3D format</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <Package className="w-8 h-8 text-green-600 mb-3" />
          <h3 className="font-semibold text-gray-900">PLY</h3>
          <p className="text-sm text-gray-600 mt-1">Point cloud format</p>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Recent Exports</h3>
        </div>
        <div className="divide-y divide-gray-200">
          {exports.map((exp) => (
            <div key={exp.id} className="p-6 hover:bg-gray-50 flex items-center justify-between">
              <div>
                <h4 className="font-medium text-gray-900">{exp.name}</h4>
                <p className="text-sm text-gray-600 mt-1">{exp.size} • {exp.date}</p>
              </div>
              <button className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                <Download className="w-4 h-4" />
                <span>Download</span>
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default Exports
