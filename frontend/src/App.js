import { useState } from "react";
import axios from "axios";
import {
  ArcElement,
  Chart as ChartJS,
  Legend,
  Tooltip
} from "chart.js";
import { Pie } from "react-chartjs-2";

ChartJS.register(ArcElement, Tooltip, Legend);

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

function KeywordList({ title, items, variant }) {
  return (
    <section className="keyword-card">
      <h3>{title} <span className="count">{items.length}</span></h3>
      {items.length ? (
        <div className="keyword-list">
          {items.map((item) => (
            <span className={`keyword ${variant}`} key={item}>{item}</span>
          ))}
        </div>
      ) : (
        <p className="muted">No keywords to show.</p>
      )}
    </section>
  );
}

export default function App() {
  const [resume, setResume] = useState(null);
  const [jobDescription, setJobDescription] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setResult(null);

    if (!resume) {
      setError("Please choose a PDF or TXT resume first.");
      return;
    }
    if (!jobDescription.trim()) {
      setError("Please paste the job description.");
      return;
    }

    const formData = new FormData();
    formData.append("resume", resume);
    formData.append("job_description", jobDescription);

    try {
      setLoading(true);
      const response = await axios.post(`${API_URL}/analyze/`, formData);
      setResult(response.data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Could not connect to the API. Make sure the FastAPI backend is running on port 8000."
      );
    } finally {
      setLoading(false);
    }
  }

  const chartData = result ? {
    labels: ["Matched", "Missing"],
    datasets: [{
      data: [
        result.total_matched_keywords,
        Math.max(result.total_job_keywords - result.total_matched_keywords, 0)
      ],
      backgroundColor: ["#16a34a", "#e5e7eb"],
      borderWidth: 0
    }]
  } : null;

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="AI Resume Optimizer home">
          <span className="brand-mark">R</span>
          <span>Resume<span className="brand-light">Pilot</span></span>
        </a>
        <span className="topbar-tag">CAREER TOOLKIT</span>
      </header>

      <section className="hero">
        <p className="eyebrow">YOUR NEXT OPPORTUNITY STARTS HERE</p>
        <h1>Make your resume work<br /><span>for the role you want.</span></h1>
        <p className="hero-copy">
          Compare your resume with a job description and find keywords worth reviewing.
        </p>
      </section>

      <form className="workspace" onSubmit={handleSubmit}>
        <section className="panel">
          <div className="section-heading">
            <span className="step">01</span>
            <div>
              <h2>Upload your resume</h2>
              <p>Choose a text-based PDF or TXT file (max 5 MB).</p>
            </div>
          </div>
          <label className="upload-area">
            <input
              type="file"
              accept=".pdf,.txt"
              onChange={(event) => setResume(event.target.files?.[0] || null)}
            />
            <span className="upload-icon">↑</span>
            <strong>{resume ? resume.name : "Choose a file to upload"}</strong>
            <span className="muted">{resume ? `${(resume.size / 1024).toFixed(1)} KB` : "PDF or TXT · Your file is processed for this request"}</span>
          </label>
        </section>

        <section className="panel">
          <div className="section-heading">
            <span className="step">02</span>
            <div>
              <h2>Add the job description</h2>
              <p>Paste the role requirements to compare relevant terms.</p>
            </div>
          </div>
          <textarea
            value={jobDescription}
            onChange={(event) => setJobDescription(event.target.value)}
            placeholder="Paste the job title, responsibilities, required skills and qualifications here..."
            rows={9}
          />
          <div className="textarea-footer">{jobDescription.trim().length} characters</div>
        </section>

        {error && <div className="alert" role="alert">{error}</div>}

        <button className="analyze-button" type="submit" disabled={loading}>
          {loading ? "Analyzing resume..." : "Analyze resume  →"}
        </button>
      </form>

      {result && (
        <section className="results">
          <div className="results-heading">
            <div>
              <p className="eyebrow">YOUR ANALYSIS</p>
              <h2>Resume match report</h2>
              <p className="muted">File: {result.filename}</p>
            </div>
            <div className="score-badge">
              <strong>{result.ats_score}%</strong>
              <span>keyword match</span>
            </div>
          </div>

          <div className="report-grid">
            <section className="panel chart-panel">
              <h3>Keyword overview</h3>
              <div className="chart-wrap">
                <Pie
                  data={chartData}
                  options={{
                    plugins: { legend: { position: "bottom" } },
                    maintainAspectRatio: false
                  }}
                />
              </div>
              <p className="muted small">{result.note}</p>
            </section>
            <section className="stats-panel">
              <div className="stat-card">
                <span className="stat-label">Matched keywords</span>
                <strong>{result.total_matched_keywords}</strong>
              </div>
              <div className="stat-card">
                <span className="stat-label">Keywords reviewed</span>
                <strong>{result.total_job_keywords}</strong>
              </div>
              <p className="tip">Tip: only add a missing keyword if it accurately describes your experience or skills.</p>
            </section>
          </div>

          <div className="keyword-grid">
            <KeywordList title="Matched keywords" items={result.matched_keywords} variant="matched" />
            <KeywordList title="Missing keywords" items={result.missing_keywords} variant="missing" />
          </div>
        </section>
      )}

      <footer>
        <p>ResumePilot · Built with React and FastAPI</p>
        <p className="small">A learning project. Results are keyword estimates, not hiring advice or a real ATS score.</p>
      </footer>
    </main>
  );
}
