import axios from 'axios'

// Use environment variable for API URL, fallback to relative path for proxy
const baseURL = import.meta.env.VITE_API_URL 
  ? `${import.meta.env.VITE_API_URL}/api`
  : '/api'

const api = axios.create({
  baseURL: baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Log the API URL for debugging
console.log('API Base URL:', baseURL)

export const jobsApi = {
  getJobs: (params = {}) => api.get('/jobs', { params }),
  getJob: (jobId) => api.get(`/jobs/${jobId}`),
  getJobStats: (jobId) => api.get(`/jobs/${jobId}/stats`),
  getJobLog: (jobId, tail = 6000) => api.get(`/logs/${jobId}?tail=${tail}`, {
    headers: { 'Accept': 'text/plain' }
  }),
  stopJob: (jobId) => api.post(`/process/${jobId}/stop`),
  startProcessing: (jobId) => api.post(`/process/${jobId}/start`),
  createJob: (formData) => api.post('/jobs', formData, {
    headers: { 'Content-Type': 'application/json' }
  }),
  updateJob: (jobId, data) => api.patch(`/jobs/${jobId}`, data),
  deleteJob: (jobId) => api.delete(`/jobs/${jobId}`),
}

export const statsApi = {
  getDashboardStats: async () => {
    // Fetch all jobs to calculate stats
    const response = await api.get('/jobs', { params: { limit: 100 } })
    const jobs = response.data.jobs || []
    
    // Calculate stats
    const totalProjects = jobs.length
    const activeJobs = jobs.filter(j => j.status === 'processing' || j.status === 'queued').length
    const completedJobs = jobs.filter(j => j.status === 'completed').length
    
    // Calculate storage (sum of all job files)
    let totalStorage = 0
    jobs.forEach(job => {
      if (job.stats && job.stats.total_size) {
        totalStorage += job.stats.total_size
      }
    })
    
    return {
      totalProjects,
      activeJobs,
      completedJobs,
      totalModels: completedJobs,
      storageUsed: totalStorage,
      jobs
    }
  },
  
  getRecentProjects: async (limit = 5) => {
    const response = await api.get('/jobs', { params: { limit } })
    return response.data.jobs || []
  }
}

export const reconstructionApi = {
  getSceneData: (jobId) => api.get(`/reconstruction/${jobId}/scene`),
  getPointCloud: (jobId, limit = 50000) => api.get(`/reconstruction/${jobId}/points`, {
    params: { limit }
  }),
  getCameras: (jobId) => api.get(`/reconstruction/${jobId}/cameras`),
  downloadPly: (jobId) => api.get(`/reconstruction/${jobId}/download/ply`, {
    responseType: 'blob'
  }),
}

export const browseApi = {
  browse: (params) => api.get('/browse', { params }),
  mkdir: (data) => api.post('/browse/mkdir', data, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  }),
}

export default api
