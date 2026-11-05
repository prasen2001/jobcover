import { ChangeEvent, useRef, useState } from 'react'
import { FileText, Plus, Upload, X } from 'lucide-react'
import { api } from '../api'
import { Resume } from '../types'

export function ResumeLibrary({ resumes, refresh }: { resumes: Resume[]; refresh: () => Promise<void> }) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [modal, setModal] = useState(false)
  const [target, setTarget] = useState<Resume | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function upload(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!file) return setError('Choose a resume file first.')
    const values = new FormData(event.currentTarget)
    values.set('file', file)
    setBusy(true); setError('')
    try {
      await api(target ? `/resumes/${target.id}/versions` : '/resumes', { method: 'POST', body: values })
      setModal(false); setFile(null); setTarget(null); await refresh()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Upload failed.')
    } finally { setBusy(false) }
  }

  function chooseFile(event: ChangeEvent<HTMLInputElement>) { setFile(event.target.files?.[0] || null) }
  function openUpload(resume: Resume | null = null) { setTarget(resume); setModal(true); setError(''); setFile(null) }

  return (
    <section className="page-section">
      <header className="page-header"><div><p className="eyebrow">YOUR SOURCE OF TRUTH</p><h1>Resume library</h1><p>Keep role-specific resumes together without losing the history behind them.</p></div><button className="primary-button compact" onClick={() => openUpload()}><Plus size={18} /> Add resume</button></header>
      {resumes.length === 0 ? <button className="empty-drop" onClick={() => openUpload()}><span><Upload size={24} /></span><strong>Upload your first resume</strong><small>PDF, DOCX, TXT, or Markdown · up to 10 MB</small></button> :
        <div className="resume-grid">{resumes.map((resume) => <article className="resume-card" key={resume.id}>
          <div className="file-icon"><FileText size={23} /></div>
          <div className="resume-title"><span className="tag">{resume.category}</span><h3>{resume.name}</h3><p>{resume.versions.length} version{resume.versions.length === 1 ? '' : 's'} · latest v{resume.latestVersion}</p></div>
          <div className="version-list">{resume.versions.slice(0, 3).map((version) => <div key={version.id}><span>v{version.versionNumber}</span><span><strong>{version.filename}</strong><small>{version.notes || `${version.parserMode} parsing`} · {new Date(version.createdAt).toLocaleDateString()}</small></span></div>)}</div>
          <button className="text-button" onClick={() => openUpload(resume)}><Plus size={16} /> Add new version</button>
        </article>)}</div>}
      {modal && <div className="modal-backdrop" onMouseDown={() => setModal(false)}><div className="modal-card" onMouseDown={(e) => e.stopPropagation()}><button className="modal-close" onClick={() => setModal(false)}><X /></button><p className="eyebrow">{target ? `NEW VERSION · ${target.name}` : 'NEW RESUME'}</p><h2>{target ? `Upload version ${target.latestVersion + 1}` : 'Add to your library'}</h2><form onSubmit={upload} className="stack-form">
        {!target && <><label>Resume name<input name="name" required placeholder="e.g. Product engineer resume" /></label><label>Category<input name="category" required placeholder="e.g. Software engineering" /></label></>}
        <label>Parsing mode<select name="parserMode" defaultValue="standard"><option value="standard">Standard — digital documents</option><option value="ocr">OCR — scanned documents</option><option value="vlm">VLM — complex visual layouts</option></select></label>
        <label className="file-picker" onClick={() => inputRef.current?.click()}><input ref={inputRef} hidden type="file" accept=".pdf,.docx,.txt,.md" onChange={chooseFile} /><Upload size={21} /><span>{file ? file.name : 'Choose PDF, DOCX, TXT, or MD'}</span></label>
        <label>Version note <small>(optional)</small><input name="notes" placeholder="What changed in this version?" /></label>
        {error && <p className="form-error">{error}</p>}<button className="primary-button" disabled={busy}>{busy ? 'Parsing resume…' : 'Upload & parse'}</button>
      </form></div></div>}
    </section>
  )
}

