import { useState, useRef, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Editor from '@monaco-editor/react'
import { toast } from 'sonner'
import { api, ApiError } from '@/api/client'

interface TestCase { id: number; stdin: string; expected_output: string; is_hidden: boolean }
interface Challenge {
  id: number; title: string; planet_name: string; description: string
  difficulty: string; points: number; examples: string; starter_code: string
  test_cases: TestCase[]
}
interface DetailData {
  challenge: Challenge
  already_approved: boolean
  active_event: { title: string; multiplier: number } | null
  last_submission: { code: string; status: string; tutor_comment: string } | null
}

interface RunResult {
  mode: 'tests' | 'plain'
  stdout?: string; stderr?: string; exit_code?: number; timed_out?: boolean
  all_passed?: boolean; passed?: number; total?: number
  results?: Array<{ passed: boolean; stdin: string; expected: string; actual: string; timed_out: boolean }>
}

export default function ChallengeDetail() {
  const { id } = useParams<{ id: string }>()
  const qc = useQueryClient()
  const [code, setCode] = useState<string | undefined>(undefined)
  const [runResult, setRunResult] = useState<RunResult | null>(null)
  const [running, setRunning] = useState(false)
  const [allPassed, setAllPassed] = useState(false)
  const editorRef = useRef<unknown>(null)
  const codeInitialized = useRef(false)

  const { data, isLoading } = useQuery<DetailData>({
    queryKey: ['challenge', id],
    queryFn: () => api.get(`/challenges/${id}`),
  })

  useEffect(() => {
    if (data && !codeInitialized.current) {
      codeInitialized.current = true
      setCode(data.last_submission?.code ?? data.challenge.starter_code ?? '# Write your solution here\n')
    }
  }, [data])

  const submit = useMutation({
    mutationFn: () => api.post<{ status: string; message: string }>('/submit', { challenge_id: id, code: code ?? '' }),
    onSuccess: (r) => {
      toast.success(r.message)
      qc.invalidateQueries({ queryKey: ['challenge', id] })
      qc.invalidateQueries({ queryKey: ['challenges'] })
    },
    onError: (e: Error) => toast.error(e instanceof ApiError ? e.message : e.message),
  })

  async function handleRun() {
    setRunning(true)
    setRunResult(null)
    setAllPassed(false)
    try {
      const result = await api.post<RunResult>('/run', { code: code ?? '', challenge_id: id })
      setRunResult(result)
      if (result.mode === 'tests') setAllPassed(!!result.all_passed)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Run failed')
    } finally {
      setRunning(false)
    }
  }

  if (isLoading || !data) {
    return <div className="flex items-center justify-center min-h-[60vh]"><div className="text-neon-blue animate-pulse">🪐 Loading challenge...</div></div>
  }

  const { challenge, already_approved, active_event, last_submission } = data
  const initialCode = code ?? last_submission?.code ?? challenge.starter_code ?? '# Write your solution here\n'

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <div className="mb-6">
        <Link to="/challenges" className="text-gray-500 hover:text-gray-300 text-sm transition">← Back to Planets</Link>
      </div>

      {already_approved && (
        <div className="mb-6 bg-green-900/40 border border-green-500/50 rounded-2xl p-4 flex items-center gap-3">
          <span className="text-2xl">✅</span>
          <span className="font-bold text-green-300">You already solved this challenge!</span>
        </div>
      )}

      {last_submission?.status === 'rejected' && (
        <div className="mb-6 bg-red-900/30 border border-red-500/40 rounded-2xl p-4">
          <div className="font-bold text-red-300 mb-1">❌ Solution rejected</div>
          <div className="text-red-200/70 text-sm">{last_submission.tutor_comment}</div>
        </div>
      )}

      {active_event && active_event.multiplier > 1 && (
        <div className="mb-6 bg-yellow-900/30 border border-yellow-500/30 rounded-xl p-3 flex items-center gap-3">
          <span>⚡</span>
          <span className="text-yellow-300 text-sm font-semibold">{active_event.title} — ×{active_event.multiplier} points active!</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: problem statement */}
        <div className="space-y-4">
          <div className="glass rounded-2xl p-6 border border-white/10">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h1 className="text-2xl font-black text-white">{challenge.title}</h1>
                <p className="text-gray-400 text-sm mt-1">📍 {challenge.planet_name}</p>
              </div>
              <div className="text-right">
                <div className="text-yellow-300 font-bold">+{challenge.points} ⚡</div>
                <div className={`text-xs mt-1 px-2 py-0.5 rounded-full font-semibold inline-block ${challenge.difficulty === 'easy' ? 'bg-green-900/50 text-green-300' : challenge.difficulty === 'medium' ? 'bg-yellow-900/50 text-yellow-300' : 'bg-red-900/50 text-red-300'}`}>
                  {challenge.difficulty.toUpperCase()}
                </div>
              </div>
            </div>
            <div className="text-gray-300 leading-relaxed whitespace-pre-wrap text-sm">{challenge.description}</div>
          </div>

          {challenge.examples && (
            <div className="glass rounded-2xl p-5 border border-white/10">
              <h3 className="font-bold text-white mb-3">📋 Examples</h3>
              <pre className="text-gray-300 text-sm bg-space-700/50 rounded-lg p-3 overflow-x-auto">{challenge.examples}</pre>
            </div>
          )}

          {/* Run output */}
          {runResult && (
            <div className="glass rounded-2xl p-5 border border-white/10">
              <h3 className="font-bold text-white mb-3">🧪 Test Results</h3>
              {runResult.mode === 'tests' ? (
                <div>
                  <div className={`text-sm font-bold mb-3 ${runResult.all_passed ? 'text-green-400' : 'text-red-400'}`}>
                    {runResult.all_passed ? '✅' : '❌'} {runResult.passed}/{runResult.total} tests passed
                  </div>
                  <div className="space-y-2">
                    {runResult.results?.map((r, i) => (
                      <div key={i} className={`rounded-lg p-3 text-xs ${r.passed ? 'bg-green-900/30 border border-green-500/30' : 'bg-red-900/30 border border-red-500/30'}`}>
                        <div className="font-bold mb-1">{r.passed ? '✅' : '❌'} Test {i + 1}</div>
                        {!r.passed && (
                          <>
                            <div className="text-gray-400">Expected: <span className="text-white font-mono">{r.expected}</span></div>
                            <div className="text-gray-400">Got: <span className="text-red-300 font-mono">{r.actual || '(empty)'}</span></div>
                          </>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div>
                  {runResult.stdout && <pre className="text-green-300 text-sm font-mono bg-space-700/50 rounded p-3 mb-2 overflow-x-auto">{runResult.stdout}</pre>}
                  {runResult.stderr && <pre className="text-red-300 text-sm font-mono bg-space-700/50 rounded p-3 overflow-x-auto">{runResult.stderr}</pre>}
                  {runResult.timed_out && <div className="text-yellow-400 text-sm">⏱️ Timed out!</div>}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right: editor */}
        <div className="flex flex-col gap-4">
          <div className="monaco-container flex-1" style={{ minHeight: '400px' }}>
            <Editor
              height="450px"
              language="python"
              theme="vs-dark"
              value={initialCode}
              onChange={v => setCode(v ?? '')}
              onMount={e => { editorRef.current = e }}
              options={{ fontSize: 14, minimap: { enabled: false }, scrollBeyondLastLine: false, fontLigatures: true }}
            />
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleRun}
              disabled={running}
              className="flex-1 bg-space-600 hover:bg-space-500 border border-white/10 text-white font-bold py-3 rounded-xl transition disabled:opacity-50"
            >
              {running ? '⏳ Running...' : '▶ Run Tests'}
            </button>
            <button
              onClick={() => submit.mutate()}
              disabled={submit.isPending || (!allPassed && (challenge.test_cases?.length ?? 0) > 0) || already_approved}
              className="flex-1 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 text-white font-bold py-3 rounded-xl transition disabled:opacity-50"
            >
              {submit.isPending ? '🚀 Submitting...' : '🚀 Submit'}
            </button>
          </div>
          {!allPassed && (challenge.test_cases?.length ?? 0) > 0 && !already_approved && (
            <p className="text-center text-gray-500 text-xs">Run tests and pass all to enable submission</p>
          )}
        </div>
      </div>
    </div>
  )
}
