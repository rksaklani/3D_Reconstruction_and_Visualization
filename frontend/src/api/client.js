import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

export const jobsApi = {
  getJobs: () => api.get('/jobs'),
  getJob: (jobId) => api.get(`/job/${jobId}`),
  getJobLog: (jobId, tail = 6000) => api.get(`/job/${jobId}/log?tail=${tail}`),
  stopJob: (jobId) => api.post(`/job/${jobId}/stop`),
  createJob: (formData) => api.post('/run', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  }),
}

export const browseApi = {
  browse: (params) => api.get('/browse', { params }),
  mkdir: (data) => api.post('/browse/mkdir', data, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  }),
}

export default api
