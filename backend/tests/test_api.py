"""
Integration tests for the REST API endpoints.

Uses Django's test database (auto-created and destroyed per test run).
Celery task dispatch is mocked so tests run without Redis/workers.
"""
import io
import uuid
import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def user(db):
    """Primary test user."""
    return User.objects.create_user(
        username="alice",
        email="alice@example.com",
        password="testpass123",
    )


@pytest.fixture
def other_user(db):
    """A second user to test ownership enforcement."""
    return User.objects.create_user(
        username="bob",
        email="bob@example.com",
        password="testpass123",
    )


@pytest.fixture
def auth_client(user):
    """APIClient authenticated as `user` via a JWT access token."""
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


@pytest.fixture
def other_client(other_user):
    """APIClient authenticated as `other_user` via a JWT access token."""
    client = APIClient()
    refresh = RefreshToken.for_user(other_user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


@pytest.fixture
def anon_client():
    """Unauthenticated (anonymous) APIClient."""
    return APIClient()


@pytest.fixture
def mock_task():
    """Prevent Celery from actually dispatching tasks during tests."""
    with patch("apps.parser.views.parse_resume_task") as m:
        m.delay.return_value = None
        yield m


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_register_creates_user_and_returns_tokens(anon_client):
    resp = anon_client.post(
        "/api/v1/auth/register",
        {
            "username": "newuser",
            "email": "new@example.com",
            "password": "securepass1",
            "password2": "securepass1",
        },
        format="json",
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["user"]["username"] == "newuser"
    assert "access" in data
    assert "refresh" in data


@pytest.mark.django_db
def test_register_rejects_mismatched_passwords(anon_client):
    resp = anon_client.post(
        "/api/v1/auth/register",
        {
            "username": "u",
            "email": "u@example.com",
            "password": "pass1234",
            "password2": "different",
        },
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_login_returns_tokens(user, anon_client):
    resp = anon_client.post(
        "/api/v1/auth/login",
        {"username": "alice", "password": "testpass123"},
        format="json",
    )
    assert resp.status_code == 200
    assert "access" in resp.json()
    assert "refresh" in resp.json()


@pytest.mark.django_db
def test_login_rejects_wrong_password(user, anon_client):
    resp = anon_client.post(
        "/api/v1/auth/login",
        {"username": "alice", "password": "wrongpassword"},
        format="json",
    )
    assert resp.status_code == 401


@pytest.mark.django_db
def test_me_returns_current_user(auth_client):
    resp = auth_client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice"


@pytest.mark.django_db
def test_me_requires_auth(anon_client):
    resp = anon_client.get("/api/v1/auth/me")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Upload endpoint
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_upload_valid_pdf_returns_202(auth_client, mock_task):
    pdf = io.BytesIO(b"%PDF-1.4 " + b"x" * 300)
    pdf.name = "resume.pdf"

    resp = auth_client.post("/api/v1/resumes/upload", {"file": pdf}, format="multipart")

    assert resp.status_code == 202
    data = resp.json()
    assert "job_id" in data
    assert data["status"] == "pending"
    mock_task.delay.assert_called_once()


@pytest.mark.django_db
def test_upload_non_pdf_returns_400(auth_client, mock_task):
    txt = io.BytesIO(b"not a pdf")
    txt.name = "resume.txt"

    resp = auth_client.post("/api/v1/resumes/upload", {"file": txt}, format="multipart")

    assert resp.status_code == 400
    assert "PDF" in resp.json()["error"]


@pytest.mark.django_db
def test_upload_no_file_returns_400(auth_client):
    resp = auth_client.post("/api/v1/resumes/upload", {}, format="multipart")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_upload_requires_auth(anon_client):
    pdf = io.BytesIO(b"%PDF-1.4 " + b"x" * 300)
    pdf.name = "resume.pdf"
    resp = anon_client.post("/api/v1/resumes/upload", {"file": pdf}, format="multipart")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Job status endpoint
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_job_status_returns_pending(auth_client, user):
    from apps.parser.models import ResumeParseJob
    job = ResumeParseJob.objects.create(
        user=user,
        original_filename="test.pdf",
        file_path="uploads/test.pdf",
        file_size_bytes=1024,
    )
    resp = auth_client.get(f"/api/v1/resumes/jobs/{job.id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"


@pytest.mark.django_db
def test_job_status_includes_result_when_completed(auth_client, user):
    from apps.parser.models import ResumeParseJob, ParsedResumeData
    job = ResumeParseJob.objects.create(
        user=user,
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
    resp = auth_client.get(f"/api/v1/resumes/jobs/{job.id}")
    assert resp.status_code == 200
    assert resp.json()["result"]["data_id"] == str(parsed.id)
    assert resp.json()["result"]["confidence_score"] == 0.85


@pytest.mark.django_db
def test_job_status_404_for_unknown_id(auth_client):
    resp = auth_client.get(f"/api/v1/resumes/jobs/{uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_job_status_404_for_other_users_job(auth_client, other_user):
    """A user cannot see another user's job — 404 prevents resource enumeration."""
    from apps.parser.models import ResumeParseJob
    job = ResumeParseJob.objects.create(
        user=other_user,
        original_filename="secret.pdf",
        file_path="uploads/secret.pdf",
        file_size_bytes=1024,
    )
    resp = auth_client.get(f"/api/v1/resumes/jobs/{job.id}")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_job_status_requires_auth(anon_client, user):
    from apps.parser.models import ResumeParseJob
    job = ResumeParseJob.objects.create(
        user=user,
        original_filename="test.pdf",
        file_path="uploads/test.pdf",
        file_size_bytes=1024,
    )
    resp = anon_client.get(f"/api/v1/resumes/jobs/{job.id}")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Parsed data detail endpoint
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_parsed_data_detail_returns_validated_data(auth_client, user):
    from apps.parser.models import ResumeParseJob, ParsedResumeData
    job = ResumeParseJob.objects.create(
        user=user,
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
    resp = auth_client.get(f"/api/v1/resumes/data/{parsed.id}")
    assert resp.status_code == 200
    assert resp.json()["validated_data"]["contact"]["name"] == "Alice"


@pytest.mark.django_db
def test_parsed_data_detail_404_for_other_users_data(auth_client, other_user):
    """A user cannot read another user's parsed result."""
    from apps.parser.models import ResumeParseJob, ParsedResumeData
    job = ResumeParseJob.objects.create(
        user=other_user,
        original_filename="secret.pdf",
        file_path="uploads/secret.pdf",
        file_size_bytes=1024,
        status=ResumeParseJob.STATUS_COMPLETED,
    )
    parsed = ParsedResumeData.objects.create(
        job=job,
        raw_json={},
        validated_data={},
        confidence_score=0.9,
        extraction_method="pdfplumber",
        llm_model="claude-haiku-4-5-20251001",
    )
    resp = auth_client.get(f"/api/v1/resumes/data/{parsed.id}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# List endpoint
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_list_returns_paginated_results(auth_client, user):
    from apps.parser.models import ResumeParseJob
    for i in range(5):
        ResumeParseJob.objects.create(
            user=user,
            original_filename=f"resume_{i}.pdf",
            file_path=f"uploads/resume_{i}.pdf",
            file_size_bytes=1024,
        )
    resp = auth_client.get("/api/v1/resumes/list")
    assert resp.status_code == 200
    assert "results" in resp.json()
    assert resp.json()["count"] == 5


@pytest.mark.django_db
def test_list_only_returns_own_jobs(auth_client, user, other_user):
    """Each user only sees their own jobs — never another user's."""
    from apps.parser.models import ResumeParseJob
    ResumeParseJob.objects.create(
        user=user,
        original_filename="mine.pdf",
        file_path="uploads/mine.pdf",
        file_size_bytes=1024,
    )
    ResumeParseJob.objects.create(
        user=other_user,
        original_filename="theirs.pdf",
        file_path="uploads/theirs.pdf",
        file_size_bytes=1024,
    )
    resp = auth_client.get("/api/v1/resumes/list")
    assert resp.status_code == 200
    assert resp.json()["count"] == 1
    assert resp.json()["results"][0]["original_filename"] == "mine.pdf"


# ---------------------------------------------------------------------------
# Delete endpoint
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_delete_job_returns_204(auth_client, user, tmp_path):
    from apps.parser.models import ResumeParseJob

    # Create a real file on disk so the delete view can remove it
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    pdf = upload_dir / "dummy.pdf"
    pdf.write_bytes(b"%PDF")

    job = ResumeParseJob.objects.create(
        user=user,
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
        resp = auth_client.delete(f"/api/v1/resumes/jobs/{job.id}/delete")

    assert resp.status_code == 204
    assert not ResumeParseJob.objects.filter(id=job.id).exists()


@pytest.mark.django_db
def test_delete_job_404_for_other_users_job(auth_client, other_user):
    """A user cannot delete another user's job, and the job must remain intact."""
    from apps.parser.models import ResumeParseJob
    job = ResumeParseJob.objects.create(
        user=other_user,
        original_filename="notmine.pdf",
        file_path="uploads/notmine.pdf",
        file_size_bytes=1024,
    )
    resp = auth_client.delete(f"/api/v1/resumes/jobs/{job.id}/delete")
    assert resp.status_code == 404
    # The job must still exist
    assert ResumeParseJob.objects.filter(id=job.id).exists()
