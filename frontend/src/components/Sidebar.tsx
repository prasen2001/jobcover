import { CodeXml, FileStack, LayoutDashboard, LogOut, PenLine, UserRound } from 'lucide-react'
import { User } from '../types'
import { Logo } from './Logo'

export type View = 'home' | 'resumes' | 'application' | 'latex' | 'profile'

export function Sidebar({ view, setView, user, onLogout }: { view: View; setView: (view: View) => void; user: User; onLogout: () => void }) {
  const links: { id: View; label: string; icon: typeof LayoutDashboard }[] = [
    { id: 'home', label: 'Overview', icon: LayoutDashboard },
    { id: 'resumes', label: 'My resumes', icon: FileStack },
    { id: 'application', label: 'New application', icon: PenLine },
    { id: 'latex', label: 'LaTeX builder', icon: CodeXml },
    { id: 'profile', label: 'Profile', icon: UserRound },
  ]
  return (
    <aside className="sidebar">
      <Logo />
      <nav>{links.map((link) => <button key={link.id} className={view === link.id ? 'active' : ''} onClick={() => setView(link.id)}><link.icon size={19} />{link.label}</button>)}</nav>
      <div className="sidebar-user">
        <span className="avatar">{(user.fullName || user.email)[0].toUpperCase()}</span>
        <span><strong>{user.fullName || 'Your profile'}</strong><small>{user.email}</small></span>
        <button aria-label="Log out" onClick={onLogout}><LogOut size={17} /></button>
      </div>
    </aside>
  )
}

