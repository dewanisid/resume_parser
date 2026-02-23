import uuid
from django.db import models
from django.utils import timezone


class ResumeParseJob(models.Model):
    """
    Represents one uploaded PDF file and tracks it through the parsing pipeline.

    Lifecycle: pending → processing → completed (or failed)

    Created immediately when a PDF is uploaded. The Celery worker picks it up,
    updates the status as it works, and links a ParsedResumeData record on success.
    """

    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Nullable in Phase 1 — no authentication yet
    user = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="parse_jobs",
    )

    original_filename = models.CharField(max_length=255)
    # Path relative to MEDIA_ROOT, e.g. "uploads/abc123.pdf"
    file_path = models.CharField(max_length=500)
    file_size_bytes = models.IntegerField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )
    error_message = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    # How long the entire pipeline took, filled in on completion
    processing_time = models.IntegerField(
        null=True, blank=True, help_text="Processing duration in seconds"
    )

    class Meta:
        db_table = "resume_parse_jobs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        return f"{self.original_filename} [{self.status}]"

    # ------------------------------------------------------------------
    # Status transition helpers — called by Celery tasks
    # ------------------------------------------------------------------

    def mark_processing(self):
        """Called when the Celery worker picks up this job."""
        self.status = self.STATUS_PROCESSING
        self.started_at = timezone.now()
        self.save(update_fields=["status", "started_at"])

    def mark_completed(self):
        """Called after ParsedResumeData is successfully saved."""
        now = timezone.now()
        self.status = self.STATUS_COMPLETED
        self.completed_at = now
        if self.started_at:
            self.processing_time = int((now - self.started_at).total_seconds())
        self.save(update_fields=["status", "completed_at", "processing_time"])

    def mark_failed(self, error: str):
        """Called when any step in the pipeline raises an unrecoverable error."""
        self.status = self.STATUS_FAILED
        self.error_message = error
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "error_message", "completed_at"])


class ParsedResumeData(models.Model):
    """
    Stores the structured data extracted from a resume.

    Only created when parsing succeeds. Has a OneToOne link back to the job,
    so you can always go: job.parsed_data to get the results, or
    parsed_data.job to get back to the original upload info.
    """

    EXTRACTION_PDFPLUMBER = "pdfplumber"
    EXTRACTION_OCR = "ocr"

    EXTRACTION_CHOICES = [
        (EXTRACTION_PDFPLUMBER, "PDFPlumber"),
        (EXTRACTION_OCR, "OCR"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.OneToOneField(
        ResumeParseJob,
        on_delete=models.CASCADE,
        related_name="parsed_data",
    )

    # The raw dict returned by the LLM, before any validation
    raw_json = models.JSONField(help_text="Raw JSON returned by the LLM")
    # The same data after Pydantic validates and normalises it
    validated_data = models.JSONField(help_text="Pydantic-validated resume data")

    # 0.0–1.0 score based on how complete the extracted data is
    confidence_score = models.FloatField(db_index=True)

    extraction_method = models.CharField(max_length=20, choices=EXTRACTION_CHOICES)
    llm_model = models.CharField(max_length=80)
    llm_tokens_used = models.IntegerField(default=0)
    # Cost in USD — Decimal for precision with money values
    llm_cost = models.DecimalField(
        max_digits=10, decimal_places=6, default=0, help_text="Cost in USD"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "parsed_resume_data"

    def __str__(self):
        return f"ParsedData for {self.job.original_filename} (score={self.confidence_score:.2f})"
