import { Zap, Target, Layers, Activity } from 'lucide-react'

function AIAnalysis() {
  const analyses = [
    { id: '1', type: 'Object Detection', count: 24, confidence: 0.92, project: 'Office Scan' },
    { id: '2', type: 'Segmentation', count: 156, confidence: 0.88, project: 'Product Demo' },
    { id: '3', type: 'Tracking', count: 12, confidence: 0.95, project: 'Room Reconstruction' },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">AI Analysis</h2>
        <p className="text-gray-600 mt-1">View AI-powered insights from your reconstructions</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <Target className="w-8 h-8 text-blue-600 mb-3" />
          <h3 className="font-semibold text-gray-900">Object Detection</h3>
          <p className="text-sm text-gray-600 mt-1">YOLO-based detection</p>
          <p className="text-2xl font-bold text-gray-900 mt-3">24 objects</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <Layers className="w-8 h-8 text-purple-600 mb-3" />
          <h3 className="font-semibold text-gray-900">Segmentation</h3>
          <p className="text-sm text-gray-600 mt-1">SAM segmentation</p>
          <p className="text-2xl font-bold text-gray-900 mt-3">156 segments</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <Activity className="w-8 h-8 text-green-600 mb-3" />
          <h3 className="font-semibold text-gray-900">Tracking</h3>
          <p className="text-sm text-gray-600 mt-1">Object tracking</p>
          <p className="text-2xl font-bold text-gray-900 mt-3">12 tracks</p>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Recent Analyses</h3>
        </div>
        <div className="divide-y divide-gray-200">
          {analyses.map((analysis) => (
            <div key={analysis.id} className="p-6 hover:bg-gray-50">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-gray-900">{analysis.type}</h4>
                  <p className="text-sm text-gray-600 mt-1">{analysis.project}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-600">Confidence</p>
                  <p className="text-lg font-semibold text-gray-900">{(analysis.confidence * 100).toFixed(0)}%</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default AIAnalysis
