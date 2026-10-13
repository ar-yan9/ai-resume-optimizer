from fastapi.testclient import TestClient

from main import app, keywords

client = TestClient(app)


def analyze(resume_bytes, name, jd):
    return client.post(
        "/analyze/",
        files={"resume": (name, resume_bytes, "application/octet-stream")},
        data={"job_description": jd},
    )


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_keywords_drop_stop_words_and_keep_symbols():
    words = keywords("We use Python, C++ and Node.js with the REST APIs")
    assert "python" in words
    assert "c++" in words
    assert "node.js" in words
    assert "the" not in words


def test_txt_analysis_counts_matches():
    r = analyze(b"Python FastAPI React developer", "cv.txt", "Python React Docker Kubernetes")
    assert r.status_code == 200
    body = r.json()
    assert body["matched_keywords"] == ["python", "react"]
    assert body["missing_keywords"] == ["docker", "kubernetes"]
    assert body["ats_score"] == 50


def test_rejects_unsupported_type():
    assert analyze(b"x", "cv.docx", "Python").status_code == 400


def test_rejects_empty_file_and_blank_jd():
    assert analyze(b"", "cv.txt", "Python").status_code == 400
    assert analyze(b"Python", "cv.txt", "   ").status_code == 400


def test_rejects_bad_pdf():
    assert analyze(b"not a pdf", "cv.pdf", "Python").status_code == 400
