"""
Celery tasks for resume parsing.

parse_resume_task(job_id)
    Main pipeline: PDF extraction → LLM → Pydantic validation → DB save.
    Runs asynchronously in a Celery worker process.

parse_batch_resumes(job_ids)
    Fan-out task: dispatches individual parse tasks for a list of job IDs.

cleanup_old_files()
    Periodic housekeeping: deletes completed jobs + PDFs older than 30 days.
    Scheduled via Celery Beat (see config/celery.py).
"""
import logging
import os
from datetime import timedelta
from typing import List

from celery import shared_task
from django.conf import settings
from django.utils import timezone
from pydantic import ValidationError

logger = logging.getLogger("apps.parser")


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def parse_resume_task(self, job_id: str):
    """
    Full resume-parsing pipeline for a single job.

    Steps:
    1. Load the ResumeParseJob from the database and mark it as processing.
    2. Build the absolute file path and extract text from the PDF.
    3. Send the extracted text to Claude and get back structured JSON.
    4. Validate the JSON with Pydantic (ParsedResume schema).
    5. Save a ParsedResumeData record with the results.
    6. Mark the job as completed (or failed on any unrecoverable error).

    bind=True means `self` is the task instance — needed for self.retry().
    max_retries=3 limits how many times Celery will automatically retry.
    """
    # Imports inside the function avoid circular-import issues at module load time
    from .models import ResumeParseJob, ParsedResumeData
    from .pdf_extractor import PDFExtractor, PDFExtractionError
    from .llm_extractor import LLMExtractor, LLMExtractionError
    from .schemas import ParsedResume, calculate_confidence

    # Step 1: Load job
    try:
        job = ResumeParseJob.objects.get(id=job_id)
    except ResumeParseJob.DoesNotExist:
        logger.error("Job %s not found in database — skipping", job_id)
        return

    job.mark_processing()
    logger.info("Processing job %s (%s)", job_id, job.original_filename)

    try:
        # Step 2: PDF extraction
        # file_path is relative to MEDIA_ROOT (e.g. "uploads/abc123.pdf")
        absolute_path = os.path.join(settings.MEDIA_ROOT, job.file_path)
        extraction = PDFExtractor().extract_text(absolute_path)

        if not extraction["text"]:
            raise PDFExtractionError("No text could be extracted from the PDF")

        # Step 3: LLM extraction
        raw_dict, usage_meta = LLMExtractor().extract_structured_data(extraction["text"])

        # Step 4: Pydantic validation
        # This raises ValidationError if the LLM response doesn't match the schema
        validated = ParsedResume(**raw_dict)
        confidence = calculate_confidence(validated)

        # Step 5: Save results
        ParsedResumeData.objects.create(
            job=job,
            raw_json=raw_dict,
            validated_data=validated.model_dump(mode="json"),
            confidence_score=confidence,
            extraction_method=extraction["method"],
            llm_model=usage_meta["model"],
            llm_tokens_used=usage_meta["input_tokens"] + usage_meta["output_tokens"],
            llm_cost=usage_meta["cost_usd"],
        )

        # Step 6: Mark completed
        job.mark_completed()
        logger.info(
            "Job %s completed — confidence=%.2f, method=%s, tokens=%d",
            job_id, confidence, extraction["method"],
            usage_meta["input_tokens"] + usage_meta["output_tokens"],
        )

    except ValidationError as exc:
        # Pydantic validation failed — the LLM returned something we can't use.
        # Don't retry: the same LLM call would likely fail the same way.
        error_msg = f"Schema validation failed: {exc.error_count()} error(s)"
        logger.warning("Job %s — %s", job_id, error_msg)
        job.mark_failed(error_msg)

    except (PDFExtractionError, LLMExtractionError) as exc:
        # Transient failures (file I/O errors, API timeouts) — retry with
        # exponential backoff: wait 30s, 60s, 120s between attempts.
        logger.error("Job %s failed (attempt %d): %s", job_id, self.request.retries + 1, exc)
        job.mark_failed(str(exc))
        raise self.retry(exc=exc, countdown=2 ** self.request.retries * 30)

    except Exception as exc:
        # Unexpected error — log the full traceback and fail without retry
        logger.exception("Unexpected error for job %s", job_id)
        job.mark_failed(f"Unexpected error: {exc}")


@shared_task
def parse_batch_resumes(job_ids: List[str]):
    """
    Fan-out task: enqueue individual parse tasks for a list of job IDs.

    Called by BatchUploadView (Phase 2). Each job is processed independently
    by a worker, so they run in parallel up to the worker concurrency limit.
    """
    for job_id in job_ids:
        parse_resume_task.delay(job_id)
    logger.info("Dispatched %d parse tasks from batch", len(job_ids))


@shared_task
def cleanup_old_files():
    """
    Delete completed jobs + their uploaded PDFs older than 30 days.

    Scheduled via Celery Beat to run at 02:00 UTC daily (see config/celery.py).
    This keeps storage usage under control without requiring manual cleanup.
    """
    from .models import ResumeParseJob

    cutoff = timezone.now() - timedelta(days=30)
    old_jobs = ResumeParseJob.objects.filter(
        created_at__lt=cutoff,
        status=ResumeParseJob.STATUS_COMPLETED,
    )

    deleted = 0
    for job in old_jobs:
        absolute_path = os.path.join(settings.MEDIA_ROOT, job.file_path)
        try:
            if os.path.exists(absolute_path):
                os.remove(absolute_path)
        except OSError as exc:
            logger.warning("Could not delete file %s: %s", absolute_path, exc)

        job.delete()
        deleted += 1

    logger.info("cleanup_old_files: removed %d old jobs", deleted)
