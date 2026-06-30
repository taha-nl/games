import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { api } from '@/api/client'
import { useWebSocket } from '@/hooks/useWebSocket'

interface DashboardData {
  team: { id: number; name: string; score: number; coins: number; is_frozen: boolean; frozen_until: string | null }
  rank: number
  challenges: Array<{ id: number; title: string; difficulty: string; points: number; planet_name: string }>
  approved_ids: number[]
  pending_count: number
  achievements: Array<{ badge_icon: string; badge_name: string; description: string }>
  team_cards: Array<{ id: number; quantity: number; card: { id: number; name: string; icon: string; card_type: string } }>
  active_event: { title: string; description: string; multiplier: number } | null
}

const difficultyEmoji: Record<string, string> = { easy: '🟢', medium: '🟡', hard: '🔴' }
const difficultyColor: Record<string, string> = {
  easy: 'bg-green-900/50 text-green-300',
  medium: 'bg-yellow-900/50 text-yellow-300',
  hard: 'bg-red-900/50 text-red-300',
}

export default function Dashboard() {
  const qc = useQueryClient()
  const { data, isLoading } = useQuery<DashboardData>({
    queryKey: ['dashboard'],
    queryFn: () => api.get('/dashboard'),
  })

  const useCard = useMutation({
    mutationFn: (teamCardId: number) => api.post(`/cards/use/${teamCardId}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['dashboard'] }); toast.success('Card used!') },
    onError: (e: Error) => toast.error(e.message),
  })

  useWebSocket(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws/leaderboard`, {
    score_update: (d) => {
      toast.success(d['message'] as string)
      qc.invalidateQueries({ queryKey: ['dashboard'] })
    },
    rejection: (d) => toast.error(d['message'] as string, { duration: 8000 }),
    hint: (d) => toast.info(d['message'] as string, { duration: 10000 }),
    freeze: (d) => { toast.warning(d['message'] as string); qc.invalidateQueries({ queryKey: ['dashboard'] }) },
    card_effect: (d) => toast.success(d['message'] as string),
    event: (d) => toast.info(`⚡ ${d['title']}: ${d['description']}`, { duration: 8000 }),
  })

  if (isLoading || !data) {
    return <div className="flex items-center justify-center min-h-[60vh]"><div className="text-neon-blue animate-pulse text-xl">🚀 Loading mission data...</div></div>
  }

  const { team, rank, challenges, approved_ids, pending_count, achievements, team_cards, active_event } = data

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">

      {active_event && (
        <div className="mb-6 bg-gradient-to-r from-yellow-900/60 to-orange-900/60 border border-yellow-500/40 rounded-2xl p-4 flex items-center gap-4">
          <span className="text-4xl">⚡</span>
          <div>
            <div className="font-bold text-yellow-300 text-lg">{active_event.title}</div>
            <div className="text-yellow-200/70 text-sm">{active_event.description}</div>
          </div>
          {active_event.multiplier > 1 && (
            <div className="ml-auto text-2xl font-black text-yellow-300">×{active_event.multiplier}</div>
          )}
        </div>
      )}

      {team.is_frozen && (
        <div className="mb-6 frozen-card bg-blue-900/40 border-2 border-blue-400 rounded-2xl p-4 flex items-center gap-4">
          <span className="text-4xl">🥶</span>
          <div>
            <div className="font-bold text-blue-300 text-lg">TEAM FROZEN!</div>
            <div className="text-blue-200/70 text-sm">
              Submissions blocked until {team.frozen_until ? new Date(team.frozen_until).toLocaleTimeString() : 'soon'}.
            </div>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-4xl font-black text-white">
            <span className="text-neon-green">{team.name}</span> Mission
          </h1>
          <p className="text-gray-400 mt-1">Your spaceship is ready. Conquer the planets!</p>
        </div>
        <div className="text-6xl rocket-float">🛸</div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="glass rounded-2xl p-5 border border-yellow-500/30">
          <div className="text-3xl mb-2">⚡</div>
          <div className="text-3xl font-black text-yellow-300">{team.score}</div>
          <div className="text-gray-400 text-sm font-semibold uppercase tracking-wide mt-1">Fuel Units</div>
          <div className="mt-3 h-1.5 bg-space-600 rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-yellow-500 to-orange-400 rounded-full progress-bar" style={{ width: `${Math.min(team.score / 10, 100)}%` }} />
          </div>
        </div>
        <div className="glass rounded-2xl p-5 border border-purple-500/30">
          <div className="text-3xl mb-2">🏆</div>
          <div className={`text-3xl font-black ${rank === 1 ? 'rank-1' : rank === 2 ? 'rank-2' : rank === 3 ? 'rank-3' : 'text-purple-300'}`}>#{rank}</div>
          <div className="text-gray-400 text-sm font-semibold uppercase tracking-wide mt-1">Mission Rank</div>
        </div>
        <div className="glass rounded-2xl p-5 border border-amber-500/30">
          <div className="text-3xl mb-2">🪙</div>
          <div className="text-3xl font-black text-amber-300">{team.coins}</div>
          <div className="text-gray-400 text-sm font-semibold uppercase tracking-wide mt-1">Space Coins</div>
        </div>
        <div className="glass rounded-2xl p-5 border border-green-500/30">
          <div className="text-3xl mb-2">🪐</div>
          <div className="text-3xl font-black text-green-300">{approved_ids.length}</div>
          <div className="text-gray-400 text-sm font-semibold uppercase tracking-wide mt-1">Planets Conquered</div>
          {pending_count > 0 && <div className="text-xs text-yellow-400 mt-1">{pending_count} pending review</div>}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Challenges */}
        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-white">🪐 Available Planets</h2>
            <Link to="/challenges" className="text-indigo-400 hover:text-indigo-300 text-sm transition">View all →</Link>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {challenges.slice(0, 4).map(c => {
              const solved = approved_ids.includes(c.id)
              return (
                <Link
                  key={c.id}
                  to={`/challenge/${c.id}`}
                  className={`planet-card glass rounded-xl p-4 border transition-all duration-200 block ${solved ? 'border-green-500/50 bg-green-900/20' : 'border-white/10 hover:border-indigo-400/50'}`}
                >
                  <div className="flex items-start justify-between">
                    <div className="text-3xl mb-2">{difficultyEmoji[c.difficulty] ?? '⚪'}</div>
                    {solved ? <span className="text-green-400 font-bold text-lg">✓</span> : <span className="text-yellow-300 font-bold text-sm">+{c.points}</span>}
                  </div>
                  <div className="font-bold text-white text-sm">{c.title}</div>
                  <div className="text-gray-400 text-xs mt-0.5">{c.planet_name}</div>
                  <div className="mt-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${difficultyColor[c.difficulty] ?? ''}`}>
                      {c.difficulty.toUpperCase()}
                    </span>
                  </div>
                </Link>
              )
            })}
          </div>
          {challenges.length > 4 && (
            <Link to="/challenges" className="mt-3 block text-center text-indigo-400 hover:text-indigo-300 text-sm py-2">
              + {challenges.length - 4} more planets →
            </Link>
          )}
        </div>

        {/* Right panel */}
        <div className="space-y-5">
          {/* Achievements */}
          <div className="glass rounded-2xl p-5 border border-white/10">
            <h3 className="font-bold text-white mb-3 flex items-center gap-2"><span>🏅</span> Achievements</h3>
            {achievements.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {achievements.map((a, i) => (
                  <div key={i} className="group relative">
                    <div className="w-10 h-10 rounded-full bg-space-600 border border-yellow-500/40 flex items-center justify-center text-xl cursor-help hover:border-yellow-400 transition">
                      {a.badge_icon}
                    </div>
                    <div className="absolute bottom-12 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-xs rounded-lg px-2 py-1 whitespace-nowrap opacity-0 group-hover:opacity-100 transition pointer-events-none z-10 border border-white/20">
                      {a.badge_name}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">No achievements yet. Keep solving! 💪</p>
            )}
          </div>

          {/* Power Cards */}
          <div className="glass rounded-2xl p-5 border border-white/10">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-bold text-white flex items-center gap-2"><span>🃏</span> Power Cards</h3>
              <Link to="/cards/shop" className="text-indigo-400 hover:text-indigo-300 text-xs transition">Shop →</Link>
            </div>
            {team_cards.length > 0 ? (
              <div className="space-y-2">
                {team_cards.map(tc => (
                  <div key={tc.id} className="flex items-center justify-between bg-space-600/50 rounded-lg px-3 py-2">
                    <div className="flex items-center gap-2">
                      <span>{tc.card.icon}</span>
                      <span className="text-sm font-semibold">{tc.card.name}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs bg-space-500 px-2 py-0.5 rounded-full text-gray-300">×{tc.quantity}</span>
                      <button
                        onClick={() => useCard.mutate(tc.id)}
                        disabled={useCard.isPending}
                        className="text-xs bg-indigo-600 hover:bg-indigo-500 px-2 py-0.5 rounded transition disabled:opacity-50"
                      >
                        USE
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">No cards. <Link to="/cards/shop" className="text-indigo-400">Visit the shop!</Link></p>
            )}
          </div>

          {/* Quick links */}
          <div className="glass rounded-2xl p-5 border border-white/10">
            <h3 className="font-bold text-white mb-3">🚀 Quick Actions</h3>
            <div className="space-y-2">
              <Link to="/leaderboard" className="flex items-center gap-2 text-sm text-gray-300 hover:text-white transition py-1">🏆 Live Leaderboard</Link>
              <Link to="/challenges" className="flex items-center gap-2 text-sm text-gray-300 hover:text-white transition py-1">🪐 All Challenges</Link>
              <Link to="/cards/shop" className="flex items-center gap-2 text-sm text-gray-300 hover:text-white transition py-1">🃏 Card Shop</Link>
              <Link to="/quiz" className="flex items-center gap-2 text-sm text-neon-purple/80 hover:text-neon-purple transition py-1 font-semibold">🧠 Algorithm Quiz</Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
