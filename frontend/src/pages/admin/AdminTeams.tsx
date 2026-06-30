import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { api, ApiError } from '@/api/client'

interface Team { id: number; name: string; score: number; coins: number; is_frozen: boolean; created_at: string }

export default function AdminTeams() {
  const qc = useQueryClient()
  const [teamName, setTeamName] = useState('')
  const [password, setPassword] = useState('')
  const [staffUser, setStaffUser] = useState('')
  const [staffPass, setStaffPass] = useState('')
  const [staffRole, setStaffRole] = useState<'tutor' | 'admin'>('tutor')

  const { data } = useQuery<{ teams: Team[] }>({ queryKey: ['admin-teams'], queryFn: () => api.get('/admin/teams') })

  const createTeam = useMutation({
    mutationFn: () => api.post('/admin/teams', { team_name: teamName, password }),
    onSuccess: () => { toast.success('Team created!'); setTeamName(''); setPassword(''); qc.invalidateQueries({ queryKey: ['admin-teams'] }) },
    onError: (e: Error) => toast.error(e instanceof ApiError ? e.message : e.message),
  })

  const deleteTeam = useMutation({
    mutationFn: (id: number) => api.delete(`/admin/teams/${id}`),
    onSuccess: () => { toast.success('Team deleted.'); qc.invalidateQueries({ queryKey: ['admin-teams'] }) },
    onError: (e: Error) => toast.error(e instanceof ApiError ? e.message : e.message),
  })

  const createStaff = useMutation({
    mutationFn: () => api.post('/admin/tutors', { username: staffUser, password: staffPass, role: staffRole }),
    onSuccess: () => { toast.success('Staff account created!'); setStaffUser(''); setStaffPass('') },
    onError: (e: Error) => toast.error(e instanceof ApiError ? e.message : e.message),
  })

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      <h1 className="text-3xl font-black text-white mb-6">👥 Team Management</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Create team */}
        <div className="glass rounded-2xl p-6 border border-white/10">
          <h2 className="font-bold text-white mb-4">➕ Create Team</h2>
          <div className="space-y-3">
            <input value={teamName} onChange={e => setTeamName(e.target.value)} placeholder="Team name"
              className="w-full bg-space-700 border border-white/10 rounded-xl px-3 py-2 text-white text-sm focus:outline-none" />
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Password"
              className="w-full bg-space-700 border border-white/10 rounded-xl px-3 py-2 text-white text-sm focus:outline-none" />
            <button onClick={() => createTeam.mutate()} disabled={!teamName || !password || createTeam.isPending}
              className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-2.5 rounded-xl transition disabled:opacity-50">
              Create Team
            </button>
          </div>
        </div>

        {/* Create staff */}
        <div className="glass rounded-2xl p-6 border border-white/10">
          <h2 className="font-bold text-white mb-4">🛸 Create Staff Account</h2>
          <div className="space-y-3">
            <input value={staffUser} onChange={e => setStaffUser(e.target.value)} placeholder="Username"
              className="w-full bg-space-700 border border-white/10 rounded-xl px-3 py-2 text-white text-sm focus:outline-none" />
            <input type="password" value={staffPass} onChange={e => setStaffPass(e.target.value)} placeholder="Password"
              className="w-full bg-space-700 border border-white/10 rounded-xl px-3 py-2 text-white text-sm focus:outline-none" />
            <select value={staffRole} onChange={e => setStaffRole(e.target.value as 'tutor' | 'admin')}
              className="w-full bg-space-700 border border-white/10 rounded-xl px-3 py-2 text-white text-sm focus:outline-none">
              <option value="tutor">Tutor</option>
              <option value="admin">Admin</option>
            </select>
            <button onClick={() => createStaff.mutate()} disabled={!staffUser || !staffPass || createStaff.isPending}
              className="w-full bg-purple-600 hover:bg-purple-500 text-white font-bold py-2.5 rounded-xl transition disabled:opacity-50">
              Create Staff
            </button>
          </div>
        </div>
      </div>

      {/* Teams table */}
      <div className="glass rounded-2xl border border-white/10 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/10 text-gray-400 text-sm">
              <th className="text-left px-6 py-3">Team</th>
              <th className="text-right px-4 py-3">⚡ Fuel</th>
              <th className="text-right px-4 py-3">🪙 Coins</th>
              <th className="text-left px-4 py-3">Status</th>
              <th className="text-right px-6 py-3">Action</th>
            </tr>
          </thead>
          <tbody>
            {data?.teams.map(t => (
              <tr key={t.id} className="border-b border-white/5 hover:bg-white/5 transition">
                <td className="px-6 py-4 font-bold text-white">{t.name}</td>
                <td className="px-4 py-4 text-right text-yellow-300">{t.score}</td>
                <td className="px-4 py-4 text-right text-amber-300">{t.coins}</td>
                <td className="px-4 py-4">
                  {t.is_frozen ? <span className="text-blue-400 text-sm">🥶 Frozen</span> : <span className="text-green-400 text-sm">✅ Active</span>}
                </td>
                <td className="px-6 py-4 text-right">
                  <button
                    onClick={() => { if (confirm(`Delete team "${t.name}"?`)) deleteTeam.mutate(t.id) }}
                    className="text-red-400 hover:text-red-300 text-sm transition"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!data?.teams.length && <div className="text-center py-12 text-gray-500">No teams yet.</div>}
      </div>
    </div>
  )
}
