import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, CheckCircle, XCircle, AlertCircle } from 'lucide-react'

function ApiTest() {
  const [results, setResults] = useState({})
  const [testing, setTesting] = useState(false)

  const testEndpoint = async (name, url, method = 'GET') => {
    try {
      const startTime = performance.now()
      const response = await fetch(url, { method })
      const endTime = performance.now()
      const time = Math.round(endTime - startTime)
      
      let data = null
      const contentType = response.headers.get('content-type')
      if (contentType && contentType.includes('application/json')) {
        data = await response.json()
      } else {
        data = await response.text()
      }

      return {
        name,
        url,
        status: response.ok ? 'success' : 'error',
        statusCode: response.status,
        statusText: response.statusText,
        time,
        data: typeof data === 'string' ? data.substring(0, 200) : data
      }
    } catch (err) {
      return {
        name,
        url,
        status: 'error',
        error: err.message
      }
    }
  }

  const runTests = async () => {
    setTesting(true)
    setResults({})

    const tests = [
      { name: 'Backend Health', url: '/api/health' },
      { name: 'Backend Root', url: '/api/' },
      { name: 'Jobs List', url: '/api/jobs?limit=1' },
      { name: 'Direct Backend (8000)', url: 'http://localhost:8000/api/health' },
      { name: 'Direct Backend Root', url: 'http://localhost:8000/health' },
    ]

    const newResults = {}
    for (const test of tests) {
      const result = await testEndpoint(test.name, test.url)
      newResults[test.name] = result
      setResults({ ...newResults })
    }

    setTesting(false)
  }

  const getStatusIcon = (status) => {
    if (status === 'success') return <CheckCircle className="w-5 h-5 text-green-600" />
    if (status === 'error') return <XCircle className="w-5 h-5 text-red-600" />
    return <AlertCircle className="w-5 h-5 text-yellow-600" />
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <Link to="/app/jobs" className="flex items-center text-blue-600 hover:text-blue-700">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Jobs
        </Link>

        <div className="bg-white rounded-lg shadow p-6">
          <h1 className="text-3xl font-bold mb-4">API Connectivity Test</h1>
          <p className="text-gray-600 mb-6">
            This page tests if the frontend can connect to the backend API.
          </p>

          <button
            onClick={runTests}
            disabled={testing}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {testing ? 'Testing...' : 'Run API Tests'}
          </button>
        </div>

        {Object.keys(results).length > 0 && (
          <div className="space-y-4">
            {Object.entries(results).map(([name, result]) => (
              <div key={name} className="bg-white rounded-lg shadow p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(result.status)}
                    <div>
                      <h3 className="font-semibold text-lg">{result.name}</h3>
                      <p className="text-sm text-gray-600">{result.url}</p>
                    </div>
                  </div>
                  {result.time && (
                    <span className="text-sm text-gray-500">{result.time}ms</span>
                  )}
                </div>

                {result.statusCode && (
                  <div className="mb-2">
                    <span className={`px-2 py-1 rounded text-sm font-medium ${
                      result.status === 'success' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {result.statusCode} {result.statusText}
                    </span>
                  </div>
                )}

                {result.error && (
                  <div className="bg-red-50 border border-red-200 rounded p-3 mb-2">
                    <p className="text-red-800 text-sm font-medium">Error:</p>
                    <p className="text-red-600 text-sm">{result.error}</p>
                  </div>
                )}

                {result.data && (
                  <div className="mt-3">
                    <p className="text-sm font-medium text-gray-700 mb-2">Response:</p>
                    <pre className="bg-gray-50 p-3 rounded text-xs overflow-auto max-h-40">
                      {typeof result.data === 'object' 
                        ? JSON.stringify(result.data, null, 2)
                        : result.data
                      }
                    </pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Diagnostic Info */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4 text-blue-900">Diagnostic Information</h2>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between py-2 border-b border-blue-200">
              <span className="font-medium text-blue-800">Current URL:</span>
              <span className="text-blue-700">{window.location.href}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-blue-200">
              <span className="font-medium text-blue-800">Origin:</span>
              <span className="text-blue-700">{window.location.origin}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-blue-200">
              <span className="font-medium text-blue-800">Expected Backend:</span>
              <span className="text-blue-700">http://localhost:8000</span>
            </div>
            <div className="flex justify-between py-2 border-b border-blue-200">
              <span className="font-medium text-blue-800">Vite Proxy:</span>
              <span className="text-blue-700">/api → http://localhost:8000</span>
            </div>
          </div>

          <div className="mt-4 space-y-2 text-sm text-blue-800">
            <p className="font-medium">Common Issues:</p>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li>Backend server not running on port 8000</li>
              <li>CORS issues (check backend CORS settings)</li>
              <li>Firewall blocking connections</li>
              <li>Wrong API URL configuration</li>
            </ul>
          </div>

          <div className="mt-4 space-y-2 text-sm text-blue-800">
            <p className="font-medium">How to Fix:</p>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li>Start backend: <code className="bg-blue-100 px-2 py-1 rounded">cd backend && python -m uvicorn api.main:app --reload --port 8000</code></li>
              <li>Check backend is running: <code className="bg-blue-100 px-2 py-1 rounded">curl http://localhost:8000/health</code></li>
              <li>Restart frontend dev server if proxy not working</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ApiTest
