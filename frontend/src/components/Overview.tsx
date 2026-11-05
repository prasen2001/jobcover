import { ArrowRight, FileStack, PenLine, UserRound } from 'lucide-react'
import { Profile, Resume } from '../types'
import { View } from './Sidebar'

export function Overview({ name, resumes, profile, setView }: { name: string; resumes: Resume[]; profile: Profile | null; setView: (v: View) => void }) {
  const profileFields = profile ? [profile.fullName, profile.phone, profile.collegeName, profile.degreeName, profile.programName, profile.professionalSummary, profile.skills] : []
  const completeness = Math.round(100 * profileFields.filter(Boolean).length / Math.max(profileFields.length, 1))
  return <section className="page-section overview"><header className="welcome"><p className="eyebrow">GOOD TO SEE YOU</p><h1>Ready for the next one, {name.split(' ')[0] || 'there'}?</h1><p>Build a strong application one deliberate step at a time.</p></header>
    <button className="hero-action" onClick={() => setView('application')}><div><span className="spark-badge"><PenLine /></span><p className="eyebrow">START HERE</p><h2>Analyze a new job</h2><p>Match a resume, find the gaps, and create your letter.</p></div><span className="round-arrow"><ArrowRight /></span></button>
    <div className="overview-grid"><article><span className="icon-tile"><FileStack /></span><div><small>RESUME LIBRARY</small><h3>{resumes.length} tailored resume{resumes.length === 1 ? '' : 's'}</h3><p>{resumes.reduce((sum, resume) => sum + resume.versions.length, 0)} saved versions</p></div><button className="text-button" onClick={() => setView('resumes')}>Manage <ArrowRight size={15} /></button></article>
      <article><span className="icon-tile coral"><UserRound /></span><div><small>PROFILE STRENGTH</small><h3>{completeness}% complete</h3><div className="profile-progress"><i style={{ width: `${completeness}%` }} /></div></div><button className="text-button" onClick={() => setView('profile')}>Complete <ArrowRight size={15} /></button></article></div>
    <div className="how-it-works"><p className="eyebrow">A BETTER APPLICATION IN THREE STEPS</p><div><span><strong>01</strong><h3>Choose your resume</h3><p>Pick the version closest to the role.</p></span><span><strong>02</strong><h3>Understand the match</h3><p>See strengths and honest gaps.</p></span><span><strong>03</strong><h3>Write with context</h3><p>Generate, edit, and make it yours.</p></span></div></div>
  </section>
}

