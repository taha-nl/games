import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Editor from '@monaco-editor/react'
import { toast } from 'sonner'
import { api, ApiError } from '@/api/client'

interface Submission {
  id: number; code: string; status: string
  team_id: number; team_name: string; challenge_title: string
  submitted_at: string; points_awarded: number | null; tutor_comment: string | null
  double_points_active: boolean
}
interface DetailData { submission: Submission }

export default function SubmissionDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [comment, setComment] = useState('')
  const [bonusPoints, setBonusPoints] = useState(0)
  const [hint, setHint] = useState('')

  const { data, isLoading } = useQuery<DetailData>({
    queryKey: ['submission-detail', id],
    queryFn: () => api.get(`/tutor/submissions/${id}`),
  })

  const approve = useMutation({
    mutationFn: () => api.post(`/tutor/submissions/${id}/approve`, { comment, bonus_points: bonusPoints }),
    onSuccess: () => { toast.success('✅ Approved!'); qc.invalidateQueries({ queryKey: ['tutor-submissions'] }); navigate('/tutor/submissions') },
    onError: (e: Error) => toast.error(e instanceof ApiError ? e.message : e.message),
  })

  const reject = useMutation({
    mutationFn: () => api.post(`/tutor/submissions/${id}/reject`, { comment }),
    onSuccess: () => { toast.success('Rejected.'); qc.invalidateQueries({ queryKey: ['tutor-submissions'] }); navigate('/tutor/submissions') },
    onError: (e: Error) => toast.error(e instanceof ApiError ? e.message : e.message),
  })

  const sendHint = useMutation({
    mutationFn: () => api.post(`/tutor/hint/${data?.submission.team_id}`, { hint_text: hint }),
    onSuccess: () => { toast.success('💡 Hint sent!'); setHint('') },
    onError: (e: Error) => toast.error(e instanceof ApiError ? e.message : e.message),
  })

  if (isLoading || !data) {
    return <div className="flex items-center justify-center min-h-[60vh]"><div className="text-neon-blue animate-pulse">Loading...</div></div>
  }

  const { submission: s } = data
  const isPending = s.status === 'pending'

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      <div className="mb-6">
        <Link to="/tutor/submissions" className="text-gray-500 hover:text-gray-300 text-sm transition">← Back to Submissions</Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Code viewer */}
        <div className="lg:col-span-2">
          <div className="glass rounded-2xl border border-white/10 overflow-hidden">
            <div className="px-5 py-4 border-b border-white/10 flex items-center justify-between">
              <div>
                <h2 className="font-bold text-white">{s.team_name}</h2>
                <p className="text-gray-400 text-sm">{s.challenge_title}</p>
              </div>
              <div className="text-right">
                <div className={`text-xs px-2 py-0.5 rounded-full font-semibold border capitalize inline-block ${s.status === 'pending' ? 'bg-yellow-900/50 text-yellow-300 border-yellow-500/30' : s.status === 'approved' ? 'bg-green-900/50 text-green-300 border-green-500/30' : 'bg-red-900/50 text-red-300 border-red-500/30'}`}>
                  {s.status}
                </div>
                {s.double_points_active && (
                  <div className="text-yellow-400 text-xs mt-1">⚡ Double Points Active</div>
                )}
              </div>
            </div>
            <Editor
              height="500px"
              language="python"
              theme="vs-dark"
              value={s.code}
              options={{ readOnly: true, fontSize: 13, minimap: { enabled: false }, scrollBeyondLastLine: false }}
            />
          </div>
        </div>

        {/* Review panel */}
        <div className="space-y-4">
          <div className="glass rounded-2xl p-5 border border-white/10">
            <div className="text-sm text-gray-400 mb-3">Submitted {new Date(s.submitted_at).toLocaleString()}</div>

            {isPending ? (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Comment (optional)</label>
                  <textarea
                    value={comment}
                    onChange={e => setComment(e.target.value)}
                    rows={3}
                    placeholder="Feedback for the team..."
                    className="w-full bg-space-700 border border-white/10 rounded-xl px-3 py-2 text-white text-sm placeholder-gray-600 focus:outline-none focus:border-neon-blue/50 resize-none"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Bonus Points</label>
                  <input
                    type="number"
                    value={bonusPoints}
                    onChange={e => setBonusPoints(Number(e.target.value))}
                    min={0}
                    className="w-full bg-space-700 border border-white/10 rounded-xl px-3 py-2 text-white text-sm focus:outline-none focus:border-neon-blue/50"
                  />
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => approve.mutate()}
                    disabled={approve.isPending}
                    className="flex-1 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 text-white font-bold py-2.5 rounded-xl transition text-sm disabled:opacity-50"
                  >
                    ✅ Approve
                  </button>
                  <button
                    onClick={() => reject.mutate()}
                    disabled={reject.isPending || !comment}
                    className="flex-1 bg-gradient-to-r from-red-700 to-red-600 hover:from-red-600 hover:to-red-500 text-white font-bold py-2.5 rounded-xl transition text-sm disabled:opacity-50"
                  >
                    ❌ Reject
                  </button>
                </div>
              </div>
            ) : (
              <div>
                {s.points_awarded != null && <div className="text-yellow-300 font-bold">+{s.points_awarded} fuel awarded</div>}
                {s.tutor_comment && <div className="text-gray-300 text-sm mt-2 glass rounded-xl p-3">{s.tutor_comment}</div>}
              </div>
            )}
          </div>

          {/* Hint sender */}
          <div className="glass rounded-2xl p-5 border border-white/10">
            <h3 className="font-bold text-white mb-3">💡 Send Hint</h3>
            <textarea
              value={hint}
              onChange={e => setHint(e.target.value)}
              rows={3}
              placeholder="Type a hint for the team..."
              className="w-full bg-space-700 border border-white/10 rounded-xl px-3 py-2 text-white text-sm placeholder-gray-600 focus:outline-none resize-none mb-2"
            />
            <button
              onClick={() => sendHint.mutate()}
              disabled={!hint.trim() || sendHint.isPending}
              className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-2 rounded-xl transition text-sm disabled:opacity-50"
            >
              Send Hint
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
