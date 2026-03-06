"""
API views for the resume parser.

POST   /api/v1/resumes/upload                 Upload a PDF, create a job, enqueue parsing
GET    /api/v1/resumes/jobs/<job_id>          Get job status (and result link when done)
GET    /api/v1/resumes/data/<data_id>         Get full parsed resume data
GET    /api/v1/resumes/list                   Paginated list of the caller's jobs
DELETE /api/v1/resumes/jobs/<job_id>/delete   Delete a job and its uploaded PDF

All endpoints require a valid JWT access token:
    Authorization: Bearer <access_token>

Users can only see and delete their own jobs.  Requests for jobs owned by a
different user intentionally return 404 (not 403) to prevent resource
enumeration — the caller cannot tell whether a job ID is invalid or just
belongs to someone else.
"""
import logging
import os
import uuid

from django.conf import settings
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .audit import log_action
from .models import AuditLog, ParsedResumeData, ResumeParseJob
from .serializers import ParsedResumeDataSerializer, ResumeParseJobSerializer
from .tasks import parse_resume_task

logger = logging.getLogger("apps.parser")

MAX_FILE_SIZE = settings.UPLOAD_SETTINGS["MAX_FILE_SIZE"]
ALLOWED_EXTENSIONS = settings.UPLOAD_SETTINGS["ALLOWED_EXTENSIONS"]


# ---------------------------------------------------------------------------
# Custom 429 handler
# django-ratelimit raises a 403 Forbidden when block=True, but we want to
# return a proper 429 Too Many Requests with a JSON body instead of HTML.
# Register this in config/urls.py as: handler403 = ratelimited_error
# ---------------------------------------------------------------------------

def ratelimited_error(request, exception):
    """Return JSON 429 instead of the default HTML page for rate-limited requests."""
    return JsonResponse(
        {"error": "Too many requests. Please slow down and try again shortly."},
        status=429,
    )


@method_decorator(
    # 10 uploads per minute per authenticated user.
    # block=True raises a 403 which our handler above converts to 429.
    ratelimit(key="user", rate="10/m", method="POST", block=True),
    name="dispatch",
)
class ResumeUploadView(APIView):
    """
    POST /api/v1/resumes/upload

    Accepts a multipart/form-data request with a "file" field.
    1. Validates file type and size.
    2. Saves the PDF to MEDIA_ROOT/uploads/<uuid>.pdf.
    3. Creates a ResumeParseJob record owned by the authenticated user.
    4. Enqueues the parse_resume_task in Celery (returns immediately).
    5. Responds 202 Accepted with the job_id.
    6. Writes an AuditLog row for the upload action.

    Rate limit: 10 uploads/minute per authenticated user.
    """
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response(
                {"error": "No file provided. Send a PDF as multipart field 'file'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate file extension
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return Response(
                {"error": f"Only PDF files are accepted. Got: {ext or 'no extension'}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate file size
        if file.size > MAX_FILE_SIZE:
            mb = MAX_FILE_SIZE // (1024 * 1024)
            return Response(
                {"error": f"File exceeds the {mb} MB size limit"},
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )

        # Save to MEDIA_ROOT/uploads/<uuid>.pdf
        unique_name = f"{uuid.uuid4()}{ext}"
        relative_path = os.path.join("uploads", unique_name)
        absolute_path = os.path.join(settings.MEDIA_ROOT, relative_path)

        os.makedirs(os.path.dirname(absolute_path), exist_ok=True)
        with open(absolute_path, "wb") as fh:
            for chunk in file.chunks():
                fh.write(chunk)

        # Create the job record — always owned by the authenticated user
        job = ResumeParseJob.objects.create(
            user=request.user,
            original_filename=file.name,
            file_path=relative_path,
            file_size_bytes=file.size,
        )

        # Hand off to Celery — this returns immediately, does not wait
        parse_resume_task.delay(str(job.id))
        logger.info("Enqueued parse_resume_task for job %s (%s)", job.id, file.name)

        log_action(
            request,
            AuditLog.ACTION_UPLOAD,
            details={"filename": file.name, "file_size_bytes": file.size},
            job=job,
        )

        return Response(
            {
                "job_id": str(job.id),
                "status": job.status,
                "message": "Resume queued for processing",
                "estimated_time_seconds": 15,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class JobStatusView(APIView):
    """
    GET /api/v1/resumes/jobs/<job_id>

    Returns the current status of a parsing job.
    Returns 404 if the job does not exist or belongs to a different user
    (we never reveal whether a job ID is valid but owned by someone else).
    If the job is completed, also includes data_id and confidence_score.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        try:
            job = ResumeParseJob.objects.get(id=job_id)
        except (ResumeParseJob.DoesNotExist, ValueError):
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

        if job.user != request.user:
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response(ResumeParseJobSerializer(job).data)


class ParsedDataDetailView(APIView):
    """
    GET /api/v1/resumes/data/<data_id>

    Returns the full structured resume data for a completed parse job.
    Returns 404 if the data does not exist or belongs to a different user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, data_id):
        try:
            parsed = ParsedResumeData.objects.select_related("job").get(id=data_id)
        except (ParsedResumeData.DoesNotExist, ValueError):
            return Response({"error": "Data not found"}, status=status.HTTP_404_NOT_FOUND)

        if parsed.job.user != request.user:
            return Response({"error": "Data not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response(ParsedResumeDataSerializer(parsed).data)


class JobListView(ListAPIView):
    """
    GET /api/v1/resumes/list

    Paginated list of the authenticated user's parse jobs, newest first.
    Users only see their own jobs — never other users' data.
    """
    serializer_class = ResumeParseJobSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ResumeParseJob.objects.filter(user=self.request.user).order_by("-created_at")


class JobDeleteView(APIView):
    """
    DELETE /api/v1/resumes/jobs/<job_id>/delete

    Deletes the job record from the database and removes the uploaded PDF
    from the local filesystem.
    Returns 404 if the job does not exist or belongs to a different user.
    Writes an AuditLog row before deletion.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, job_id):
        try:
            job = ResumeParseJob.objects.get(id=job_id)
        except (ResumeParseJob.DoesNotExist, ValueError):
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

        if job.user != request.user:
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

        log_action(
            request,
            AuditLog.ACTION_DELETE,
            details={"filename": job.original_filename, "job_id": str(job.id)},
            job=job,
        )

        # Remove the uploaded file from disk
        absolute_path = os.path.join(settings.MEDIA_ROOT, job.file_path)
        try:
            if os.path.exists(absolute_path):
                os.remove(absolute_path)
        except OSError as exc:
            logger.warning("Could not delete file %s: %s", absolute_path, exc)

        job.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
