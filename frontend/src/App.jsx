import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'

// Layouts
import PublicLayout from './layouts/PublicLayout'
import DashboardLayout from './layouts/DashboardLayout'

// Public Pages
import Home from './pages/public/Home'
import Features from './pages/public/Features'
import Pricing from './pages/public/Pricing'
import About from './pages/public/About'
import Contact from './pages/public/Contact'
import Login from './pages/public/Login'
import Signup from './pages/public/Signup'

// Dashboard Pages
import Dashboard from './pages/dashboard/Dashboard'
import Projects from './pages/dashboard/Projects'
import ProjectDetail from './pages/dashboard/ProjectDetail'
import Upload from './pages/Upload'
import Jobs from './pages/dashboard/Jobs'
import JobDetail from './pages/JobDetail'
import AIAnalysis from './pages/dashboard/AIAnalysis'
import Models from './pages/dashboard/Models'
import Viewer from './pages/Viewer'
import ViewerDebug from './pages/ViewerDebug'
import ApiTest from './pages/ApiTest'
import Exports from './pages/dashboard/Exports'
import Storage from './pages/dashboard/Storage'
import Team from './pages/dashboard/Team'
import Analytics from './pages/dashboard/Analytics'
import Settings from './pages/dashboard/Settings'
import Help from './pages/dashboard/Help'

// Protected Route Component
function ProtectedRoute({ children }) {
  // TODO: Implement actual auth check
  const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true'
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  return children
}

function App() {
  return (
    <AuthProvider>
      <Routes>
          {/* Public Routes */}
          <Route element={<PublicLayout />}>
            <Route path="/" element={<Home />} />
            <Route path="/features" element={<Features />} />
            <Route path="/pricing" element={<Pricing />} />
            <Route path="/about" element={<About />} />
            <Route path="/contact" element={<Contact />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
          </Route>

          {/* Dashboard Routes (Protected) */}
          <Route path="/app" element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }>
            <Route index element={<Dashboard />} />
            <Route path="projects" element={<Projects />} />
            <Route path="projects/:id" element={<ProjectDetail />} />
            <Route path="upload" element={<Upload />} />
            <Route path="jobs" element={<Jobs />} />
            <Route path="jobs/:id" element={<JobDetail />} />
            <Route path="ai-analysis" element={<AIAnalysis />} />
            <Route path="models" element={<Models />} />
            <Route path="viewer/:id" element={<Viewer />} />
            <Route path="viewer/:id/debug" element={<ViewerDebug />} />
            <Route path="exports" element={<Exports />} />
            <Route path="storage" element={<Storage />} />
            <Route path="team" element={<Team />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="settings" element={<Settings />} />
            <Route path="help" element={<Help />} />
            <Route path="api-test" element={<ApiTest />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
    </AuthProvider>
  )
}

export default App
