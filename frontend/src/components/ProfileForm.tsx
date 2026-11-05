import { FormEvent, useEffect, useState } from 'react'
import { Check, Save } from 'lucide-react'
import { api } from '../api'
import { Profile } from '../types'

export function ProfileForm({ profile, onSaved }: { profile: Profile | null; onSaved: (profile: Profile) => void }) {
  const [busy, setBusy] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')
  useEffect(() => setSaved(false), [profile])
  if (!profile) return <div className="loading">Loading profile…</div>

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError('')
    const form = new FormData(event.currentTarget)
    const body = Object.fromEntries(form.entries())
    try {
      const result = await api<{ profile: Profile }>('/profile', { method: 'PUT', body: JSON.stringify(body) })
      onSaved(result.profile); setSaved(true); setTimeout(() => setSaved(false), 2400)
    } catch (caught) { setError(caught instanceof Error ? caught.message : 'Could not save profile.') }
    finally { setBusy(false) }
  }

  return <section className="page-section"><header className="page-header"><div><p className="eyebrow">YOUR STORY, ONCE</p><h1>Profile</h1><p>This information helps every letter feel complete and personal.</p></div></header>
    <form onSubmit={submit} className="profile-form">
      <div className="form-section"><h3>Personal details</h3><p>How employers can identify and reach you.</p><div className="form-grid"><label>Full name<input name="fullName" defaultValue={profile.fullName} /></label><label>Email<input value={profile.email} disabled /></label><label>Phone<input name="phone" defaultValue={profile.phone} /></label><label>Location<input name="location" defaultValue={profile.location} /></label><label>LinkedIn URL<input name="linkedinUrl" type="url" defaultValue={profile.linkedinUrl} /></label><label>Portfolio URL<input name="portfolioUrl" type="url" defaultValue={profile.portfolioUrl} /></label></div></div>
      <div className="form-section"><h3>Education</h3><p>Add your current or most relevant program.</p><div className="form-grid"><label>College / university<input name="collegeName" defaultValue={profile.collegeName} /></label><label>Degree / program<input name="degreeName" defaultValue={profile.degreeName} /></label><label>Enrollment year<input name="enrollmentYear" type="number" min="1950" max="2100" defaultValue={profile.enrollmentYear || ''} /></label><label>Graduation year<input name="graduationYear" type="number" min="1950" max="2100" defaultValue={profile.graduationYear || ''} /></label></div></div>
      <div className="form-section"><h3>Professional voice</h3><p>Give the AI accurate context. It will not invent facts beyond these details and your resume.</p><div className="form-grid full"><label>Professional summary<textarea name="professionalSummary" rows={4} defaultValue={profile.professionalSummary} placeholder="A concise overview of what you do and the impact you create…" /></label><label>Skills<textarea name="skills" rows={3} defaultValue={profile.skills} placeholder="Python, product strategy, customer research…" /></label></div></div>
      {error && <p className="form-error">{error}</p>}<div className="form-actions"><button className="primary-button compact" disabled={busy}>{saved ? <><Check size={18} /> Saved</> : <><Save size={18} /> {busy ? 'Saving…' : 'Save profile'}</>}</button></div>
    </form>
  </section>
}

