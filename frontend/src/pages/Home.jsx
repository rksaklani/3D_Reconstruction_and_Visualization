import JobForm from '../components/JobForm'
import JobList from '../components/JobList'

function Home() {
  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">GS Local Platform</h1>
        
        <div className="grid lg:grid-cols-[520px_1fr] gap-6 items-start">
          {/* Job Form */}
          <div className="bg-white border border-gray-200 rounded-xl p-6">
            <h2 className="text-xl font-bold mb-6">New job</h2>
            <JobForm />
          </div>

          {/* Job List */}
          <div className="bg-white border border-gray-200 rounded-xl p-6">
            <h2 className="text-xl font-bold mb-6">Jobs</h2>
            <JobList />
          </div>
        </div>
      </div>
    </div>
  )
}

export default Home
