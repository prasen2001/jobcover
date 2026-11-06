import { ChangeEvent, useEffect, useMemo, useState } from 'react'
import { CheckCircle2, Code2, Download, FileUp, RefreshCw, ShieldCheck, Sparkles } from 'lucide-react'
import { api } from '../api'
import { Application } from '../types'

type Guardrail = { id: string; label: string; description: string; required: boolean }
type RenderedResume = { latexCode: string; pdfBase64: string; pageCount: number }

const FALLBACK_GUARDRAILS: Guardrail[] = [
  { id: 'single_page', label: 'Single Page', description: 'Keep the final resume to exactly one page without shrinking text below 9.5pt.', required: false },
  { id: 'ats_safe', label: 'ATS Safe', description: 'Use a simple single-column structure without graphics or positioned text.', required: false },
  { id: 'preserve_facts', label: 'Preserve Facts', description: 'Never invent candidate history, dates, skills, education, or metrics.', required: true },
  { id: 'no_photos', label: 'No Photos', description: 'Exclude photos, logos, and external assets.', required: false },
  { id: 'concise_bullets', label: 'Concise Bullets', description: 'Favor direct accomplishment bullets supported by the source.', required: false },
  { id: 'job_relevance', label: 'Job Relevance', description: 'Prioritize truthful evidence related to the target job.', required: false },
]

