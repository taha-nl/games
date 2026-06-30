import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { api, ApiError } from '@/api/client'

interface TestCase { id: number; stdin: string; expected_output: string; is_hidden: boolean }

export default function AdminTestCases() {
  const { id } = useParams<{ id: string }>()
  const qc = useQueryClient()
  const [stdin, setStdin] = useState('')
  const [expected, setExpected] = useState('')
  const [isHidden, setIsHidden] = useState(false)

  const { data } = useQuery<{ challenge: { title: string }; test_cases: TestCase[] }>({
    queryKey: ['admin-test-cases', id],
    queryFn: () => api.get(`/admin/challenges/${id}/test-cases`),
  })

  const add = useMutation({
    mutationFn: () => api.post(`/admin/challenges/${id}/test-cases`, { stdin, expected_output: expected, is_hidden: isHidden }),
    onSuccess: () => { toast.success('Test case added!'); setStdin(''); setExpected(''); qc.invalidateQueries({ queryKey: ['admin-test-cases', id] }) },
    onError: (e: Error) => toast.error(e instanceof ApiError ? e.message : e.message),
  })

  const del = useMutation({
    mutationFn: (tcId: number) => api.delete(`/admin/challenges/${id}/test-cases/${tcId}`),
    onSuccess: () => { toast.success('Deleted.'); qc.invalidateQueries({ queryKey: ['admin-test-cases', id] }) },
  })

  const inputClass = 'w-full bg-space-700 border border-white/10 rounded-xl px-3 py-2 text-white text-sm focus:outline-none font-mono'

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <div className="mb-6">
        <Link to="/admin/challenges" className="text-gray-500 hover:text-gray-300 text-sm transition">← Back to Challenges</Link>
      </div>
      <h1 className="text-3xl font-black text-white mb-2">🧪 Test Cases</h1>
      {data && <p className="text-gray-400 mb-6">{data.challenge.title}</p>}

      {/* Add form */}
      <div className="glass rounded-2xl p-6 border border-white/10 mb-6">
        <h2 className="font-bold text-white mb-4">➕ Add Test Case</h2>
        <div className="grid grid-cols-2 gap-4 mb-3">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Input (stdin / test driver code)</label>
            <textarea value={stdin} onChange={e => setStdin(e.target.value)} rows={5} placeholder="print(solution(...))" className={`${inputClass} resize-none`} />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Expected Output</label>
            <textarea value={expected} onChange={e => setExpected(e.target.value)} rows={5} placeholder="Expected stdout" className={`${inputClass} resize-none`} />
          </div>
        </div>
        <div className="flex items-center justify-between">
          <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
            <input type="checkbox" checked={isHidden} onChange={e => setIsHidden(e.target.checked)} className="w-4 h-4" />
            Hidden test case
          </label>
          <button onClick={() => add.mutate()} disabled={!stdin || !expected || add.isPending}
            className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl text-sm transition disabled:opacity-50">
            Add Test Case
          </button>
        </div>
      </div>

      {/* Test cases list */}
      <div className="space-y-3">
        {data?.test_cases.map((tc, i) => (
          <div key={tc.id} className="glass rounded-xl p-4 border border-white/10">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-bold text-white">Test {i + 1} {tc.is_hidden && <span className="text-xs text-gray-400 ml-2">🔒 hidden</span>}</span>
              <button onClick={() => { if (confirm('Delete?')) del.mutate(tc.id) }} className="text-red-400 hover:text-red-300 text-sm transition">Delete</button>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <div className="text-xs text-gray-400 mb-1">Input</div>
                <pre className="bg-space-700/50 rounded-lg p-2 text-xs text-gray-300 overflow-x-auto">{tc.stdin || '(none)'}</pre>
              </div>
              <div>
                <div className="text-xs text-gray-400 mb-1">Expected</div>
                <pre className="bg-space-700/50 rounded-lg p-2 text-xs text-green-300 overflow-x-auto">{tc.expected_output}</pre>
              </div>
            </div>
          </div>
        ))}
        {!data?.test_cases.length && <div className="text-center py-8 text-gray-500">No test cases yet.</div>}
      </div>
    </div>
  )
}
