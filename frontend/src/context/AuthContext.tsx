import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { authApi, type TeamInfo, type TutorInfo } from '@/api/auth'

interface AuthState {
  team: TeamInfo | null
  tutor: TutorInfo | null
  loading: boolean
  refetch: () => Promise<void>
}

const AuthContext = createContext<AuthState>({
  team: null, tutor: null, loading: true, refetch: async () => {},
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const [team, setTeam] = useState<TeamInfo | null>(null)
  const [tutor, setTutor] = useState<TutorInfo | null>(null)
  const [loading, setLoading] = useState(true)

  const refetch = async () => {
    try {
      const data = await authApi.me()
      setTeam(data.team ?? null)
      setTutor(data.tutor ?? null)
    } catch {
      setTeam(null)
      setTutor(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { refetch() }, [])

  return (
    <AuthContext.Provider value={{ team, tutor, loading, refetch }}>
      {children}
    </AuthContext.Provider>
  )
}

// oxlint-disable-next-line react/only-export-components -- hook lives here intentionally
export const useAuth = () => useContext(AuthContext)
