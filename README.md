# JobCover

JobCover is a full-stack application for keeping role-specific resume versions, measuring how well a resume fits a job, and generating an editable cover letter grounded in the user's real profile and resume.

The app uses a React + TypeScript frontend, a Flask API, SQLite for local development, Docling for resume parsing, and LangChain for cover-letter generation. Google Gemini 3.8 Flash is the default, with local Meta Llama 3.1 8B through Ollama and OpenAI's `gpt-oss-120b` on Groq as selectable alternatives; no Chinese model or Chinese-maintained AI library is configured.

## What is included

- Email/password sign-up and sign-in with hashed passwords and JWT access tokens
- A profile with contact details, college, separate degree and program/major fields, enrollment/graduation years, summary, and skills
- Resume categories with immutable, numbered versions and parsing notes
- PDF, DOCX, TXT, and Markdown uploads stored locally with metadata in SQLite
- Docling standard, Tesseract OCR, and IBM Granite Docling VLM modes
- Job descriptions from pasted text or a public job URL
- Explainable scores for keyword alignment, evidence/impact, clarity, ATS structure, and contact completeness
- Practical suggested changes and an explicit readiness threshold
- LangChain cover-letter generation with an editable result
- A guarded LaTeX resume builder with `.tex` paste/upload, selectable analysis suggestions, AI tailoring, and an embedded PDF preview
- A deterministic cover-letter fallback when no API key is configured
- Responsive desktop and mobile UI

## Project layout

```text
jobcover/
├── .env                    # local secrets; ignored by Git
├── .env.example            # safe template
├── backend/
│   ├── app/
│   │   ├── routes/         # auth, profile, resumes, applications
│   │   ├── services/       # parsing, scoring, fetch safety, LangChain
│   │   └── models.py
│   ├── tests/
│   ├── requirements.txt
│   └── run.py
└── frontend/
    ├── src/components/
    ├── src/api.ts
    └── vite.config.ts
```

## Local setup

Prerequisites: Python 3.11 or 3.12, Node.js 20+, npm, and Tectonic for LaTeX rendering. Tesseract is needed only for scanned resume PDFs. Python 3.12 is recommended in `backend/.python-version`.

```bash
brew install tectonic
```

1. Create the one root environment file:

   ```bash
   cp .env.example .env
   ```

   Generate strong values for `SECRET_KEY` and `JWT_SECRET_KEY`. Add a `GOOGLE_API_KEY` from Google AI Studio for Gemini, or a `GROQ_API_KEY` for the Groq alternative. Without a provider key, scoring still works and non-explicit API usage falls back to a local template.

2. Create the Python virtual environment and start Flask:

   ```bash
   python3.12 -m venv backend/.venv
   source backend/.venv/bin/activate
   python -m pip install --upgrade pip
   pip install -r backend/requirements-dev.txt
   python backend/run.py
   ```

3. In another terminal, start React:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

