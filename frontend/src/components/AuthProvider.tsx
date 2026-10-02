import { useEffect, useState, type ReactNode } from 'react'
import * as api from '../api'
import { AuthContext } from '../auth'

// Keeps track of who is logged in. The session itself lives in an HttpOnly cookie set by the backend.
export default function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<api.User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .fetchMe()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  const login = async (email: string, password: string) => {
    const u = await api.login(email, password)
    setUser(u)
    return u
  }

  const register = async (input: api.RegisterInput) => {
    const u = await api.register(input)
    setUser(u)
    return u
  }

  const logout = async () => {
    await api.logout()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}
