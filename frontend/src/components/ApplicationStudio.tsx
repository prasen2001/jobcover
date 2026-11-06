import { FormEvent, useMemo, useState } from 'react'
import { CheckCircle2, Clipboard, ExternalLink, Sparkles, WandSparkles } from 'lucide-react'
import { api, streamApi } from '../api'
import { Application, Resume } from '../types'

export function ApplicationStudio({ resumes }: { resumes: Resume[] }) {
  const versions = useMemo(() => resumes.flatMap((r) => r.versions.map((v) => ({ ...v, resumeName: r.name }))), [resumes])
  const [result, setResult] = useState<Application | null>(null)
  const [busy, setBusy] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')
  const [source, setSource] = useState<'text' | 'url'>('text')
  const [aiModel, setAiModel] = useState('gemini:gemini-3.8-flash')

  async function analyze(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError(''); setResult(null)
    const form = new FormData(event.currentTarget)
    try {
      const response = await api<{ application: Application }>('/applications/analyze', { method: 'POST', body: JSON.stringify(Object.fromEntries(form.entries())) })
      setResult(response.application)
    } catch (caught) { setError(caught instanceof Error ? caught.message : 'Analysis failed.') }
    finally { setBusy(false) }
  }

  async function generate() {
    if (!result) return
    setGenerating(true); setError('')
    try {
      const separator = aiModel.indexOf(':')
      const provider = aiModel.slice(0, separator)
      const model = aiModel.slice(separator + 1)
      let draft = ''
      await streamApi(`/applications/${result.id}/cover-letter/stream`, { provider, model }, (word) => {
        draft += word
        setResult((current) => current ? { ...current, coverLetter: draft } : current)
      })
    } catch (caught) {
      setResult((current) => current ? { ...current, coverLetter: '' } : current)
      setError(caught instanceof Error ? caught.message : 'Generation failed.')
    }
    finally { setGenerating(false) }
  }

  return <section className="page-section"><header className="page-header"><div><p className="eyebrow">APPLICATION STUDIO</p><h1>Tailor with intention</h1><p>Compare a resume against the actual role before writing your letter.</p></div></header>
    <div className="studio-grid"><form className="analysis-form" onSubmit={analyze}><div className="numbered-title"><span>1</span><div><h3>Choose the role</h3><p>Paste the description for the most reliable analysis.</p></div></div><div className="form-grid"><label>Company<input name="companyName" placeholder="Acme, Inc." /></label><label>Role title<input name="roleTitle" placeholder="Senior product engineer" /></label></div>
      <div className="source-tabs"><button type="button" className={source === 'text' ? 'active' : ''} onClick={() => setSource('text')}>Paste description</button><button type="button" className={source === 'url' ? 'active' : ''} onClick={() => setSource('url')}><ExternalLink size={15} /> Job link</button></div>
      {source === 'text' ? <label>Job description<textarea name="jobDescription" rows={10} required placeholder="Paste the responsibilities, qualifications, and company context here…" /></label> : <label>Job posting URL<input name="jobUrl" type="url" required placeholder="https://company.com/jobs/…" /><small>Some sites block automated reading. You can always paste the description instead.</small></label>}
      <div className="numbered-title second"><span>2</span><div><h3>Select your resume</h3><p>Each version is scored independently.</p></div></div><label>Resume version<select name="resumeVersionId" required defaultValue=""><option value="" disabled>Select a resume…</option>{versions.map((v) => <option value={v.id} key={v.id}>{v.resumeName} · v{v.versionNumber} · {v.filename}</option>)}</select></label>
      {versions.length === 0 && <p className="inline-note">Upload a resume before starting an analysis.</p>}{error && <p className="form-error">{error}</p>}<button className="primary-button" disabled={busy || versions.length === 0}><Sparkles size={18} /> {busy ? 'Reading the role…' : 'Analyze my fit'}</button>
    </form>
    <aside className={`results-panel ${result ? 'has-result' : ''}`}>{!result ? <div className="results-placeholder"><span><WandSparkles /></span><h3>Your fit report will appear here</h3><p>We’ll show keyword alignment, evidence, clarity, ATS structure, and practical next steps.</p></div> : <><div className="score-hero"><div className="score-ring" style={{ '--score': `${result.metrics.overall * 3.6}deg` } as React.CSSProperties}><span><strong>{result.metrics.overall}</strong><small>/100</small></span></div><div><p className="eyebrow">OVERALL MATCH</p><h2>{result.metrics.overall >= 80 ? 'Strong alignment' : result.metrics.overall >= 65 ? 'Promising fit' : 'Needs tailoring'}</h2><p>{result.metrics.readyForCoverLetter ? 'You have a solid foundation for a tailored letter.' : 'Make the highest-impact resume changes first.'}</p></div></div>
      <div className="dimension-list">{result.metrics.dimensions.map((d) => <div key={d.name}><span>{d.name}<strong>{d.score}</strong></span><div><i style={{ width: `${d.score}%` }} /></div></div>)}</div>
      <div className="suggestions"><h3>Suggested changes</h3>{result.metrics.suggestions.map((s) => <p key={s}><CheckCircle2 size={17} />{s}</p>)}</div>
      <div className="keyword-row"><div><small>MATCHED</small>{result.metrics.matchedKeywords.slice(0, 6).map(k => <span className="keyword good" key={k}>{k}</span>)}</div><div><small>OPPORTUNITIES</small>{result.metrics.missingKeywords.slice(0, 6).map(k => <span className="keyword" key={k}>{k}</span>)}</div></div>
      {!result.coverLetter ? <div className="generation-controls"><label>AI model<select value={aiModel} onChange={(event) => setAiModel(event.target.value)}><option value="gemini:gemini-3.8-flash">Gemini 3.8 Flash · Google</option><option value="ollama:llama3.1:8b">Llama 3.1 8B · Local on this Mac</option><option value="groq:openai/gpt-oss-120b">GPT-OSS 120B · Groq</option></select><small>Local Llama needs Ollama running; hosted models need their matching API key.</small></label><button className="primary-button" onClick={generate} disabled={generating}><WandSparkles size={18} />{generating ? 'Starting the model…' : 'Generate cover letter'}</button></div> : <div className="letter-result"><div><h3>{generating ? 'Writing your cover letter…' : 'Your cover letter'}</h3>{!generating && <button className="text-button" onClick={() => navigator.clipboard.writeText(result.coverLetter)}><Clipboard size={16} /> Copy</button>}</div>{generating ? <div className="streaming-letter" aria-live="polite">{result.coverLetter}<span className="typing-cursor" /></div> : <textarea value={result.coverLetter} onChange={(e) => setResult({ ...result, coverLetter: e.target.value })} rows={18} />}</div>}
    </>}</aside></div>
  </section>
}

