import { FormEvent, useState } from 'react'
import { ArrowRight, Check, Eye, EyeOff, Sparkles } from 'lucide-react'
import { api } from '../api'
import { User } from '../types'
import { Logo } from './Logo'

export function AuthScreen({ onAuthenticated }: { onAuthenticated: (token: string, user: User) => void }) {
  const [mode, setMode] = useState<'signup' | 'login'>('signup')
  const [showPassword, setShowPassword] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true)
    setError('')
    const form = new FormData(event.currentTarget)
    try {
      const result = await api<{ accessToken: string; user: User }>(`/auth/${mode}`, {
        method: 'POST',
        body: JSON.stringify({
          fullName: form.get('fullName'),
          email: form.get('email'),
          password: form.get('password'),
        }),
      })
      onAuthenticated(result.accessToken, result.user)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to continue.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-story">
        <Logo />
        <div className="story-copy">
          <p className="eyebrow"><Sparkles size={15} /> Your application co-pilot</p>
          <h1>Turn your experience into a story worth reading.</h1>
          <p className="lede">Keep every resume version in one place, see how it fits the role, and write a cover letter that still sounds like you.</p>
          <div className="benefit-list">
            <span><Check size={16} /> Private, versioned resume library</span>
            <span><Check size={16} /> Clear, explainable fit scores</span>
            <span><Check size={16} /> Tailored letters in minutes</span>
          </div>
        </div>
        <p className="story-footnote">Built to support your judgment — never replace it.</p>
      </section>
      <section className="auth-panel">
        <div className="auth-card">
          <div className="auth-heading auth-transition" key={`heading-${mode}`}>
            <p className="step-label">{mode === 'signup' ? 'START YOUR WORKSPACE' : 'WELCOME BACK'}</p>
            <h2>{mode === 'signup' ? 'Create your account' : 'Sign in to JobCover'}</h2>
            <p>{mode === 'signup' ? 'Your next application starts here.' : 'Pick up where you left off.'}</p>
          </div>
          <div className={`mode-toggle ${mode}`}>
            <button className={mode === 'signup' ? 'active' : ''} onClick={() => setMode('signup')}>Sign up</button>
            <button className={mode === 'login' ? 'active' : ''} onClick={() => setMode('login')}>Sign in</button>
          </div>
          <form onSubmit={submit} className="stack-form">
            <div className={`signup-field ${mode === 'signup' ? 'visible' : ''}`} aria-hidden={mode !== 'signup'}>
              <label>Full name<input name="fullName" required={mode === 'signup'} disabled={mode !== 'signup'} autoComplete="name" placeholder="Alex Morgan" /></label>
            </div>
            <label>Email address<input name="email" type="email" required autoComplete="email" placeholder="alex@example.com" /></label>
            <label>Password<div className="password-field"><input name="password" type={showPassword ? 'text' : 'password'} minLength={8} required autoComplete={mode === 'signup' ? 'new-password' : 'current-password'} placeholder="At least 8 characters" /><button type="button" aria-label="Show password" onClick={() => setShowPassword(!showPassword)}>{showPassword ? <EyeOff size={18} /> : <Eye size={18} />}</button></div></label>
            {error && <p className="form-error" role="alert">{error}</p>}
            <button className="primary-button" disabled={busy}><span className="auth-transition" key={`submit-${mode}`}>{busy ? 'One moment…' : mode === 'signup' ? 'Create account' : 'Sign in'}</span> <ArrowRight size={18} /></button>
          </form>
          <p className="terms">By continuing, you agree to protect the personal data you upload.</p>
        </div>
      </section>
    </main>
  )
}

