import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { api, ApiError } from '@/api/client'

interface Challenge {
  id: number; title: string; planet_name: string; difficulty: string
  points: number; is_active: boolean; test_case_count: number
}

export default function AdminChallenges() {
  const qc = useQueryClient()
  const [form, setForm] = useState({ title: '', planet_name: '', difficulty: 'easy', points: '100', description: '', examples: '', starter_code: '', coins_reward: '10', challenge_type: 'code' })

  const { data } = useQuery<{ challenges: Challenge[] }>({ queryKey: ['admin-challenges'], queryFn: () => api.get('/admin/challenges') })

  const create = useMutation({
    mutationFn: () => api.post('/admin/challenges', form),
    onSuccess: () => { toast.success('Challenge created!'); setForm({ title: '', planet_name: '', difficulty: 'easy', points: '100', description: '', examples: '', starter_code: '', coins_reward: '10', challenge_type: 'code' }); qc.invalidateQueries({ queryKey: ['admin-challenges'] }) },
    onError: (e: Error) => toast.error(e instanceof ApiError ? e.message : e.message),
  })

  const toggle = useMutation({
    mutationFn: (id: number) => api.post(`/admin/challenges/${id}/toggle`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin-challenges'] }),
  })

  const f = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
    setForm(prev => ({ ...prev, [k]: e.target.value }))

  const inputClass = 'w-full bg-space-700 border border-white/10 rounded-xl px-3 py-2 text-white text-sm focus:outline-none focus:border-neon-blue/40'

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      <h1 className="text-3xl font-black text-white mb-6">🪐 Challenge Management</h1>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Create form */}
        <div className="lg:col-span-2">
          <div className="glass rounded-2xl p-6 border border-white/10">
            <h2 className="font-bold text-white mb-4">➕ New Challenge</h2>
            <div className="space-y-3">
              <input value={form.title} onChange={f('title')} placeholder="Title" className={inputClass} />
              <input value={form.planet_name} onChange={f('planet_name')} placeholder="Planet name" className={inputClass} />
              <div className="grid grid-cols-2 gap-2">
                <select value={form.challenge_type} onChange={f('challenge_type')} className={inputClass}>
                  <option value="code">💻 Code</option>
                  <option value="riddle">🧩 Riddle</option>
                </select>
                <input type="number" value={form.coins_reward} onChange={f('coins_reward')} placeholder="Coin reward" className={inputClass} />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <select value={form.difficulty} onChange={f('difficulty')} className={inputClass}>
                  <option value="easy">Easy</option>
                  <option value="medium">Medium</option>
                  <option value="hard">Hard</option>
                </select>
                <input type="number" value={form.points} onChange={f('points')} placeholder="Points" className={inputClass} />
              </div>
              <textarea value={form.description} onChange={f('description')} placeholder="Description..." rows={4} className={`${inputClass} resize-none`} />
              <textarea value={form.examples} onChange={f('examples')} placeholder="Examples (optional)" rows={2} className={`${inputClass} resize-none`} />
              <textarea value={form.starter_code} onChange={f('starter_code')} placeholder={form.challenge_type === 'riddle' ? 'Answer key (shown to tutors only)' : 'Starter code (optional)'} rows={3} className={`${inputClass} resize-none font-mono text-xs`} />
              <button onClick={() => create.mutate()} disabled={!form.title || !form.description || create.isPending}
                className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-2.5 rounded-xl transition disabled:opacity-50">
                Create Challenge
              </button>
            </div>
          </div>
        </div>

        {/* List */}
        <div className="lg:col-span-3 space-y-3">
          {data?.challenges.map(c => (
            <div key={c.id} className={`glass rounded-xl p-4 border flex items-center justify-between ${c.is_active ? 'border-white/10' : 'border-red-500/20 opacity-60'}`}>
              <div>
                <div className="font-bold text-white">{c.title}</div>
                <div className="text-gray-400 text-xs mt-0.5">{c.planet_name} · {c.difficulty} · {c.points}pts · {c.test_case_count} tests</div>
              </div>
              <div className="flex items-center gap-2">
                <Link to={`/admin/challenges/${c.id}/test-cases`}
                  className="text-xs px-3 py-1 glass border border-white/10 rounded-lg hover:border-indigo-400/50 text-gray-300 hover:text-white transition">
                  Test Cases
                </Link>
                <button onClick={() => toggle.mutate(c.id)}
                  className={`text-xs px-3 py-1 rounded-lg border font-semibold transition ${c.is_active ? 'border-red-500/30 text-red-400 hover:bg-red-900/30' : 'border-green-500/30 text-green-400 hover:bg-green-900/30'}`}>
                  {c.is_active ? 'Deactivate' : 'Activate'}
                </button>
              </div>
            </div>
          ))}
          {!data?.challenges.length && <div className="text-center py-12 text-gray-500">No challenges yet.</div>}
        </div>
      </div>
    </div>
  )
}
