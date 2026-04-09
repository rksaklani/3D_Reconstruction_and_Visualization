import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import JobDetail from './pages/JobDetail'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/job/:jobId" element={<JobDetail />} />
    </Routes>
  )
}

export default App
