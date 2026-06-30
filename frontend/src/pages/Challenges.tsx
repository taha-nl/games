import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/api/client'

interface Challenge {
  id: number; title: string; planet_name: string; description: string
  difficulty: string; points: number; coins_reward: number; challenge_type: string
}
interface ChallengesData {
  challenges: Challenge[]
  approved_ids: number[]
  pending_ids: number[]
}

const difficultyEmoji: Record<string, string> = { easy: '🟢', medium: '🟡', hard: '🔴' }
const difficultyColor: Record<string, string> = {
  easy: 'bg-green-900/50 text-green-300 border-green-500/30',
  medium: 'bg-yellow-900/50 text-yellow-300 border-yellow-500/30',
  hard: 'bg-red-900/50 text-red-300 border-red-500/30',
}

type Filter = 'all' | 'easy' | 'medium' | 'hard' | 'riddle'

export default function Challenges() {
  const [filter, setFilter] = useState<Filter>('all')
  const { data, isLoading } = useQuery<ChallengesData>({
    queryKey: ['challenges'],
    queryFn: () => api.get('/challenges'),
  })

  if (isLoading || !data) {
    return <div className="flex items-center justify-center min-h-[60vh]"><div className="text-neon-blue animate-pulse text-xl">🪐 Loading planets...</div></div>
  }

  const { challenges, approved_ids, pending_ids } = data
  const visible = filter === 'all'
    ? challenges
    : filter === 'riddle'
    ? challenges.filter(c => c.challenge_type === 'riddle')
    : challenges.filter(c => c.challenge_type !== 'riddle' && c.difficulty === filter)

  const filters: { key: Filter; label: string }[] = [
    { key: 'all', label: 'All' },
    { key: 'easy', label: '🟢 Easy' },
    { key: 'medium', label: '🟡 Medium' },
    { key: 'hard', label: '🔴 Hard' },
    { key: 'riddle', label: '🧩 Riddles' },
  ]

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <div className="flex items-center justify-between mb-8 flex-wrap gap-4">
        <div>
          <h1 className="text-4xl font-black text-white">🪐 Planet Map</h1>
          <p className="text-gray-400 mt-1">Explore and conquer all challenges across the galaxy</p>
        </div>
        <div className="flex gap-1 bg-space-700 p-1 rounded-xl flex-wrap">
          {filters.map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setFilter(key)}
              className={`px-4 py-1.5 rounded-lg text-sm font-semibold transition ${filter === key ? (key === 'riddle' ? 'bg-neon-purple text-white' : 'bg-indigo-600 text-white') : 'text-gray-400 hover:text-white'}`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {visible.map(c => {
          const isRiddle = c.challenge_type === 'riddle'
          const solved = approved_ids.includes(c.id)
          const pending = pending_ids.includes(c.id)
          return (
            <Link
              key={c.id}
              to={`/challenge/${c.id}`}
              className={`planet-card glass rounded-2xl p-5 border transition-all duration-200 block group ${solved ? 'border-green-500/50 bg-green-900/10' : pending ? 'border-yellow-500/30' : isRiddle ? 'border-neon-purple/20 hover:border-neon-purple/50' : 'border-white/10 hover:border-indigo-400/50'}`}
            >
              <div className="flex items-start justify-between mb-3">
                <span className="text-4xl">{isRiddle ? '🧩' : (difficultyEmoji[c.difficulty] ?? '⚪')}</span>
                <div className="text-right">
                  {solved ? (
                    <span className="text-green-400 font-bold text-lg">✓ Solved</span>
                  ) : pending ? (
                    <span className="text-yellow-300 font-bold text-sm">⏳ Pending</span>
                  ) : (
                    <div>
                      <div className="text-yellow-300 font-bold">+{c.points} ⚡</div>
                      <div className="text-amber-400 text-xs">+{c.coins_reward} 🪙</div>
                    </div>
                  )}
                </div>
              </div>
              <h3 className={`font-bold text-white text-lg transition ${isRiddle ? 'group-hover:text-neon-purple' : 'group-hover:text-neon-blue'}`}>{c.title}</h3>
              <p className="text-gray-400 text-sm mt-0.5 mb-3">{c.planet_name}</p>
              <p className="text-gray-500 text-sm line-clamp-2">{c.description}</p>
              <div className="mt-3 flex items-center gap-2">
                {isRiddle ? (
                  <span className="text-xs px-2 py-0.5 rounded-full font-semibold border bg-neon-purple/10 text-neon-purple border-neon-purple/30">
                    🧩 RIDDLE
                  </span>
                ) : (
                  <span className={`text-xs px-2 py-0.5 rounded-full font-semibold border ${difficultyColor[c.difficulty] ?? ''}`}>
                    {c.difficulty.toUpperCase()}
                  </span>
                )}
              </div>
            </Link>
          )
        })}
      </div>

      {visible.length === 0 && (
        <div className="text-center py-20 text-gray-500">
          <div className="text-5xl mb-4">🌌</div>
          <p>No {filter === 'riddle' ? 'riddles' : filter} challenges found.</p>
        </div>
      )}
    </div>
  )
}
