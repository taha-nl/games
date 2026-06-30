import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { api, ApiError } from '@/api/client'

interface Stats {
  total_teams: number; total_challenges: number
  pending_submissions: number; approved_submissions: number
  active_event: { title: string; multiplier: number } | null
}
interface Team { id: number; name: string; score: number; coins: number; is_frozen: boolean }

export default function AdminDashboard() {
  const qc = useQueryClient()
  const [awardTeam, setAwardTeam] = useState('')
  const [awardPts, setAwardPts] = useState('')
  const [awardCoins, setAwardCoins] = useState('')
  const [resetConfirm, setResetConfirm] = useState('')

  const { data: stats } = useQuery<Stats>({ queryKey: ['admin-stats'], queryFn: () => api.get('/admin/stats') })
  const { data: teamsData } = useQuery<{ teams: Team[] }>({ queryKey: ['admin-teams'], queryFn: () => api.get('/admin/teams') })

  const awardPoints = useMutation({
    mutationFn: () => api.post('/admin/award_points', { team_id: awardTeam, points: awardPts }),
    onSuccess: () => { toast.success('Points awarded!'); qc.invalidateQueries({ queryKey: ['admin-teams'] }); setAwardPts('') },
    onError: (e: Error) => toast.error(e instanceof ApiError ? e.message : e.message),
  })

  const awardCoinsM = useMutation({
    mutationFn: () => api.post('/admin/award_coins', { team_id: awardTeam, coins: awardCoins }),
    onSuccess: () => { toast.success('Coins awarded!'); qc.invalidateQueries({ queryKey: ['admin-teams'] }); setAwardCoins('') },
    onError: (e: Error) => toast.error(e instanceof ApiError ? e.message : e.message),
  })

  const reset = useMutation({
    mutationFn: () => api.post('/admin/reset', { confirm: resetConfirm }),
    onSuccess: () => { toast.success('All scores reset!'); setResetConfirm(''); qc.invalidateQueries() },
    onError: (e: Error) => toast.error(e instanceof ApiError ? e.message : e.message),
  })

  const teams = teamsData?.teams ?? []

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      <h1 className="text-3xl font-black text-white mb-6">⚙️ Admin Dashboard</h1>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {[
          { label: 'Teams', value: stats?.total_teams ?? '—', icon: '👥' },
          { label: 'Challenges', value: stats?.total_challenges ?? '—', icon: '🪐' },
          { label: 'Pending', value: stats?.pending_submissions ?? '—', icon: '⏳', accent: 'text-yellow-300' },
          { label: 'Approved', value: stats?.approved_submissions ?? '—', icon: '✅', accent: 'text-green-300' },
        ].map(s => (
          <div key={s.label} className="glass rounded-2xl p-5 border border-white/10">
            <div className="text-2xl mb-2">{s.icon}</div>
            <div className={`text-3xl font-black ${s.accent ?? 'text-white'}`}>{s.value}</div>
            <div className="text-gray-400 text-sm mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      {stats?.active_event && (
        <div className="mb-6 bg-yellow-900/30 border border-yellow-500/30 rounded-2xl p-4 flex items-center gap-4">
          <span className="text-2xl">⚡</span>
          <span className="text-yellow-300 font-bold">Active Event: {stats.active_event.title} (×{stats.active_event.multiplier})</span>
          <Link to="/admin/events" className="ml-auto text-yellow-400 hover:text-yellow-300 text-sm">Manage →</Link>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Award points */}
        <div className="glass rounded-2xl p-6 border border-white/10">
          <h2 className="font-bold text-white mb-4">⚡ Award Points / Coins</h2>
          <div className="space-y-3">
            <select value={awardTeam} onChange={e => setAwardTeam(e.target.value)}
              className="w-full bg-space-700 border border-white/10 rounded-xl px-3 py-2 text-white text-sm focus:outline-none">
              <option value="">Select team...</option>
              {teams.map(t => <option key={t.id} value={t.id}>{t.name} ({t.score}⚡)</option>)}
            </select>
            <div className="flex gap-2">
              <input type="number" value={awardPts} onChange={e => setAwardPts(e.target.value)} placeholder="Points"
                className="flex-1 bg-space-700 border border-white/10 rounded-xl px-3 py-2 text-white text-sm focus:outline-none" />
              <button onClick={() => awardPoints.mutate()} disabled={!awardTeam || !awardPts}
                className="px-4 py-2 bg-yellow-600 hover:bg-yellow-500 text-white rounded-xl text-sm font-bold transition disabled:opacity-50">
                +Fuel
              </button>
            </div>
            <div className="flex gap-2">
              <input type="number" value={awardCoins} onChange={e => setAwardCoins(e.target.value)} placeholder="Coins"
                className="flex-1 bg-space-700 border border-white/10 rounded-xl px-3 py-2 text-white text-sm focus:outline-none" />
              <button onClick={() => awardCoinsM.mutate()} disabled={!awardTeam || !awardCoins}
                className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-xl text-sm font-bold transition disabled:opacity-50">
                +Coins
              </button>
            </div>
          </div>
        </div>

        {/* Quick links */}
        <div className="glass rounded-2xl p-6 border border-white/10">
          <h2 className="font-bold text-white mb-4">🚀 Quick Navigation</h2>
          <div className="grid grid-cols-2 gap-3">
            {[
              { to: '/admin/teams', label: '👥 Teams' },
              { to: '/admin/challenges', label: '🪐 Challenges' },
              { to: '/admin/events', label: '⚡ Events' },
              { to: '/admin/quiz', label: '🧠 Quiz' },
              { to: '/tutor/submissions', label: '📋 Submissions' },
              { to: '/leaderboard', label: '🏆 Leaderboard' },
            ].map(l => (
              <Link key={l.to} to={l.to} className="glass rounded-xl p-3 border border-white/10 hover:border-indigo-400/50 text-sm font-semibold text-gray-300 hover:text-white transition text-center">
                {l.label}
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* Danger zone */}
      <div className="mt-6 glass rounded-2xl p-6 border border-red-500/30">
        <h2 className="font-bold text-red-400 mb-4">💣 Danger Zone</h2>
        <div className="flex gap-3 items-end">
          <div className="flex-1">
            <label className="block text-sm text-gray-400 mb-1">Type <span className="font-mono text-red-400">RESET</span> to confirm</label>
            <input type="text" value={resetConfirm} onChange={e => setResetConfirm(e.target.value)} placeholder="RESET"
              className="w-full bg-space-700 border border-red-500/30 rounded-xl px-3 py-2 text-white text-sm focus:outline-none" />
          </div>
          <button onClick={() => reset.mutate()} disabled={resetConfirm !== 'RESET' || reset.isPending}
            className="px-5 py-2 bg-red-700 hover:bg-red-600 text-white rounded-xl text-sm font-bold transition disabled:opacity-50">
            Reset All Scores
          </button>
        </div>
      </div>
    </div>
  )
}
