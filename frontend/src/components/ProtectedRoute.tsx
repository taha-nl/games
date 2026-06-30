import { Navigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'

interface Props {
  children: React.ReactNode
  require: 'team' | 'tutor' | 'admin'
}

export function ProtectedRoute({ children, require: role }: Props) {
  const { team, tutor, loading } = useAuth()

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-neon-blue text-xl animate-pulse">🚀 Loading...</div>
      </div>
    )
  }

  if (role === 'team' && !team) return <Navigate to="/login" replace />
  if (role === 'tutor' && !tutor) return <Navigate to="/tutor/login" replace />
  if (role === 'admin' && tutor?.role !== 'admin') return <Navigate to="/tutor/submissions" replace />

  return <>{children}</>
}