export function LatexResumeBuilder() {
  const [latexCode, setLatexCode] = useState('')
  const [rendered, setRendered] = useState<RenderedResume | null>(null)
  const [applications, setApplications] = useState<Application[]>([])
  const [applicationId, setApplicationId] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [guardrailOptions, setGuardrailOptions] = useState<Guardrail[]>(FALLBACK_GUARDRAILS)
  const [guardrails, setGuardrails] = useState<string[]>(FALLBACK_GUARDRAILS.map((item) => item.id))
  const [selectedSuggestions, setSelectedSuggestions] = useState<string[]>([])
  const [instructions, setInstructions] = useState('')
  const [aiModel, setAiModel] = useState('ollama:llama3.1:8b')
  const [busy, setBusy] = useState<'compile' | 'generate' | ''>('')
  const [error, setError] = useState('')

  useEffect(() => {
    void Promise.all([
      api<{ applications: Application[] }>('/applications'),
      api<{ guardrails: Guardrail[]; defaultGuardrails: string[] }>('/latex/options'),
    ]).then(([applicationResponse, optionResponse]) => {
      setApplications(applicationResponse.applications)
      setGuardrailOptions(optionResponse.guardrails)
      setGuardrails(optionResponse.defaultGuardrails)
    }).catch(() => undefined)
  }, [])

  const selectedApplication = useMemo(
    () => applications.find((item) => String(item.id) === applicationId),
    [applications, applicationId],
  )
  const pdfUrl = useMemo(() => {
    if (!rendered?.pdfBase64) return ''
    const binary = atob(rendered.pdfBase64)
    const bytes = Uint8Array.from(binary, (character) => character.charCodeAt(0))
    return URL.createObjectURL(new Blob([bytes], { type: 'application/pdf' }))
  }, [rendered])
  useEffect(() => () => { if (pdfUrl) URL.revokeObjectURL(pdfUrl) }, [pdfUrl])

  function chooseApplication(value: string) {
    setApplicationId(value)
    const application = applications.find((item) => String(item.id) === value)
    if (application) {
      setJobDescription(application.jobDescription)
      setSelectedSuggestions(application.metrics.suggestions)
    } else {
      setSelectedSuggestions([])
    }
  }

  function uploadTex(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.tex')) {
      setError('Choose a UTF-8 .tex file.')
      return
    }
    const reader = new FileReader()
    reader.onload = () => { setLatexCode(String(reader.result || '')); setRendered(null); setError('') }
    reader.onerror = () => setError('The .tex file could not be read.')
    reader.readAsText(file)
  }

  async function compile() {
    setBusy('compile'); setError('')
    try {
      const response = await api<RenderedResume>('/latex/compile', { method: 'POST', body: JSON.stringify({ latexCode }) })
      setRendered(response)
    } catch (caught) { setError(caught instanceof Error ? caught.message : 'LaTeX rendering failed.') }
    finally { setBusy('') }
  }

  async function generate() {
    setBusy('generate'); setError('')
    try {
      const separator = aiModel.indexOf(':')
      const response = await api<RenderedResume>('/latex/generate', {
        method: 'POST',
        body: JSON.stringify({
          latexCode,
          applicationId: applicationId || null,
          jobDescription,
          selectedSuggestions,
          guardrails,
          additionalInstructions: instructions,
          provider: aiModel.slice(0, separator),
          model: aiModel.slice(separator + 1),
        }),
      })
      setLatexCode(response.latexCode)
      setRendered(response)
    } catch (caught) { setError(caught instanceof Error ? caught.message : 'Resume generation failed.') }
    finally { setBusy('') }
  }

  function toggleGuardrail(id: string, required: boolean) {
    if (required) return
    setGuardrails((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id])
  }

  function toggleSuggestion(suggestion: string) {
    setSelectedSuggestions((current) => current.includes(suggestion)
      ? current.filter((item) => item !== suggestion)
      : [...current, suggestion])
  }

  function download(content: BlobPart, filename: string, type: string) {
    const url = URL.createObjectURL(new Blob([content], { type }))
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = filename; anchor.click()
    URL.revokeObjectURL(url)
  }

  return <section className="page-section latex-builder">
    <header className="page-header"><div><p className="eyebrow">LATEX RESUME BUILDER</p><h1>Write once. Tailor with guardrails.</h1><p>Render existing LaTeX or create a job-specific version without inventing candidate facts.</p></div></header>
    <div className="latex-workspace">
      <div className="latex-controls">
        <article className="builder-card"><div className="builder-heading"><span>1</span><div><h3>Source resume</h3><p>Paste a complete standalone article document or upload UTF-8 LaTeX.</p></div></div>
          <label className="tex-upload"><FileUp size={17} /> Upload .tex<input type="file" accept=".tex,text/x-tex" onChange={uploadTex} /></label>
          <label>LaTeX code<textarea className="code-editor" value={latexCode} onChange={(event) => { setLatexCode(event.target.value); setRendered(null) }} rows={20} spellCheck={false} placeholder={'\\documentclass[10pt]{article}\n...\n\\begin{document}\n...\n\\end{document}'} /></label>
          <button className="secondary-button" onClick={compile} disabled={Boolean(busy) || !latexCode.trim()}><Code2 size={17} />{busy === 'compile' ? 'Compiling safely…' : 'Render current LaTeX'}</button>
        </article>

        <article className="builder-card"><div className="builder-heading"><span>2</span><div><h3>Target job and suggestions</h3><p>Select a prior analysis or paste a description directly.</p></div></div>
          <label>Analyzed application<select value={applicationId} onChange={(event) => chooseApplication(event.target.value)}><option value="">Paste a job description manually</option>{applications.map((item) => <option key={item.id} value={item.id}>{item.companyName || 'Unnamed company'} · {item.roleTitle || 'Untitled role'}</option>)}</select></label>
          <label>Job description<textarea rows={8} value={jobDescription} onChange={(event) => { setJobDescription(event.target.value); if (applicationId) { setApplicationId(''); setSelectedSuggestions([]) } }} placeholder="Paste at least 100 characters…" /></label>
          {selectedApplication && <div className="suggestion-picker"><small>SELECT SUGGESTIONS TO APPLY</small>{selectedApplication.metrics.suggestions.map((suggestion) => <label key={suggestion}><input type="checkbox" checked={selectedSuggestions.includes(suggestion)} onChange={() => toggleSuggestion(suggestion)} /><span><CheckCircle2 size={15} />{suggestion}</span></label>)}</div>}
        </article>

        <article className="builder-card"><div className="builder-heading"><span>3</span><div><h3>Generation constraints</h3><p>Safety and truthfulness checks are enforced again on the server.</p></div></div>
          <div className="guardrail-grid">{guardrailOptions.map((item) => <label className={guardrails.includes(item.id) ? 'selected' : ''} key={item.id}><input type="checkbox" checked={guardrails.includes(item.id)} disabled={item.required} onChange={() => toggleGuardrail(item.id, item.required)} /><ShieldCheck size={17} /><span><strong>{item.label}{item.required ? ' · required' : ''}</strong><small>{item.description}</small></span></label>)}</div>
          <label>Additional instructions<textarea rows={4} maxLength={2000} value={instructions} onChange={(event) => setInstructions(event.target.value)} placeholder="Example: Emphasize backend work, keep the education section, and use concise action verbs. Instructions cannot override safety or truthfulness." /></label>
          <label>AI model<select value={aiModel} onChange={(event) => setAiModel(event.target.value)}><option value="ollama:llama3.1:8b">Llama 3.1 8B · Local on this Mac</option><option value="gemini:gemini-3.8-flash">Gemini 3.8 Flash · Google</option><option value="groq:openai/gpt-oss-120b">GPT-OSS 120B · Groq</option></select></label>
          {error && <p className="form-error">{error}</p>}
          <button className="primary-button" onClick={generate} disabled={Boolean(busy) || !latexCode.trim() || jobDescription.trim().length < 100}><Sparkles size={18} />{busy === 'generate' ? 'Generating, checking, and rendering…' : 'Generate tailored resume'}</button>
        </article>
      </div>

      <aside className="pdf-preview builder-card"><div className="preview-heading"><div><p className="eyebrow">LIVE OUTPUT</p><h2>{rendered ? `${rendered.pageCount} page${rendered.pageCount === 1 ? '' : 's'}` : 'PDF preview'}</h2></div>{rendered && <div><button className="text-button" onClick={() => download(rendered.latexCode, 'tailored-resume.tex', 'text/x-tex')}><Download size={15} /> .tex</button><button className="text-button" onClick={() => download(Uint8Array.from(atob(rendered.pdfBase64), (character) => character.charCodeAt(0)), 'tailored-resume.pdf', 'application/pdf')}><Download size={15} /> PDF</button></div>}</div>
        {pdfUrl ? <object data={pdfUrl} type="application/pdf" aria-label="Rendered resume PDF"><a href={pdfUrl} target="_blank" rel="noreferrer">Open the rendered PDF</a></object> : <div className="preview-empty"><RefreshCw size={30} /><h3>No rendered resume yet</h3><p>Render the source or generate a tailored version. Unsafe LaTeX and page-limit violations are rejected before display.</p></div>}
      </aside>
    </div>
  </section>
}
