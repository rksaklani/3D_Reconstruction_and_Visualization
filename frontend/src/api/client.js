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
  getJobs: () => api.get('/jobs'),
  getJob: (jobId) => api.get(`/jobs/${jobId}`),
  getJobLog: (jobId, tail = 6000) => api.get(`/logs/${jobId}?tail=${tail}`, {
    headers: { 'Accept': 'text/plain' }
  }),
  stopJob: (jobId) => api.post(`/process/${jobId}/stop`),
  startProcessing: (jobId) => api.post(`/process/${jobId}/start`),
  createJob: (formData) => api.post('/jobs', formData, {
    headers: { 'Content-Type': 'application/json' }
  }),
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
