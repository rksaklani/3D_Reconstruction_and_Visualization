import { Link } from 'react-router-dom'
import { Zap, Eye, Cpu, Box, Target, Activity } from 'lucide-react'

function Features() {
  const features = [
    {
      icon: Cpu,
      title: 'COLMAP Integration',
      description: 'Industry-standard Structure from Motion for accurate camera pose estimation and sparse reconstruction.',
    },
    {
      icon: Zap,
      title: 'Gaussian Splatting',
      description: 'State-of-the-art 3D Gaussian Splatting for photorealistic real-time rendering.',
    },
    {
      icon: Target,
      title: 'AI Object Detection',
      description: 'YOLO-powered object detection to identify and track objects in your scenes.',
    },
    {
      icon: Activity,
      title: 'Segmentation',
      description: 'SAM-based segmentation for precise object boundaries and masks.',
    },
    {
      icon: Box,
      title: 'Multiple Export Formats',
      description: 'Export to GLB, OBJ, PLY, and more for use in any 3D application.',
    },
    {
      icon: Eye,
      title: 'Real-time Viewer',
      description: 'Interactive 3D viewer powered by Babylon.js for instant visualization.',
    },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero */}
      <div className="bg-gradient-to-br from-blue-600 to-purple-700 text-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-5xl font-bold mb-6">Powerful Features</h1>
          <p className="text-xl text-blue-100 max-w-3xl mx-auto">
            Everything you need to create stunning 3D reconstructions from images
          </p>
        </div>
      </div>

      {/* Features Grid */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature) => {
            const Icon = feature.icon
            return (
              <div key={feature.title} className="bg-white rounded-lg shadow-lg p-8 hover:shadow-xl transition-shadow">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                  <Icon className="w-6 h-6 text-blue-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">{feature.title}</h3>
                <p className="text-gray-600">{feature.description}</p>
              </div>
            )
          })}
        </div>
      </div>

      {/* CTA */}
      <div className="bg-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">Ready to get started?</h2>
          <p className="text-xl text-gray-600 mb-8">Create your first 3D reconstruction today</p>
          <Link
            to="/signup"
            className="inline-block px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-lg font-medium"
          >
            Get Started Free
          </Link>
        </div>
      </div>
    </div>
  )
}

export default Features
