import re
from collections import Counter

STOP_WORDS = {
    "and", "the", "with", "for", "that", "this", "from", "your", "you", "our", "are",
    "will", "have", "has", "job", "role", "work", "team", "years", "using", "about", "who",
    "but", "not", "all", "can", "into", "their", "they", "we", "a", "an", "to", "of", "in",
    "on", "is", "as", "be", "or", "at", "by", "it",
}


def analyze_resume(resume_text: str, job_text: str) -> dict:
    resume_lower = resume_text.lower()
    job_keywords = _keywords(job_text)
    matched = [keyword for keyword in job_keywords if keyword in resume_lower]
    missing = [keyword for keyword in job_keywords if keyword not in resume_lower]
    keyword_score = round(100 * len(matched) / max(len(job_keywords), 1))
    impact_terms = len(re.findall(r"\b(increased|reduced|improved|grew|saved|led|built|delivered|launched)\b", resume_lower))
    numbers = len(re.findall(r"\b\d+(?:\.\d+)?%?\b", resume_text))
    impact_score = min(100, 30 + impact_terms * 8 + numbers * 5)
    length = len(resume_text.split())
    clarity_score = 90 if 300 <= length <= 900 else max(45, 90 - abs(length - 600) // 12)
    sections = sum(label in resume_lower for label in ("experience", "education", "skills", "project"))
    structure_score = min(100, 35 + sections * 15)
    contact_score = 40 + (20 if "@" in resume_text else 0) + (20 if re.search(r"linkedin\.com", resume_lower) else 0) + (20 if re.search(r"\+?\d[\d\s().-]{7,}", resume_text) else 0)
    overall = round(keyword_score * .45 + impact_score * .2 + clarity_score * .15 + structure_score * .1 + contact_score * .1)
    suggestions = []
    if missing:
        suggestions.append(f"Add evidence for relevant terms where truthful: {', '.join(missing[:8])}.")
    if impact_score < 70:
        suggestions.append("Quantify achievements with scope, percentages, time saved, or business outcomes.")
    if structure_score < 80:
        suggestions.append("Use clear Experience, Education, Skills, and Projects headings for ATS readability.")
    if clarity_score < 75:
        suggestions.append("Keep the resume focused and concise; target roughly one to two pages.")
    if not suggestions:
        suggestions.append("The resume is well aligned. Proofread it and tailor the opening summary to this role.")
    return {
        "overall": max(0, min(100, overall)),
        "dimensions": [
            {"name": "Keyword alignment", "score": keyword_score},
            {"name": "Evidence & impact", "score": impact_score},
            {"name": "Clarity", "score": clarity_score},
            {"name": "ATS structure", "score": structure_score},
            {"name": "Contact completeness", "score": contact_score},
        ],
        "matchedKeywords": matched[:12],
        "missingKeywords": missing[:12],
        "suggestions": suggestions,
        "readyForCoverLetter": overall >= 70,
    }


def _keywords(text: str) -> list[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z+#.-]{2,}", text.lower())
    counts = Counter(word.strip(".-") for word in words if word not in STOP_WORDS)
    return [word for word, _count in counts.most_common(30)]

