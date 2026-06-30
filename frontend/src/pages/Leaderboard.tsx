import { useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { api } from '@/api/client'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useAuth } from '@/context/AuthContext'

interface LeaderboardEntry {
  rank: number; id: number; name: string; score: number; coins: number
  is_frozen: boolean; badges: Array<{ icon: string; name: string }>
}
interface LeaderboardData { leaderboard: LeaderboardEntry[]; team_id?: number }

export default function Leaderboard() {
  const { team } = useAuth()
  const qc = useQueryClient()

  const { data, isLoading } = useQuery<LeaderboardData>({
    queryKey: ['leaderboard'],
    queryFn: () => api.get('/leaderboard'),
  })

  useWebSocket(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws/leaderboard`, {
    leaderboard: (d) => {
      qc.setQueryData(['leaderboard'], (old: LeaderboardData | undefined) => ({
        ...old,
        leaderboard: d['data'] as LeaderboardEntry[],
      }))
    },
    event: (d) => toast.info(`⚡ ${d['title']}: ${d['description']}`, { duration: 8000 }),
    event_end: (d) => toast.info(d['message'] as string),
  })

  if (isLoading || !data) {
    return <div className="flex items-center justify-center min-h-[60vh]"><div className="text-neon-blue animate-pulse text-xl">🏆 Loading rankings...</div></div>
  }

  const { leaderboard } = data
  const myId = team?.id

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <div className="text-center mb-8">
        <h1 className="text-4xl font-black text-white mb-2">🏆 Mission Leaderboard</h1>
        <p className="text-gray-400">Live rankings — updates in real time</p>
        <div className="flex items-center justify-center gap-2 mt-2">
          <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
          <span className="text-green-400 text-xs">Live</span>
        </div>
      </div>

      {/* Top 3 podium */}
      {leaderboard.length >= 3 && (
        <div className="flex items-end justify-center gap-4 mb-8">
          {[leaderboard[1], leaderboard[0], leaderboard[2]].map((entry, i) => {
            const order = [2, 1, 3][i]
            const heights = ['h-24', 'h-32', 'h-20']
            const rankClass = order === 1 ? 'rank-1' : order === 2 ? 'rank-2' : 'rank-3'
            return (
              <div key={entry.id} className="flex flex-col items-center gap-2">
                <div className="text-2xl font-black neon-text text-center">{entry.name}</div>
                <div className={`text-sm font-bold ${rankClass}`}>{entry.score} ⚡</div>
                <div className={`${heights[i]} w-28 glass rounded-t-2xl border border-white/20 flex items-center justify-center`}>
                  <span className={`text-4xl font-black ${rankClass}`}>#{order}</span>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Full table */}
      <div className="glass rounded-2xl border border-white/10 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/10 text-gray-400 text-sm">
              <th className="text-left px-6 py-3">Rank</th>
              <th className="text-left px-4 py-3">Team</th>
              <th className="text-right px-4 py-3">⚡ Fuel</th>
              <th className="text-right px-4 py-3">🪙 Coins</th>
              <th className="text-right px-6 py-3">Badges</th>
            </tr>
          </thead>
          <tbody>
            {leaderboard.map((entry) => (
              <tr
                key={entry.id}
                className={`border-b border-white/5 transition ${entry.id === myId ? 'bg-indigo-900/30' : 'hover:bg-white/5'}`}
              >
                <td className="px-6 py-4">
                  <span className={`text-xl font-black ${entry.rank === 1 ? 'rank-1' : entry.rank === 2 ? 'rank-2' : entry.rank === 3 ? 'rank-3' : 'text-gray-400'}`}>
                    #{entry.rank}
                  </span>
                </td>
                <td className="px-4 py-4">
                  <div className="flex items-center gap-2">
                    {entry.is_frozen && <span title="Frozen">🥶</span>}
                    <span className={`font-bold ${entry.id === myId ? 'text-neon-blue' : 'text-white'}`}>{entry.name}</span>
                    {entry.id === myId && <span className="text-xs text-neon-blue bg-neon-blue/10 px-2 py-0.5 rounded-full">YOU</span>}
                  </div>
                </td>
                <td className="px-4 py-4 text-right font-bold text-yellow-300">{entry.score}</td>
                <td className="px-4 py-4 text-right text-amber-300">{entry.coins}</td>
                <td className="px-6 py-4 text-right">
                  <div className="flex justify-end gap-1">
                    {entry.badges.map((b, i) => (
                      <span key={i} title={b.name} className="text-lg">{b.icon}</span>
                    ))}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {leaderboard.length === 0 && (
          <div className="text-center py-12 text-gray-500">No teams yet.</div>
        )}
      </div>
    </div>
  )
}
