import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/api/client'

interface QuizQuestion { id: number; category: string; question: string; points: number }
interface QuizData {
  questions: QuizQuestion[]; correct_ids: number[]; answered_ids: number[]
  categories: string[]; total_pts: number
}

export default function QuizIndex() {
  const [activeCategory, setActiveCategory] = useState('All')
  const { data, isLoading } = useQuery<QuizData>({
    queryKey: ['quiz'],
    queryFn: () => api.get('/quiz'),
  })

  if (isLoading || !data) {
    return <div className="flex items-center justify-center min-h-[60vh]"><div className="text-neon-purple animate-pulse">🧠 Loading quiz...</div></div>
  }

  const { questions, correct_ids, answered_ids, categories, total_pts } = data
  const visible = activeCategory === 'All' ? questions : questions.filter(q => q.category === activeCategory)

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-4xl font-black text-white">🧠 Algorithm Quiz</h1>
          <p className="text-gray-400 mt-1">Test your algorithmic knowledge for bonus points</p>
        </div>
        <div className="glass rounded-2xl px-5 py-3 text-center">
          <div className="text-2xl font-black text-neon-purple">{total_pts}</div>
          <div className="text-xs text-gray-400 uppercase tracking-wide">Points Earned</div>
        </div>
      </div>

      {/* Category filter */}
      <div className="flex flex-wrap gap-2 mb-6">
        {['All', ...categories].map(cat => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={`px-4 py-1.5 rounded-full text-sm font-semibold transition ${activeCategory === cat ? 'bg-neon-purple text-white' : 'glass text-gray-400 hover:text-white border border-white/10'}`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Questions grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {visible.map(q => {
          const correct = correct_ids.includes(q.id)
          const answered = answered_ids.includes(q.id)
          return (
            <Link
              key={q.id}
              to={`/quiz/${q.id}`}
              className={`glass rounded-2xl p-5 border transition-all block group ${correct ? 'border-green-500/50 bg-green-900/10' : answered ? 'border-red-500/30' : 'border-white/10 hover:border-neon-purple/40'}`}
            >
              <div className="flex items-start justify-between mb-3">
                <span className="text-xs px-2 py-0.5 rounded-full bg-neon-purple/20 text-neon-purple font-semibold">{q.category}</span>
                <div className="text-right">
                  {correct ? (
                    <span className="text-green-400 font-bold">✓ {q.points}pts</span>
                  ) : (
                    <span className="text-gray-400 text-sm">+{q.points}pts</span>
                  )}
                </div>
              </div>
              <p className="text-white font-semibold text-sm group-hover:text-neon-purple transition line-clamp-2">{q.question}</p>
              {answered && !correct && <p className="text-red-400 text-xs mt-2">❌ Wrong answer</p>}
            </Link>
          )
        })}
      </div>

      {visible.length === 0 && (
        <div className="text-center py-16 text-gray-500">No questions in this category.</div>
      )}
    </div>
  )
}
