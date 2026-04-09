import { BarChart3, TrendingUp, Activity, Clock } from 'lucide-react'

function Analytics() {
  const stats = [
    { name: 'Total Projects', value: '24', change: '+12%', icon: BarChart3 },
    { name: 'Processing Time', value: '45h', change: '-8%', icon: Clock },
    { name: 'Success Rate', value: '94%', change: '+3%', icon: TrendingUp },
    { name: 'Active Users', value: '8', change: '+2', icon: Activity },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Analytics</h2>
        <p className="text-gray-600 mt-1">Track your usage and performance</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => {
          const Icon = stat.icon
          return (
            <div key={stat.name} className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <Icon className="w-8 h-8 text-blue-600" />
                <span className="text-sm text-green-600 font-medium">{stat.change}</span>
              </div>
              <p className="text-sm text-gray-600">{stat.name}</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{stat.value}</p>
            </div>
          )
        })}
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Usage Over Time</h3>
        <div className="h-64 flex items-end justify-between space-x-2">
          {[40, 65, 45, 80, 55, 90, 70].map((height, i) => (
            <div key={i} className="flex-1 bg-blue-600 rounded-t" style={{ height: `${height}%` }}></div>
          ))}
        </div>
        <div className="flex justify-between mt-2 text-sm text-gray-600">
          <span>Mon</span>
          <span>Tue</span>
          <span>Wed</span>
          <span>Thu</span>
          <span>Fri</span>
          <span>Sat</span>
          <span>Sun</span>
        </div>
      </div>
    </div>
  )
}

export default Analytics
