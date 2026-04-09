import { Link } from 'react-router-dom'
import { Target, Users, Zap } from 'lucide-react'

function About() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero */}
      <div className="bg-gradient-to-br from-blue-600 to-purple-700 text-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-5xl font-bold mb-6">About Us</h1>
          <p className="text-xl text-blue-100 max-w-3xl mx-auto">
            Making 3D reconstruction accessible to everyone
          </p>
        </div>
      </div>

      {/* Mission */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="max-w-3xl mx-auto text-center mb-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-6">Our Mission</h2>
          <p className="text-xl text-gray-600 leading-relaxed">
            We believe that creating stunning 3D reconstructions should be simple and accessible. 
            Our platform combines cutting-edge AI and computer vision technology to transform 
            ordinary images into extraordinary 3D experiences.
          </p>
        </div>

        {/* Values */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
          <div className="text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Target className="w-8 h-8 text-blue-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">Innovation</h3>
            <p className="text-gray-600">
              Pushing the boundaries of 3D reconstruction with the latest AI and computer vision research
            </p>
          </div>

          <div className="text-center">
            <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Users className="w-8 h-8 text-purple-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">Community</h3>
            <p className="text-gray-600">
              Building a community of creators, developers, and enthusiasts passionate about 3D
            </p>
          </div>

          <div className="text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Zap className="w-8 h-8 text-green-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">Performance</h3>
            <p className="text-gray-600">
              Delivering fast, reliable, and high-quality results for every reconstruction
            </p>
          </div>
        </div>

        {/* Story */}
        <div className="bg-white rounded-lg shadow-lg p-12 max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-gray-900 mb-6">Our Story</h2>
          <div className="space-y-4 text-gray-600 leading-relaxed">
            <p>
              Founded in 2024, our platform was born from a simple observation: creating 3D 
              reconstructions was too complex and required expensive software and expertise.
            </p>
            <p>
              We set out to change that by building a platform that combines the power of 
              COLMAP, Gaussian Splatting, and AI into a simple, intuitive interface that 
              anyone can use.
            </p>
            <p>
              Today, we're proud to serve thousands of users worldwide, from hobbyists and 
              students to professionals and enterprises, all creating amazing 3D content.
            </p>
          </div>
        </div>
      </div>

      {/* CTA */}
      <div className="bg-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">Join us on this journey</h2>
          <p className="text-xl text-gray-600 mb-8">Start creating amazing 3D reconstructions today</p>
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

export default About
