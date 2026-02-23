"""
Integration tests for the REST API endpoints.

Uses Django's test database (auto-created and destroyed per test run).
Celery task dispatch is mocked so tests run without Redis/workers.
"""
import io
import uuid
import pytest
from rest_framework.test import APIClient
from unittest.mock import patch


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def mock_task():
    """Prevent Celery from actually dispatching tasks during tests."""
    with patch("apps.parser.views.parse_resume_task") as m:
        m.delay.return_value = None
        yield m


# ---------------------------------------------------------------------------
# Upload endpoint
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_upload_valid_pdf_returns_202(client, mock_task):
    pdf = io.BytesIO(b"%PDF-1.4 " + b"x" * 300)
    pdf.name = "resume.pdf"

    resp = client.post("/api/v1/resumes/upload", {"file": pdf}, format="multipart")

    assert resp.status_code == 202
    data = resp.json()
    assert "job_id" in data
    assert data["status"] == "pending"
    mock_task.delay.assert_called_once()


@pytest.mark.django_db
def test_upload_non_pdf_returns_400(client, mock_task):
    txt = io.BytesIO(b"not a pdf")
    txt.name = "resume.txt"

    resp = client.post("/api/v1/resumes/upload", {"file": txt}, format="multipart")

    assert resp.status_code == 400
    assert "PDF" in resp.json()["error"]


@pytest.mark.django_db
def test_upload_no_file_returns_400(client):
    resp = client.post("/api/v1/resumes/upload", {}, format="multipart")
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Job status endpoint
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_job_status_returns_pending(client):
    from apps.parser.models import ResumeParseJob
    job = ResumeParseJob.objects.create(
        original_filename="test.pdf",
        file_path="uploads/test.pdf",
        file_size_bytes=1024,
    )
    resp = client.get(f"/api/v1/resumes/jobs/{job.id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"


@pytest.mark.django_db
def test_job_status_includes_result_when_completed(client):
    from apps.parser.models import ResumeParseJob, ParsedResumeData
    job = ResumeParseJob.objects.create(
        original_filename="done.pdf",
        file_path="uploads/done.pdf",
        file_size_bytes=1024,
        status=ResumeParseJob.STATUS_COMPLETED,
    )
    parsed = ParsedResumeData.objects.create(
        job=job,
        raw_json={"contact": {"name": "Alice"}},
        validated_data={"contact": {"name": "Alice"}},
        confidence_score=0.85,
        extraction_method="pdfplumber",
        llm_model="claude-haiku-4-5-20251001",
    )
    resp = client.get(f"/api/v1/resumes/jobs/{job.id}")
    assert resp.status_code == 200
    assert resp.json()["result"]["data_id"] == str(parsed.id)
    assert resp.json()["result"]["confidence_score"] == 0.85


@pytest.mark.django_db
def test_job_status_404_for_unknown_id(client):
    resp = client.get(f"/api/v1/resumes/jobs/{uuid.uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Parsed data detail endpoint
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_parsed_data_detail_returns_validated_data(client):
    from apps.parser.models import ResumeParseJob, ParsedResumeData
    job = ResumeParseJob.objects.create(
        original_filename="alice.pdf",
        file_path="uploads/alice.pdf",
        file_size_bytes=2048,
        status=ResumeParseJob.STATUS_COMPLETED,
    )
    parsed = ParsedResumeData.objects.create(
        job=job,
        raw_json={"contact": {"name": "Alice"}},
        validated_data={"contact": {"name": "Alice", "email": None}},
        confidence_score=0.75,
        extraction_method="pdfplumber",
        llm_model="claude-haiku-4-5-20251001",
    )
    resp = client.get(f"/api/v1/resumes/data/{parsed.id}")
    assert resp.status_code == 200
    assert resp.json()["validated_data"]["contact"]["name"] == "Alice"


# ---------------------------------------------------------------------------
# List endpoint
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_list_returns_paginated_results(client):
    from apps.parser.models import ResumeParseJob
    for i in range(5):
        ResumeParseJob.objects.create(
            original_filename=f"resume_{i}.pdf",
            file_path=f"uploads/resume_{i}.pdf",
            file_size_bytes=1024,
        )
    resp = client.get("/api/v1/resumes/list")
    assert resp.status_code == 200
    assert "results" in resp.json()
    assert resp.json()["count"] == 5


# ---------------------------------------------------------------------------
# Delete endpoint
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_delete_job_returns_204(client, tmp_path):
    from apps.parser.models import ResumeParseJob

    # Create a real file on disk so the delete view can remove it
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    pdf = upload_dir / "dummy.pdf"
    pdf.write_bytes(b"%PDF")

    job = ResumeParseJob.objects.create(
        original_filename="dummy.pdf",
        file_path="uploads/dummy.pdf",
        file_size_bytes=4,
    )

    with patch("apps.parser.views.settings") as mock_settings:
        mock_settings.MEDIA_ROOT = str(tmp_path)
        mock_settings.UPLOAD_SETTINGS = {
            "MAX_FILE_SIZE": 10 * 1024 * 1024,
            "ALLOWED_EXTENSIONS": [".pdf"],
        }
        resp = client.delete(f"/api/v1/resumes/jobs/{job.id}/delete")

    assert resp.status_code == 204
    assert not ResumeParseJob.objects.filter(id=job.id).exists()
