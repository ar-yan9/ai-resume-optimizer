from io import BytesIO
import os
import re
from collections import Counter
from typing import List

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader

app = FastAPI(title="AI Resume Optimizer API", version="1.0.0")

# Comma-separated list, e.g. CORS_ORIGINS="https://example.com,http://localhost:3000"
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by", "for",
    "from", "has", "have", "in", "into", "is", "it", "its", "of", "on", "or",
    "our", "that", "the", "their", "this", "to", "was", "were", "will", "with",
    "you", "your", "we", "they", "i", "he", "she", "using", "use", "work",
    "working", "experience", "skills", "skill", "ability", "role", "job",
    "candidate", "required", "preferred", "responsibilities", "including"
}


def extract_resume_text(filename: str, content: bytes) -> str:
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if suffix == "pdf":
        try:
            reader = PdfReader(BytesIO(content))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Could not read this PDF.") from exc
    if suffix in {"txt", "md"}:
        return content.decode("utf-8", errors="replace")
    raise HTTPException(
        status_code=400,
        detail="Unsupported file type. Please upload a PDF or TXT file."
    )


def keyword_counts(text: str) -> Counter:
    """Token frequency in source text, with the same filtering as keyword lists."""
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]{1,}", text.lower())
    return Counter(
        word for token in tokens
        if len(word := token.strip(".-")) > 1
        and word not in STOP_WORDS and not word.isdigit()
    )


def keywords(text: str) -> List[str]:
    return [word for word, _ in keyword_counts(text).most_common()]


@app.get("/")
def root():
    return {"message": "AI Resume Optimizer API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze/")
async def analyze_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):
    if not job_description.strip():
        raise HTTPException(status_code=400, detail="Please provide a job description.")

    content = await resume.read()
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded resume is empty.")
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File is too large. Maximum size is 5 MB.")

    resume_text = extract_resume_text(resume.filename or "", content)
    if not resume_text.strip():
        raise HTTPException(
            status_code=400,
            detail="No readable text was found. Try a text-based PDF or TXT file."
        )

    resume_words = set(keywords(resume_text))
    job_counts = keyword_counts(job_description)
    job_words = [word for word, _ in job_counts.most_common()]
    matched = [word for word in job_words if word in resume_words]
    missing = [word for word in job_words if word not in resume_words]

    score = round((len(matched) / len(job_words)) * 100) if job_words else 0

    total_weight = sum(job_counts.values())
    matched_weight = sum(job_counts[word] for word in matched)
    weighted_score = round(matched_weight / total_weight * 100) if total_weight else 0

    return {
        "weighted_keyword_score": weighted_score,
        "keyword_weights": dict(job_counts.most_common(50)),
        "total_job_keyword_weight": total_weight,
        "matched_keyword_weight": matched_weight,
        "weighting_note": "JD token frequency only; repetition does not prove importance. Resume repetition gives no extra credit.",
        "filename": resume.filename,
        "ats_score": score,
        "matched_keywords": matched[:50],
        "missing_keywords": missing[:50],
        "total_job_keywords": len(job_words),
        "total_matched_keywords": len(matched),
        "note": "Estimated keyword overlap only; this is not an actual ATS ranking."
    }
