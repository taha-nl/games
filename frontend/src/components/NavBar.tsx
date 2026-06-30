import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { authApi } from '@/api/auth'

export function NavBar() {
  const { team, tutor, refetch } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const path = location.pathname

  const navLink = (href: string, label: string) => (
    <Link
      to={href}
      className={`px-3 py-1.5 rounded-lg hover:bg-white/10 transition text-sm ${path === href || path.startsWith(href + '/') ? 'bg-white/10' : ''}`}
    >
      {label}
    </Link>
  )

  async function handleLogout() {
    if (tutor) await authApi.tutorLogout()
    else await authApi.logout()
    await refetch()
    navigate('/login')
  }

  return (
    <nav className="relative z-10 glass border-b border-white/10 px-6 py-3">
      <div className="max-w-7xl mx-auto flex items-center justify-between">

        {/* Logo */}
        {team ? (
          <Link to="/dashboard" className="flex items-center gap-3">
            <span className="text-3xl rocket-float">🚀</span>
            <div>
              <div className="text-lg font-black text-white tracking-wide">SPACE MISSION</div>
              <div className="text-xs text-neon-blue/80 tracking-widest uppercase">Coding Competition</div>
            </div>
          </Link>
        ) : tutor ? (
          <Link to="/tutor/submissions" className="flex items-center gap-3">
            <span className="text-3xl">🛸</span>
            <div>
              <div className="text-lg font-black text-white tracking-wide">MISSION CONTROL</div>
              <div className="text-xs text-neon-purple/80 tracking-widest uppercase">
                {tutor.role === 'admin' ? 'Admin' : 'Tutor'} Panel
              </div>
            </div>
          </Link>
        ) : (
          <div className="flex items-center gap-3">
            <span className="text-3xl rocket-float">🚀</span>
            <div>
              <div className="text-lg font-black text-white tracking-wide">SPACE MISSION</div>
              <div className="text-xs text-neon-blue/80 tracking-widest uppercase">Coding Competition</div>
            </div>
          </div>
        )}

        {/* Nav links */}
        {team && (
          <div className="flex items-center gap-4">
            <div className="glass rounded-full px-4 py-1.5 flex items-center gap-2">
              <span className="text-yellow-400">⚡</span>
              <span className="font-bold text-yellow-300">{team.score}</span>
              <span className="text-gray-400 text-xs">fuel</span>
            </div>
            <div className="glass rounded-full px-4 py-1.5 flex items-center gap-2">
              <span>🪙</span>
              <span className="font-bold text-amber-300">{team.coins}</span>
            </div>
            <div className="flex items-center gap-1 text-sm">
              {navLink('/dashboard', 'Dashboard')}
              {navLink('/challenges', '🪐 Planets')}
              {navLink('/leaderboard', '🏆 Ranks')}
              {navLink('/cards/shop', '🃏 Cards')}
              <Link
                to="/quiz"
                className={`px-3 py-1.5 rounded-lg hover:bg-white/10 transition text-sm font-semibold ${path.startsWith('/quiz') ? 'bg-neon-purple/20 text-neon-purple' : 'text-neon-purple/80'}`}
              >
                🧠 Quiz
              </Link>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center font-bold text-sm">
                {team.name[0].toUpperCase()}
              </div>
              <span className="text-sm font-semibold">{team.name}</span>
              <button onClick={handleLogout} className="text-gray-400 hover:text-red-400 transition text-xs ml-2">
                Exit
              </button>
            </div>
          </div>
        )}

        {tutor && (
          <div className="flex items-center gap-2 text-sm">
            {navLink('/tutor/submissions', '📋 Submissions')}
            {tutor.role === 'admin' && (
              <>
                {navLink('/admin', '⚙️ Admin')}
                {navLink('/admin/teams', '👥 Teams')}
                {navLink('/admin/challenges', '🪐 Challenges')}
                {navLink('/admin/events', '⚡ Events')}
                {navLink('/admin/quiz', '🧠 Quiz')}
              </>
            )}
            {navLink('/leaderboard', '🏆 Leaderboard')}
            <button onClick={handleLogout} className="text-red-400 hover:text-red-300 transition px-3 py-1.5 text-sm">
              Exit
            </button>
          </div>
        )}
      </div>
    </nav>
  )
}
