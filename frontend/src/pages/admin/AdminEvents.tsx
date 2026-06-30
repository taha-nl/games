import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { api, ApiError } from '@/api/client'

interface Event { id: number; title: string; event_type: string; multiplier: number; bonus_points: number; is_active: boolean; started_at: string }

const QUICK_EVENTS = [
  { title: '🏆 Treasure Hunt', event_type: 'treasure_hunt', multiplier: 1.5, bonus_points: 0, description: 'Hidden bonus challenges active!' },
  { title: '⚡ Speed Round', event_type: 'speed_round', multiplier: 2.0, bonus_points: 0, description: 'Double points for all submissions!' },
  { title: '⚡ Lightning Challenge', event_type: 'lightning_challenge', multiplier: 1.0, bonus_points: 50, description: 'Bonus 50 points to all teams!' },
  { title: '🌟 Global Bonus', event_type: 'global_bonus', multiplier: 1.5, bonus_points: 25, description: '+25 points + 1.5x multiplier!' },
]

export default function AdminEvents() {
  const qc = useQueryClient()
  const [form, setForm] = useState({ title: '', event_type: 'global_bonus', multiplier: '1.5', bonus_points: '0', description: '' })

  const { data } = useQuery<{ events: Event[] }>({ queryKey: ['admin-events'], queryFn: () => api.get('/admin/events') })

  const create = useMutation({
    mutationFn: (payload: Record<string, unknown>) => api.post('/admin/events', payload),
    onSuccess: () => { toast.success('Event launched! 🚀'); qc.invalidateQueries({ queryKey: ['admin-events'] }); qc.invalidateQueries({ queryKey: ['admin-stats'] }) },
    onError: (e: Error) => toast.error(e instanceof ApiError ? e.message : e.message),
  })

  const end = useMutation({
    mutationFn: (id: number) => api.post(`/admin/events/${id}/end`),
    onSuccess: () => { toast.success('Event ended.'); qc.invalidateQueries({ queryKey: ['admin-events'] }) },
  })

  const inputClass = 'w-full bg-space-700 border border-white/10 rounded-xl px-3 py-2 text-white text-sm focus:outline-none'

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <h1 className="text-3xl font-black text-white mb-6">⚡ Events</h1>

      {/* Quick events */}
      <div className="mb-6">
        <h2 className="font-bold text-white mb-3">🚀 Quick Launch</h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {QUICK_EVENTS.map(ev => (
            <button key={ev.event_type} onClick={() => create.mutate(ev)} disabled={create.isPending}
              className="glass rounded-xl p-4 border border-white/10 hover:border-yellow-500/30 text-left transition group">
              <div className="font-bold text-white text-sm group-hover:text-yellow-300">{ev.title}</div>
              <div className="text-xs text-gray-400 mt-1">{ev.description}</div>
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Custom event form */}
        <div className="glass rounded-2xl p-6 border border-white/10">
          <h2 className="font-bold text-white mb-4">✏️ Custom Event</h2>
          <div className="space-y-3">
            <input value={form.title} onChange={e => setForm(p => ({ ...p, title: e.target.value }))} placeholder="Event title" className={inputClass} />
            <select value={form.event_type} onChange={e => setForm(p => ({ ...p, event_type: e.target.value }))} className={inputClass}>
              {['treasure_hunt', 'speed_round', 'lightning_challenge', 'global_bonus'].map(t => (
                <option key={t} value={t}>{t.replace('_', ' ')}</option>
              ))}
            </select>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-xs text-gray-400">Multiplier (1.0–2.0)</label>
                <input type="number" step="0.1" min="1" max="2" value={form.multiplier} onChange={e => setForm(p => ({ ...p, multiplier: e.target.value }))} className={inputClass} />
              </div>
              <div>
                <label className="text-xs text-gray-400">Bonus Points</label>
                <input type="number" min="0" value={form.bonus_points} onChange={e => setForm(p => ({ ...p, bonus_points: e.target.value }))} className={inputClass} />
              </div>
            </div>
            <input value={form.description} onChange={e => setForm(p => ({ ...p, description: e.target.value }))} placeholder="Description" className={inputClass} />
            <button onClick={() => create.mutate(form)} disabled={!form.title || create.isPending}
              className="w-full bg-gradient-to-r from-yellow-600 to-orange-600 hover:from-yellow-500 hover:to-orange-500 text-white font-bold py-2.5 rounded-xl transition disabled:opacity-50">
              Launch Event ⚡
            </button>
          </div>
        </div>

        {/* Events list */}
        <div className="space-y-3">
          {data?.events.map(ev => (
            <div key={ev.id} className={`glass rounded-xl p-4 border ${ev.is_active ? 'border-yellow-500/40' : 'border-white/10 opacity-60'}`}>
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-bold text-white">{ev.title}</div>
                  <div className="text-gray-400 text-xs mt-1">×{ev.multiplier} · +{ev.bonus_points}pts bonus · {ev.event_type.replace('_', ' ')}</div>
                  <div className="text-gray-500 text-xs mt-1">{new Date(ev.started_at).toLocaleString()}</div>
                </div>
                {ev.is_active ? (
                  <div className="flex flex-col items-end gap-2">
                    <span className="text-xs px-2 py-0.5 bg-yellow-900/50 text-yellow-300 rounded-full font-semibold">LIVE</span>
                    <button onClick={() => end.mutate(ev.id)} className="text-xs px-3 py-1 bg-red-700 hover:bg-red-600 text-white rounded-lg transition">End</button>
                  </div>
                ) : (
                  <span className="text-xs text-gray-500">Ended</span>
                )}
              </div>
            </div>
          ))}
          {!data?.events.length && <div className="text-center py-8 text-gray-500">No events yet.</div>}
        </div>
      </div>
    </div>
  )
}
