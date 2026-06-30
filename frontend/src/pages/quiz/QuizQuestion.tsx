import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { api } from '@/api/client'

interface QuizQ {
  id: number; category: string; question: string; points: number; joke_hint?: string
  option_a: string; option_b: string; option_c: string; option_d: string
  correct: string; explanation?: string
}
interface QuizAttempt { chosen: string; is_correct: boolean; points_awarded: number }
interface QuizQuestionData {
  question: QuizQ; attempt: QuizAttempt | null
  q_number: number; q_total: number; prev_id: number | null; next_id: number | null
}

const letters = ['a', 'b', 'c', 'd'] as const

export default function QuizQuestion() {
  const { id } = useParams<{ id: string }>()
  const qc = useQueryClient()
  const [selected, setSelected] = useState<string>('')

  const { data, isLoading } = useQuery<QuizQuestionData>({
    queryKey: ['quiz-question', id],
    queryFn: () => api.get(`/quiz/${id}`),
  })

  const answer = useMutation({
    mutationFn: () => api.post<{ correct: boolean; points_awarded: number }>(`/quiz/${id}/answer`, { answer: selected }),
    onSuccess: (r) => {
      if (r.correct) toast.success(`🎉 Correct! +${r.points_awarded} points!`)
      else toast.error('❌ Wrong answer.')
      qc.invalidateQueries({ queryKey: ['quiz-question', id] })
      qc.invalidateQueries({ queryKey: ['quiz'] })
    },
  })

  if (isLoading || !data) {
    return <div className="flex items-center justify-center min-h-[60vh]"><div className="text-neon-purple animate-pulse">🧠 Loading question...</div></div>
  }

  const { question: q, attempt, q_number, q_total, prev_id, next_id } = data
  const optionMap: Record<string, string> = { a: q.option_a, b: q.option_b, c: q.option_c, d: q.option_d }

  function optionStyle(letter: string) {
    if (!attempt) {
      return selected === letter
        ? 'border-neon-purple bg-neon-purple/20 text-white'
        : 'border-white/10 hover:border-white/30 text-gray-300 hover:text-white'
    }
    if (letter === q.correct) return 'border-green-500 bg-green-900/30 text-green-300'
    if (letter === attempt.chosen && !attempt.is_correct) return 'border-red-500 bg-red-900/30 text-red-300'
    return 'border-white/10 text-gray-500'
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-8">
      <div className="flex items-center justify-between mb-6">
        <Link to="/quiz" className="text-gray-500 hover:text-gray-300 text-sm transition">← All Questions</Link>
        <span className="text-gray-400 text-sm">Question {q_number} / {q_total}</span>
      </div>

      <div className="glass rounded-2xl p-6 border border-white/10 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-xs px-2 py-0.5 rounded-full bg-neon-purple/20 text-neon-purple font-semibold">{q.category}</span>
          <span className="text-xs text-gray-400">+{q.points} points</span>
        </div>
        <h2 className="text-xl font-bold text-white leading-relaxed">{q.question}</h2>
        {q.joke_hint && !attempt && (
          <p className="text-gray-500 text-sm mt-3 italic">💭 {q.joke_hint}</p>
        )}
      </div>

      <div className="space-y-3 mb-6">
        {letters.map(letter => (
          <button
            key={letter}
            onClick={() => !attempt && setSelected(letter)}
            disabled={!!attempt}
            className={`w-full glass rounded-xl p-4 border text-left transition flex items-center gap-4 ${optionStyle(letter)}`}
          >
            <span className="w-8 h-8 rounded-full bg-space-600 flex items-center justify-center font-bold text-sm flex-shrink-0 uppercase">{letter}</span>
            <span>{optionMap[letter]}</span>
          </button>
        ))}
      </div>

      {!attempt ? (
        <button
          onClick={() => answer.mutate()}
          disabled={!selected || answer.isPending}
          className="w-full bg-gradient-to-r from-neon-purple/80 to-indigo-600 hover:from-neon-purple hover:to-indigo-500 text-white font-bold py-3 rounded-xl transition disabled:opacity-50"
        >
          {answer.isPending ? 'Checking...' : '✅ Submit Answer'}
        </button>
      ) : (
        <div className={`glass rounded-2xl p-5 border ${attempt.is_correct ? 'border-green-500/50' : 'border-red-500/50'}`}>
          <div className={`font-bold text-lg mb-2 ${attempt.is_correct ? 'text-green-400' : 'text-red-400'}`}>
            {attempt.is_correct ? `✅ Correct! +${attempt.points_awarded} points` : '❌ Incorrect'}
          </div>
          {q.explanation && <p className="text-gray-300 text-sm">{q.explanation}</p>}
        </div>
      )}

      <div className="flex justify-between mt-6">
        {prev_id ? (
          <Link to={`/quiz/${prev_id}`} onClick={() => setSelected('')} className="glass px-4 py-2 rounded-xl border border-white/10 hover:border-white/30 text-sm transition">
            ← Previous
          </Link>
        ) : <div />}
        {next_id ? (
          <Link to={`/quiz/${next_id}`} onClick={() => setSelected('')} className="glass px-4 py-2 rounded-xl border border-white/10 hover:border-white/30 text-sm transition">
            Next →
          </Link>
        ) : (
          <Link to="/quiz" className="glass px-4 py-2 rounded-xl border border-neon-purple/30 text-neon-purple text-sm transition hover:border-neon-purple">
            Finish Quiz ✓
          </Link>
        )}
      </div>
    </div>
  )
}
