import { useState, useEffect } from 'react'
import { BarChart3, TrendingUp, Activity, Clock } from 'lucide-react'
import { jobsApi } from '../../api/client'

function Analytics() {
  const [analytics, setAnalytics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadAnalytics()
  }, [])

  const loadAnalytics = async () => {
    try {
      setLoading(true)
      const response = await jobsApi.getJobs({ limit: 100 })
      const jobs = response.data.jobs || []
      
      const totalProjects = jobs.length
      const completedJobs = jobs.filter(j => j.status === 'completed')
      const failedJobs = jobs.filter(j => j.status === 'failed')
      const processingJobs = jobs.filter(j => j.status === 'processing')
      
      let totalProcessingTime = 0
      completedJobs.forEach(job => {
        if (job.started_at && job.completed_at) {
          const start = new Date(job.started_at)
          const end = new Date(job.completed_at)
          totalProcessingTime += (end - start) / 1000 / 3600
        }
      })
      
      const successRate = totalProjects > 0 
        ? ((completedJobs.length / totalProjects) * 100).toFixed(1)
        : 0
      
      const last7Days = []
      const today = new Date()
      for (let i = 6; i >= 0; i--) {
        const date = new Date(today)
        date.setDate(date.getDate() - i)
        date.setHours(0, 0, 0, 0)
        
        const nextDate = new Date(date)
        nextDate.setDate(nextDate.getDate() + 1)
        
        const dayJobs = jobs.filter(job => {
          const jobDate = new Date(job.created_at)
          return jobDate >= date && jobDate < nextDate
        })
        
        last7Days.push({
          date: date,
          count: dayJobs.length,
          day: date.toLocaleDateString('en-US', { weekday: 'short' })
        })
      }
      
      const uniqueUsers = new Set(jobs.map(j => j.user_id).filter(Boolean)).size
      
      setAnalytics({
        totalProjects,
        processingTime: totalProcessingTime.toFixed(1),
        successRate,
        activeUsers: uniqueUsers || 1,
        completedJobs: completedJobs.length,
        failedJobs: failedJobs.length,
        processingJobs: processingJobs.length,
        last7Days
      })
      setError(null)
    } catch (err) {
      console.error('Failed to load analytics:', err)
      setError('Failed to load analytics')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <p className="text-red-800">{error}</p>
        <button
          onClick={loadAnalytics}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    )
  }

  const stats = [
    { name: 'Total Projects', value: analytics.totalProjects, change: `${analytics.completedJobs} completed`, icon: BarChart3 },
    { name: 'Processing Time', value: `${analytics.processingTime}h`, change: `${analytics.processingJobs} active`, icon: Clock },
    { name: 'Success Rate', value: `${analytics.successRate}%`, change: `${analytics.failedJobs} failed`, icon: TrendingUp },
    { name: 'Active Users', value: analytics.activeUsers, change: 'Total users', icon: Activity },
  ]

  const maxCount = Math.max(...analytics.last7Days.map(d => d.count), 1)

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
                <span className="text-sm text-gray-600 font-medium">{stat.change}</span>
              </div>
              <p className="text-sm text-gray-600">{stat.name}</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{stat.value}</p>
            </div>
          )
        })}
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Projects Created (Last 7 Days)</h3>
        <div className="h-64 flex items-end justify-between space-x-2">
          {analytics.last7Days.map((day, i) => {
            const height = maxCount > 0 ? (day.count / maxCount) * 100 : 0
            return (
              <div key={i} className="flex-1 flex flex-col items-center">
                <div className="w-full flex items-end justify-center" style={{ height: '200px' }}>
                  <div 
                    className="w-full bg-blue-600 rounded-t hover:bg-blue-700 transition-colors relative group"
                    style={{ height: `${height}%`, minHeight: day.count > 0 ? '8px' : '0' }}
                  >
                    <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                      {day.count} project{day.count !== 1 ? 's' : ''}
                    </div>
                  </div>
                </div>
                <span className="text-sm text-gray-600 mt-2">{day.day}</span>
              </div>
            )
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Completed</p>
              <p className="text-2xl font-bold text-green-600 mt-1">{analytics.completedJobs}</p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Processing</p>
              <p className="text-2xl font-bold text-blue-600 mt-1">{analytics.processingJobs}</p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <Activity className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Failed</p>
              <p className="text-2xl font-bold text-red-600 mt-1">{analytics.failedJobs}</p>
            </div>
            <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
              <BarChart3 className="w-6 h-6 text-red-600" />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Analytics