Open [http://localhost:5173](http://localhost:5173). Vite proxies `/api` to Flask on port 5001. Port 5001 is used by default because macOS AirPlay Receiver commonly occupies port 5000; it can be changed with `BACKEND_PORT` and the matching target in `frontend/vite.config.ts`.

## Free AI access and model policy

Create a Gemini API key in Google AI Studio and place it only in the root `.env` as `GOOGLE_API_KEY`. The default `gemini-3.8-flash` model has a Google-documented free tier. Users can also select local Meta Llama 3.1 8B or `openai/gpt-oss-120b` on Groq. The backend enforces this non-Chinese allowlist rather than accepting arbitrary model identifiers.

API keys never reach the browser. Resume content is sent only to the provider selected when the user clicks **Generate cover letter**. The deterministic score runs locally.

### Local inference with Ollama

Local Llama inference has no per-token API bill or provider request quota. It is not literally unlimited: the model has a context limit, and generation is constrained by local memory, speed, storage, and power. JobCover uses an 8K working context to keep memory predictable even though the model supports a larger maximum.

Full LaTeX resume generation uses a separate 16K context and allows up to 4,096 output tokens so the model can return the complete document. These can be adjusted with `OLLAMA_LATEX_CONTEXT_LENGTH` and `OLLAMA_LATEX_MAX_TOKENS` in the root `.env`.

```bash
brew install ollama
brew services start ollama
ollama pull llama3.1:8b
```

The quantized model download is approximately 4.9 GB. Once installed, choose **Llama 3.1 8B · Local on this Mac** in the application studio. Resume and job text then stay on the local Ollama service.

## Docling modes

Choose a mode per upload in the UI or set the default with `DOCLING_PIPELINE`:

| Mode | Best for | Notes |
| --- | --- | --- |
| `standard` | Normal digital PDF/DOCX | Fastest; OCR is off for PDFs |
| `ocr` | Scans and image-only PDFs | Uses the locally installed Tesseract CLI and `DOCLING_OCR_LANGUAGES` |
| `vlm` | Visually complex PDF layouts | Uses Docling's default IBM Granite Docling VLM; first run downloads model weights |

Tesseract installation examples:

```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr
```

The project deliberately uses Tesseract and IBM Granite Docling for OCR/VLM; it does not configure PaddleOCR, Qwen, or other Chinese-origin models/libraries.

## Testing and quality checks

```bash
source backend/.venv/bin/activate
pytest backend/tests -q

cd frontend
npm run build
npm run lint
```

The backend tests cover auth, profile persistence, ownership checks, resume versioning, and explainable analysis output.

## API overview

All routes except health and auth require `Authorization: Bearer <token>`.

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Service health |
| `POST` | `/api/auth/signup` | Create account |
| `POST` | `/api/auth/login` | Sign in |
| `GET`, `PUT` | `/api/profile` | Read/update profile |
| `GET`, `POST` | `/api/resumes` | List/create resume family |
| `POST` | `/api/resumes/:id/versions` | Add an immutable version |
| `POST` | `/api/applications/analyze` | Fetch/paste a job and score the resume |
| `POST` | `/api/applications/:id/cover-letter` | Generate a grounded letter |
| `GET` | `/api/latex/options` | Read selectable LaTeX generation guardrails |
| `POST` | `/api/latex/compile` | Safely compile pasted or uploaded `.tex` source |
| `POST` | `/api/latex/generate` | Tailor LaTeX to a job, validate it, and return the rendered PDF |

## Security and production notes

- Passwords use Werkzeug's salted password hashing; raw passwords are never stored.
- Job-link fetching resolves DNS, rejects private/local IPs, disables redirects, requires HTML, limits response processing, and has a timeout to reduce SSRF risk.
- Upload extensions and request size are restricted, and filenames are randomized on disk.
- Resume/application queries always verify the authenticated owner.
- LaTeX compilation uses an explicit package allowlist, blocks file/shell primitives and external assets, runs without shell escape in a temporary directory, has a 30-second timeout, and validates PDF size and page count.
- Resume generation treats job text and custom instructions as untrusted data. The truthfulness constraint cannot be disabled, and selected single-page/ATS constraints are checked again after generation.
- `.env`, uploaded resumes, the database, and virtual environments are ignored by Git.

Before public deployment, use PostgreSQL, add database migrations, store uploads in encrypted object storage, use short-lived tokens plus refresh-token rotation in secure HTTP-only cookies, add email verification/password reset, malware-scan uploads, add rate limiting and audit logs, and run Flask behind HTTPS with a production WSGI server.

## Data model

```text
User 1──1 Profile
User 1──* Resume 1──* ResumeVersion
User 1──* Application *──1 ResumeVersion
```

A `Resume` is a named category such as “Backend engineering.” Each upload creates a new `ResumeVersion`; existing versions are never overwritten. An `Application` freezes the job text and the resulting metrics so past decisions remain reproducible.

