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
