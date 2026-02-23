"""
API views for the resume parser.

POST   /api/v1/resumes/upload            Upload a PDF, create a job, enqueue parsing
GET    /api/v1/resumes/jobs/<job_id>     Get job status (and result link when done)
GET    /api/v1/resumes/data/<data_id>    Get full parsed resume data
GET    /api/v1/resumes/list              Paginated list of all jobs
DELETE /api/v1/resumes/jobs/<job_id>/delete  Delete a job and its uploaded PDF
"""
import logging
import os
import uuid

from django.conf import settings
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ParsedResumeData, ResumeParseJob
from .serializers import ParsedResumeDataSerializer, ResumeParseJobSerializer
from .tasks import parse_resume_task

logger = logging.getLogger("apps.parser")

MAX_FILE_SIZE = settings.UPLOAD_SETTINGS["MAX_FILE_SIZE"]
ALLOWED_EXTENSIONS = settings.UPLOAD_SETTINGS["ALLOWED_EXTENSIONS"]


class ResumeUploadView(APIView):
    """
    POST /api/v1/resumes/upload

    Accepts a multipart/form-data request with a "file" field.
    1. Validates file type and size.
    2. Saves the PDF to MEDIA_ROOT/uploads/<uuid>.pdf.
    3. Creates a ResumeParseJob record in the database.
    4. Enqueues the parse_resume_task in Celery (returns immediately).
    5. Responds 202 Accepted with the job_id.

    The caller then polls GET /jobs/<job_id> to check progress.
    """
    parser_classes = [MultiPartParser, FormParser]

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

        # Create the job record
        job = ResumeParseJob.objects.create(
            original_filename=file.name,
            file_path=relative_path,
            file_size_bytes=file.size,
        )

        # Hand off to Celery — this returns immediately, does not wait
        parse_resume_task.delay(str(job.id))
        logger.info("Enqueued parse_resume_task for job %s (%s)", job.id, file.name)

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
    If the job is completed, also includes the data_id and confidence_score
    so the caller knows where to fetch the full results.
    """

    def get(self, request, job_id):
        try:
            job = ResumeParseJob.objects.get(id=job_id)
        except (ResumeParseJob.DoesNotExist, ValueError):
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

        data = ResumeParseJobSerializer(job).data

        # If parsing succeeded, attach a link to the parsed data
        if job.status == ResumeParseJob.STATUS_COMPLETED:
            try:
                parsed = job.parsed_data
                data["result"] = {
                    "data_id": str(parsed.id),
                    "confidence_score": parsed.confidence_score,
                }
            except ParsedResumeData.DoesNotExist:
                pass

        return Response(data)


class ParsedDataDetailView(APIView):
    """
    GET /api/v1/resumes/data/<data_id>

    Returns the full structured resume data for a completed parse job.
    The validated_data field contains the Pydantic-validated JSON.
    """

    def get(self, request, data_id):
        try:
            parsed = ParsedResumeData.objects.select_related("job").get(id=data_id)
        except (ParsedResumeData.DoesNotExist, ValueError):
            return Response({"error": "Data not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response(ParsedResumeDataSerializer(parsed).data)


class JobListView(ListAPIView):
    """
    GET /api/v1/resumes/list

    Paginated list of all parse jobs, newest first.
    Query params: ?page=2&page_size=10 (page_size capped at 100 by DRF default)
    """
    serializer_class = ResumeParseJobSerializer
    queryset = ResumeParseJob.objects.all().order_by("-created_at")


class JobDeleteView(APIView):
    """
    DELETE /api/v1/resumes/jobs/<job_id>/delete

    Deletes the job record from the database and removes the uploaded PDF
    from the local filesystem. Returns 204 No Content on success.
    """

    def delete(self, request, job_id):
        try:
            job = ResumeParseJob.objects.get(id=job_id)
        except (ResumeParseJob.DoesNotExist, ValueError):
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

        # Remove the uploaded file from disk
        absolute_path = os.path.join(settings.MEDIA_ROOT, job.file_path)
        try:
            if os.path.exists(absolute_path):
                os.remove(absolute_path)
        except OSError as exc:
            # Log but don't fail — the DB record should still be deleted
            logger.warning("Could not delete file %s: %s", absolute_path, exc)

        job.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
