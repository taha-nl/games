import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { api, ApiError } from '@/api/client'

interface QuizQuestion {
  id: number; category: string; question: string; points: number
  option_a: string; option_b: string; option_c: string; option_d: string
  correct: string; explanation: string; is_active: boolean
}

const emptyForm = { category: '', question: '', option_a: '', option_b: '', option_c: '', option_d: '', correct: 'a', points: '10', explanation: '', joke_hint: '' }

export default function AdminQuiz() {
  const qc = useQueryClient()
  const [form, setForm] = useState(emptyForm)
  const [editing, setEditing] = useState<number | null>(null)

  const { data } = useQuery<{ questions: QuizQuestion[] }>({ queryKey: ['admin-quiz'], queryFn: () => api.get('/admin/quiz') })

  const save = useMutation({
    mutationFn: () => editing
      ? api.post(`/admin/quiz/${editing}/edit`, form)
      : api.post('/admin/quiz', form),
    onSuccess: () => { toast.success(editing ? 'Updated!' : 'Created!'); setForm(emptyForm); setEditing(null); qc.invalidateQueries({ queryKey: ['admin-quiz'] }) },
    onError: (e: Error) => toast.error(e instanceof ApiError ? e.message : e.message),
  })

  const toggle = useMutation({
    mutationFn: (id: number) => api.post(`/admin/quiz/${id}/toggle`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin-quiz'] }),
  })

  const del = useMutation({
    mutationFn: (id: number) => api.delete(`/admin/quiz/${id}`),
    onSuccess: () => { toast.success('Deleted.'); qc.invalidateQueries({ queryKey: ['admin-quiz'] }) },
  })

  function startEdit(q: QuizQuestion) {
    setEditing(q.id)
    setForm({ category: q.category, question: q.question, option_a: q.option_a, option_b: q.option_b, option_c: q.option_c, option_d: q.option_d, correct: q.correct, points: String(q.points), explanation: q.explanation, joke_hint: '' })
  }

  const f = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => setForm(p => ({ ...p, [k]: e.target.value }))
  const inputClass = 'w-full bg-space-700 border border-white/10 rounded-xl px-3 py-2 text-white text-sm focus:outline-none'

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      <h1 className="text-3xl font-black text-white mb-6">🧠 Quiz Management</h1>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Form */}
        <div className="lg:col-span-2">
          <div className="glass rounded-2xl p-6 border border-white/10">
            <h2 className="font-bold text-white mb-4">{editing ? '✏️ Edit Question' : '➕ New Question'}</h2>
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-2">
                <input value={form.category} onChange={f('category')} placeholder="Category" className={inputClass} />
                <input type="number" value={form.points} onChange={f('points')} placeholder="Points" className={inputClass} />
              </div>
              <textarea value={form.question} onChange={f('question')} placeholder="Question..." rows={3} className={`${inputClass} resize-none`} />
              {(['a', 'b', 'c', 'd'] as const).map(l => (
                <input key={l} value={form[`option_${l}` as keyof typeof form]} onChange={f(`option_${l}` as keyof typeof form)} placeholder={`Option ${l.toUpperCase()}`} className={inputClass} />
              ))}
              <div>
                <label className="text-xs text-gray-400 block mb-1">Correct Answer</label>
                <select value={form.correct} onChange={f('correct')} className={inputClass}>
                  {['a', 'b', 'c', 'd'].map(l => <option key={l} value={l}>{l.toUpperCase()}</option>)}
                </select>
              </div>
              <textarea value={form.explanation} onChange={f('explanation')} placeholder="Explanation (shown after answering)" rows={2} className={`${inputClass} resize-none`} />
              <div className="flex gap-2">
                <button onClick={() => save.mutate()} disabled={!form.question || !form.category || save.isPending}
                  className="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-2.5 rounded-xl transition disabled:opacity-50 text-sm">
                  {editing ? 'Update' : 'Create'}
                </button>
                {editing && (
                  <button onClick={() => { setEditing(null); setForm(emptyForm) }}
                    className="px-4 bg-space-600 border border-white/10 text-gray-400 rounded-xl text-sm transition hover:text-white">
                    Cancel
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* List */}
        <div className="lg:col-span-3 space-y-3 max-h-[70vh] overflow-y-auto pr-1">
          {data?.questions.map(q => (
            <div key={q.id} className={`glass rounded-xl p-4 border ${q.is_active ? 'border-white/10' : 'border-white/5 opacity-60'}`}>
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs px-2 py-0.5 bg-neon-purple/20 text-neon-purple rounded-full">{q.category}</span>
                    <span className="text-xs text-gray-400">+{q.points}pts · Answer: {q.correct.toUpperCase()}</span>
                  </div>
                  <p className="text-white text-sm line-clamp-2">{q.question}</p>
                </div>
                <div className="flex flex-col gap-1 flex-shrink-0">
                  <button onClick={() => startEdit(q)} className="text-xs px-2 py-1 glass border border-white/10 rounded text-gray-300 hover:text-white">Edit</button>
                  <button onClick={() => toggle.mutate(q.id)} className={`text-xs px-2 py-1 rounded border ${q.is_active ? 'border-red-500/30 text-red-400' : 'border-green-500/30 text-green-400'}`}>
                    {q.is_active ? 'Hide' : 'Show'}
                  </button>
                  <button onClick={() => { if (confirm('Delete?')) del.mutate(q.id) }} className="text-xs px-2 py-1 text-red-400 hover:text-red-300">Del</button>
                </div>
              </div>
            </div>
          ))}
          {!data?.questions.length && <div className="text-center py-8 text-gray-500">No quiz questions yet.</div>}
        </div>
      </div>
    </div>
  )
}
