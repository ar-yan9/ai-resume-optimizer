# AI Resume Optimizer

A beginner-friendly React + FastAPI application that compares a resume with a job description and reports an estimated keyword-match score.

## Features
- Upload a PDF or TXT resume
- Paste a job description
- View an estimated keyword match score
- View matched and missing keywords
- React frontend and FastAPI REST backend

> Status: the backend tests pass and the frontend builds. The full flow (upload, analyze, results) was checked against a running backend with the API.

> This is a newly written starter implementation, not a recovered copy of any previous source code. The score is a simple keyword-overlap estimate, not a validated ATS score.

## JD-frequency weighting (API)
The backend now returns an additional `weighted_keyword_score`. Each filtered job-description token gets a weight equal to its frequency in the JD. For example, JD `Python Python Python React` and resume `Python` gives 75% weighted coverage and 50% unique-keyword overlap.

The existing `ats_score` field and frontend display keep the original unique-keyword overlap, so existing callers are unchanged. The weighted score is currently available through the API only, not displayed in the UI. Repeated resume words give no extra credit. Repetition in a JD is a crude proxy, not evidence that a skill is essential, and neither score predicts hiring or a real ATS ranking.

Responses also include `keyword_weights` (top 50 terms), `total_job_keyword_weight` and `matched_keyword_weight`. Totals and scores include every filtered JD term, even when displayed lists are capped. Tokens remain case-insensitive single words, without semantic matching or synonym detection.

Backend tests include frequency weighting, boundaries and synthetic readable/empty-text PDF fixtures. No personal resume data is used in tests.

## Requirements
- Python 3.10+
- Node.js 18+

## Run the backend
```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Run the frontend
Open a second terminal:
```bash
cd frontend
npm install
npm start
```
The React app runs on http://localhost:3000 and calls the API at http://localhost:8000.

## Configuration
- `REACT_APP_API_URL` (frontend): API address, default `http://localhost:8000`. See `frontend/.env.example`.
- `CORS_ORIGINS` (backend): comma-separated allowed origins, default `http://localhost:3000,http://127.0.0.1:3000`.

## Run the tests
```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q
```

## Notes
- PDF text extraction uses `pypdf`.
- This starter does not store uploaded resumes.
- Do not upload sensitive personal documents to any app unless you understand how they are processed.
