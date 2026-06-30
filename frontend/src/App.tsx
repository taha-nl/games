import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { AuthProvider } from '@/context/AuthContext'
import { NavBar } from '@/components/NavBar'
import { Starfield } from '@/components/Starfield'
import { ProtectedRoute } from '@/components/ProtectedRoute'

const Login            = lazy(() => import('@/pages/Login'))
const TutorLogin       = lazy(() => import('@/pages/tutor/TutorLogin'))
const Dashboard        = lazy(() => import('@/pages/Dashboard'))
const Challenges       = lazy(() => import('@/pages/Challenges'))
const ChallengeDetail  = lazy(() => import('@/pages/ChallengeDetail'))
const Leaderboard      = lazy(() => import('@/pages/Leaderboard'))
const CardShop         = lazy(() => import('@/pages/CardShop'))
const QuizIndex        = lazy(() => import('@/pages/quiz/QuizIndex'))
const QuizQuestion     = lazy(() => import('@/pages/quiz/QuizQuestion'))
const Submissions      = lazy(() => import('@/pages/tutor/Submissions'))
const SubmissionDetail = lazy(() => import('@/pages/tutor/SubmissionDetail'))
const AdminDashboard   = lazy(() => import('@/pages/admin/AdminDashboard'))
const AdminTeams       = lazy(() => import('@/pages/admin/AdminTeams'))
const AdminChallenges  = lazy(() => import('@/pages/admin/AdminChallenges'))
const AdminTestCases   = lazy(() => import('@/pages/admin/AdminTestCases'))
const AdminEvents      = lazy(() => import('@/pages/admin/AdminEvents'))
const AdminQuiz        = lazy(() => import('@/pages/admin/AdminQuiz'))

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30_000 } },
})

function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="text-neon-blue text-xl animate-pulse">🚀 Loading...</div>
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <div className="bg-space-900 text-white min-h-screen font-space">
            <Starfield />
            <NavBar />
            <main className="relative z-10">
              <Suspense fallback={<PageLoader />}>
                <Routes>
                  <Route path="/login" element={<Login />} />
                  <Route path="/tutor/login" element={<TutorLogin />} />

                  <Route path="/dashboard" element={<ProtectedRoute require="team"><Dashboard /></ProtectedRoute>} />
                  <Route path="/challenges" element={<ProtectedRoute require="team"><Challenges /></ProtectedRoute>} />
                  <Route path="/challenge/:id" element={<ProtectedRoute require="team"><ChallengeDetail /></ProtectedRoute>} />
                  <Route path="/leaderboard" element={<Leaderboard />} />
                  <Route path="/cards/shop" element={<ProtectedRoute require="team"><CardShop /></ProtectedRoute>} />
                  <Route path="/quiz" element={<ProtectedRoute require="team"><QuizIndex /></ProtectedRoute>} />
                  <Route path="/quiz/:id" element={<ProtectedRoute require="team"><QuizQuestion /></ProtectedRoute>} />

                  <Route path="/tutor/submissions" element={<ProtectedRoute require="tutor"><Submissions /></ProtectedRoute>} />
                  <Route path="/tutor/submission/:id" element={<ProtectedRoute require="tutor"><SubmissionDetail /></ProtectedRoute>} />

                  <Route path="/admin" element={<ProtectedRoute require="admin"><AdminDashboard /></ProtectedRoute>} />
                  <Route path="/admin/teams" element={<ProtectedRoute require="admin"><AdminTeams /></ProtectedRoute>} />
                  <Route path="/admin/challenges" element={<ProtectedRoute require="admin"><AdminChallenges /></ProtectedRoute>} />
                  <Route path="/admin/challenges/:id/test-cases" element={<ProtectedRoute require="admin"><AdminTestCases /></ProtectedRoute>} />
                  <Route path="/admin/events" element={<ProtectedRoute require="admin"><AdminEvents /></ProtectedRoute>} />
                  <Route path="/admin/quiz" element={<ProtectedRoute require="admin"><AdminQuiz /></ProtectedRoute>} />

                  <Route path="/" element={<Navigate to="/dashboard" replace />} />
                  <Route path="*" element={<Navigate to="/login" replace />} />
                </Routes>
              </Suspense>
            </main>
          </div>
          <Toaster
            theme="dark"
            position="bottom-right"
            toastOptions={{
              style: { background: '#0a0e1a', border: '1px solid rgba(255,255,255,0.1)', color: 'white' },
            }}
          />
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}
