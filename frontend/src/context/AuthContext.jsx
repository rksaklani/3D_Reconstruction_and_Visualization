import { createContext, useState, useContext, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if user is logged in
    const isAuth = localStorage.getItem('isAuthenticated') === 'true'
    const userData = localStorage.getItem('user')
    
    if (isAuth && userData) {
      setUser(JSON.parse(userData))
    }
    
    setLoading(false)
  }, [])

  const login = async (email, password) => {
    // TODO: Implement actual API call
    const mockUser = {
      id: '1',
      email,
      name: email.split('@')[0],
      avatar: null
    }
    
    localStorage.setItem('isAuthenticated', 'true')
    localStorage.setItem('user', JSON.stringify(mockUser))
    setUser(mockUser)
    
    return mockUser
  }

  const signup = async (email, password, name) => {
    // TODO: Implement actual API call
    const mockUser = {
      id: '1',
      email,
      name,
      avatar: null
    }
    
    localStorage.setItem('isAuthenticated', 'true')
    localStorage.setItem('user', JSON.stringify(mockUser))
    setUser(mockUser)
    
    return mockUser
  }

  const logout = () => {
    localStorage.removeItem('isAuthenticated')
    localStorage.removeItem('user')
    setUser(null)
  }

  const value = {
    user,
    loading,
    login,
    signup,
    logout,
    isAuthenticated: !!user
  }

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export default AuthContext
