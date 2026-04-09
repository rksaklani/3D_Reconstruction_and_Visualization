import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

export const jobsApi = {
  getJobs: () => api.get('/jobs'),
  getJob: (jobId) => api.get(`/jobs/${jobId}`),
  getJobLog: (jobId, tail = 6000) => api.get(`/jobs/${jobId}/log?tail=${tail}`),
  stopJob: (jobId) => api.post(`/process/${jobId}/stop`),
  startProcessing: (jobId) => api.post(`/process/${jobId}/start`),
  createJob: (formData) => api.post('/jobs', formData, {
    headers: { 'Content-Type': 'application/json' }
  }),
}

export const browseApi = {
  browse: (params) => api.get('/browse', { params }),
  mkdir: (data) => api.post('/browse/mkdir', data, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  }),
}

export default api
