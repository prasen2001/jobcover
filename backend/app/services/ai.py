import os
from datetime import date

ALLOWED_MODELS = {
    "gemini": {"gemini-3.8-flash"},
    "groq": {"openai/gpt-oss-120b"},
}


def generate_cover_letter(
    profile: dict,
    resume_text: str,
    job_text: str,
    company: str,
    role: str,
    metrics: dict,
    provider: str | None = None,
    model_name: str | None = None,
) -> str:
    explicit_provider = provider is not None
    provider = (provider or os.getenv("AI_PROVIDER", "gemini")).strip().lower()
    if provider not in ALLOWED_MODELS:
        raise ValueError("AI provider must be gemini or groq.")

    default_model = "gemini-3.8-flash" if provider == "gemini" else "openai/gpt-oss-120b"
    env_model = os.getenv("GEMINI_MODEL" if provider == "gemini" else "GROQ_MODEL", default_model)
    model_name = (model_name or env_model).strip()
    if model_name not in ALLOWED_MODELS[provider]:
        raise ValueError(f"Model {model_name!r} is not allowed for {provider}.")

    key_name = "GOOGLE_API_KEY" if provider == "gemini" else "GROQ_API_KEY"
    api_key = os.getenv(key_name, "").strip()
    if not api_key:
        if explicit_provider:
            raise ValueError(f"{key_name} is not configured in the root .env file.")
        return _fallback_letter(profile, company, role, metrics)

    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert career writer. Write a truthful, specific, concise cover letter of 300-400 words. Never invent experience. Do not use placeholders. Return only the letter."),
        ("human", "Candidate profile:\n{profile}\n\nResume:\n{resume}\n\nJob description:\n{job}\n\nCompany: {company}\nRole: {role}\nResume analysis: {metrics}"),
    ])
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        model = ChatGoogleGenerativeAI(
            google_api_key=api_key,
            model=model_name,
            temperature=0.35,
            max_retries=2,
        )
    else:
        from langchain_groq import ChatGroq

        model = ChatGroq(
            api_key=api_key,
            model=model_name,
            temperature=0.35,
            max_retries=2,
        )
    chain = prompt | model | StrOutputParser()
    return chain.invoke({
        "profile": profile,
        "resume": resume_text[:30_000],
        "job": job_text[:30_000],
        "company": company or "the hiring organization",
        "role": role or "this opportunity",
        "metrics": metrics,
    }).strip()


def _fallback_letter(profile, company, role, metrics):
    name = profile.get("fullName") or "Applicant"
    skills = profile.get("skills") or "my relevant technical and collaborative skills"
    summary = profile.get("professionalSummary") or "my experience and commitment to delivering thoughtful, high-quality work"
    matched = ", ".join(metrics.get("matchedKeywords", [])[:4]) or "the role's core requirements"
    return f"""{date.today().strftime('%B %d, %Y')}

Dear Hiring Team,

I am writing to apply for the {role or 'open position'} at {company or 'your organization'}. I am drawn to this opportunity because it closely connects with {summary.rstrip('.')}.

My background includes {skills}. In reviewing the position, I was especially interested in its focus on {matched}. These priorities align with the work represented in my resume and with the way I approach new challenges: understand the goal, collaborate clearly, and deliver measurable results.

I would welcome the opportunity to bring this experience to {company or 'your team'} and contribute from the outset. Thank you for considering my application. I look forward to the possibility of discussing how my background can support your goals.

Sincerely,
{name}"""

