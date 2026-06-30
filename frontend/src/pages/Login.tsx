import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { authApi } from '@/api/auth'
import { useAuth } from '@/context/AuthContext'
import { ApiError } from '@/api/client'

export default function Login() {
  const [teamName, setTeamName] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const { refetch } = useAuth()
  const navigate = useNavigate()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      await authApi.login(teamName, password)
      await refetch()
      navigate('/dashboard')
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-[calc(100vh-64px)] flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="text-7xl mb-4 rocket-float inline-block">🚀</div>
          <h1 className="text-4xl font-black text-white">SPACE MISSION</h1>
          <p className="text-neon-blue mt-2 tracking-widest uppercase text-sm">Coding Competition</p>
        </div>

        <div className="glass rounded-2xl p-8 border border-white/10">
          <h2 className="text-xl font-bold text-white mb-6 text-center">Team Login</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Team Name</label>
              <input
                type="text"
                value={teamName}
                onChange={e => setTeamName(e.target.value)}
                required
                placeholder="Enter your team name"
                className="w-full bg-space-700 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-neon-blue/50 transition"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                placeholder="••••••••"
                className="w-full bg-space-700 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-neon-blue/50 transition"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold py-3 rounded-xl transition disabled:opacity-50"
            >
              {loading ? '🚀 Launching...' : '🚀 Launch Mission'}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-white/10 text-center">
            <a href="/tutor/login" className="text-gray-500 hover:text-gray-300 text-sm transition">
              Tutor / Admin login →
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}
