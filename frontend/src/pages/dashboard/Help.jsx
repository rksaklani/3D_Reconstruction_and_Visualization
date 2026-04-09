import { HelpCircle, Book, MessageCircle, FileText } from 'lucide-react'

function Help() {
  const resources = [
    { icon: Book, title: 'Documentation', description: 'Complete guides and API reference', link: '#' },
    { icon: MessageCircle, title: 'Community', description: 'Join our Discord community', link: '#' },
    { icon: FileText, title: 'Tutorials', description: 'Step-by-step video tutorials', link: '#' },
    { icon: HelpCircle, title: 'FAQ', description: 'Frequently asked questions', link: '#' },
  ]

  const faqs = [
    { q: 'How do I upload images?', a: 'Go to Upload page and drag & drop your images or click to browse.' },
    { q: 'What formats are supported?', a: 'We support JPG, PNG for images and MP4 for videos.' },
    { q: 'How long does processing take?', a: 'Processing time depends on the number of images, typically 5-30 minutes.' },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Help & Support</h2>
        <p className="text-gray-600 mt-1">Get help and learn how to use the platform</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {resources.map((resource) => {
          const Icon = resource.icon
          return (
            <a
              key={resource.title}
              href={resource.link}
              className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow"
            >
              <Icon className="w-8 h-8 text-blue-600 mb-3" />
              <h3 className="font-semibold text-gray-900">{resource.title}</h3>
              <p className="text-sm text-gray-600 mt-1">{resource.description}</p>
            </a>
          )
        })}
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Frequently Asked Questions</h3>
        </div>
        <div className="divide-y divide-gray-200">
          {faqs.map((faq, i) => (
            <div key={i} className="p-6">
              <h4 className="font-medium text-gray-900">{faq.q}</h4>
              <p className="text-sm text-gray-600 mt-2">{faq.a}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default Help
