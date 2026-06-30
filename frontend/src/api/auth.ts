import { api } from './client'

export interface TeamInfo {
  id: number
  name: string
  score: number
  coins: number
  is_frozen: boolean
  frozen_until: string | null
  double_points_active: boolean
}

export interface TutorInfo {
  id: number
  username: string
  role: 'tutor' | 'admin'
}

export interface MeResponse {
  team?: TeamInfo
  tutor?: TutorInfo
}

export const authApi = {
  me: () => api.get<MeResponse>('/auth/me'),
  login: (team_name: string, password: string) =>
    api.post<{ team: TeamInfo }>('/auth/login', { team_name, password }),
  logout: () => api.post('/auth/logout'),
  tutorLogin: (username: string, password: string) =>
    api.post<{ tutor: TutorInfo }>('/auth/tutor/login', { username, password }),
  tutorLogout: () => api.post('/auth/tutor/logout'),
}
