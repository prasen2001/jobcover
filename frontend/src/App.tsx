import { useCallback, useEffect, useState } from 'react'
import { api } from './api'
import { ApplicationStudio } from './components/ApplicationStudio'
import { AuthScreen } from './components/AuthScreen'
import { Overview } from './components/Overview'
import { ProfileForm } from './components/ProfileForm'
import { ResumeLibrary } from './components/ResumeLibrary'
import { Sidebar, View } from './components/Sidebar'
import { Profile, Resume, User } from './types'

export default function App() {
  const [user, setUser] = useState<User | null>(null)
  const [profile, setProfile] = useState<Profile | null>(null)
  const [resumes, setResumes] = useState<Resume[]>([])
  const [view, setView] = useState<View>('home')
  const [loading, setLoading] = useState(Boolean(localStorage.getItem('jobcover_token')))

  const refreshResumes = useCallback(async () => {
    const response = await api<{ resumes: Resume[] }>('/resumes')
    setResumes(response.resumes)
  }, [])

  const loadWorkspace = useCallback(async () => {
    try {
      const [me, profileResponse, resumeResponse] = await Promise.all([
        api<{ user: User }>('/auth/me'), api<{ profile: Profile }>('/profile'), api<{ resumes: Resume[] }>('/resumes'),
      ])
      setUser(me.user); setProfile(profileResponse.profile); setResumes(resumeResponse.resumes)
    } catch {
      localStorage.removeItem('jobcover_token'); setUser(null)
    } finally { setLoading(false) }
  }, [])

  useEffect(() => { if (localStorage.getItem('jobcover_token')) void loadWorkspace() }, [loadWorkspace])

  function authenticate(token: string, nextUser: User) {
    localStorage.setItem('jobcover_token', token); setUser(nextUser); setLoading(true); void loadWorkspace()
  }
  function logout() { localStorage.removeItem('jobcover_token'); setUser(null); setProfile(null); setResumes([]); setView('home') }

  if (loading) return <div className="app-loading"><span>J</span><p>Opening your workspace…</p></div>
  if (!user) return <AuthScreen onAuthenticated={authenticate} />

  return <div className="app-shell"><Sidebar view={view} setView={setView} user={user} onLogout={logout} /><main className="workspace">
    {view === 'home' && <Overview name={user.fullName} resumes={resumes} profile={profile} setView={setView} />}
    {view === 'resumes' && <ResumeLibrary resumes={resumes} refresh={refreshResumes} />}
    {view === 'application' && <ApplicationStudio resumes={resumes} />}
    {view === 'profile' && <ProfileForm profile={profile} onSaved={(next) => { setProfile(next); setUser({ ...user, fullName: next.fullName }) }} />}
  </main></div>
}

