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


def test_weighted_score_preserves_original_overlap():
    body = analyze(b"Python", "cv.txt", "Python Python Python React").json()
    assert body["ats_score"] == 50
    assert body["weighted_keyword_score"] == 75
    assert body["keyword_weights"] == {"python": 3, "react": 1}
    assert body["total_job_keyword_weight"] == 4
    assert body["matched_keyword_weight"] == 3


def test_resume_repetition_does_not_increase_weight():
    a = analyze(b"Python", "cv.txt", "Python Python React").json()
    b = analyze(b"Python Python Python Python", "cv.txt", "Python Python React").json()
    assert a["weighted_keyword_score"] == b["weighted_keyword_score"] == 67


def test_weighting_case_symbols_and_stop_words():
    body = analyze(b"C++ Node.js", "cv.txt", "C++ c++ Node.js and the React").json()
    assert body["keyword_weights"] == {"c++": 2, "node.js": 1, "react": 1}
    assert body["weighted_keyword_score"] == 75


def test_no_usable_job_keywords():
    body = analyze(b"Python", "cv.txt", "the and 123 456").json()
    assert body["weighted_keyword_score"] == 0
    assert body["keyword_weights"] == {}
    assert body["total_job_keyword_weight"] == 0


def test_all_or_no_matches():
    assert analyze(b"Python React", "cv.txt", "Python Python React").json()["weighted_keyword_score"] == 100
    assert analyze(b"Docker", "cv.txt", "Python Python React").json()["weighted_keyword_score"] == 0


def test_weight_summary_uses_all_terms_not_display_limit():
    terms = ["term" + str(i) for i in range(60)]
    body = analyze(" ".join(terms).encode(), "cv.txt", " ".join(terms)).json()
    assert len(body["keyword_weights"]) == 50
    assert body["total_job_keywords"] == 60
    assert body["total_job_keyword_weight"] == 60
    assert body["matched_keyword_weight"] == 60
    assert body["weighted_keyword_score"] == 100


def test_equal_frequency_keeps_first_occurrence_order():
    body = analyze(b"React", "cv.txt", "React Python Docker").json()
    assert list(body["keyword_weights"]) == ["react", "python", "docker"]


def pdf_fixture(text):
    """Small synthetic one-page PDF with real text and correct xref offsets."""
    content = ("BT /F1 12 Tf 72 720 Td (" + text + ") Tj ET").encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream",
    ]
    data = b"%PDF-1.4\n"
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(data))
        data += str(number).encode() + b" 0 obj\n" + obj + b"\nendobj\n"
    xref = len(data)
    data += b"xref\n0 6\n0000000000 65535 f \n"
    data += b"".join(("%010d 00000 n \n" % offset).encode() for offset in offsets[1:])
    data += b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n" + str(xref).encode() + b"\n%%EOF\n"
    return data


def test_readable_pdf_analysis():
    result = analyze(pdf_fixture("Python React"), "synthetic.pdf", "Python Python Docker")
    assert result.status_code == 200
    assert result.json()["matched_keywords"] == ["python"]
    assert result.json()["weighted_keyword_score"] == 67


def test_pdf_without_readable_text_is_rejected():
    assert analyze(pdf_fixture(""), "empty-text.pdf", "Python").status_code == 400
