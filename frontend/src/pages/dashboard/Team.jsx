import { Users, Mail, Shield, Plus } from 'lucide-react'

function Team() {
  const members = [
    { id: '1', name: 'John Doe', email: 'john@example.com', role: 'Owner', avatar: 'JD' },
    { id: '2', name: 'Jane Smith', email: 'jane@example.com', role: 'Admin', avatar: 'JS' },
    { id: '3', name: 'Bob Johnson', email: 'bob@example.com', role: 'Member', avatar: 'BJ' },
  ]

  const getRoleColor = (role) => {
    switch (role) {
      case 'Owner': return 'bg-purple-100 text-purple-800'
      case 'Admin': return 'bg-blue-100 text-blue-800'
      case 'Member': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Team</h2>
          <p className="text-gray-600 mt-1">Manage team members and permissions</p>
        </div>
        <button className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          <Plus className="w-5 h-5" />
          <span>Invite Member</span>
        </button>
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Team Members</h3>
        </div>
        <div className="divide-y divide-gray-200">
          {members.map((member) => (
            <div key={member.id} className="p-6 flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-semibold">
                  {member.avatar}
                </div>
                <div>
                  <h4 className="font-medium text-gray-900">{member.name}</h4>
                  <div className="flex items-center text-sm text-gray-600 mt-1">
                    <Mail className="w-4 h-4 mr-1" />
                    {member.email}
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${getRoleColor(member.role)}`}>
                  {member.role}
                </span>
                <button className="p-2 text-gray-400 hover:text-gray-600">
                  <Shield className="w-5 h-5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default Team
