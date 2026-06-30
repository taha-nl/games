import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/api/client'

interface Submission {
  id: number; team_name: string; challenge_title: string
  status: string; submitted_at: string; points_awarded: number | null
}
interface SubmissionsData { submissions: Submission[]; pending_count: number; status_filter: string }

const statusColor: Record<string, string> = {
  pending:  'bg-yellow-900/50 text-yellow-300 border-yellow-500/30',
  approved: 'bg-green-900/50 text-green-300 border-green-500/30',
  rejected: 'bg-red-900/50 text-red-300 border-red-500/30',
}

export default function Submissions() {
  const [filter, setFilter] = useState('pending')

  const { data, isLoading } = useQuery<SubmissionsData>({
    queryKey: ['tutor-submissions', filter],
    queryFn: () => api.get(`/tutor/submissions?status_filter=${filter}`),
    refetchInterval: 15_000,
  })

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-black text-white">📋 Submission Queue</h1>
          {data && <p className="text-yellow-400 mt-1">{data.pending_count} pending review</p>}
        </div>
        <div className="flex gap-2">
          {['pending', 'approved', 'rejected', 'all'].map(s => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`px-4 py-1.5 rounded-lg text-sm font-semibold transition capitalize ${filter === s ? 'bg-indigo-600 text-white' : 'glass border border-white/10 text-gray-400 hover:text-white'}`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-neon-blue animate-pulse">Loading submissions...</div>
      ) : (
        <div className="glass rounded-2xl border border-white/10 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/10 text-gray-400 text-sm">
                <th className="text-left px-6 py-3">Team</th>
                <th className="text-left px-4 py-3">Challenge</th>
                <th className="text-left px-4 py-3">Submitted</th>
                <th className="text-left px-4 py-3">Status</th>
                <th className="text-right px-6 py-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {data?.submissions.map(s => (
                <tr key={s.id} className="border-b border-white/5 hover:bg-white/5 transition">
                  <td className="px-6 py-4 font-bold text-white">{s.team_name}</td>
                  <td className="px-4 py-4 text-gray-300">{s.challenge_title}</td>
                  <td className="px-4 py-4 text-gray-500 text-sm">
                    {new Date(s.submitted_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-4">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-semibold border capitalize ${statusColor[s.status] ?? ''}`}>
                      {s.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <Link
                      to={`/tutor/submission/${s.id}`}
                      className="text-indigo-400 hover:text-indigo-300 text-sm transition"
                    >
                      Review →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!data?.submissions.length && (
            <div className="text-center py-12 text-gray-500">No {filter} submissions.</div>
          )}
        </div>
      )}
    </div>
  )
}
