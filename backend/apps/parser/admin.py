from django.contrib import admin
from .models import ResumeParseJob, ParsedResumeData


@admin.register(ResumeParseJob)
class ResumeParseJobAdmin(admin.ModelAdmin):
    list_display = (
        "original_filename",
        "status",
        "confidence_display",
        "file_size_kb",
        "created_at",
        "processing_time",
    )
    list_filter = ("status",)
    search_fields = ("original_filename",)
    readonly_fields = (
        "id",
        "file_path",
        "file_size_bytes",
        "created_at",
        "started_at",
        "completed_at",
        "processing_time",
    )
    ordering = ("-created_at",)

    def confidence_display(self, obj):
        try:
            return f"{obj.parsed_data.confidence_score:.0%}"
        except ParsedResumeData.DoesNotExist:
            return "—"
    confidence_display.short_description = "Confidence"

    def file_size_kb(self, obj):
        return f"{obj.file_size_bytes / 1024:.1f} KB"
    file_size_kb.short_description = "Size"


@admin.register(ParsedResumeData)
class ParsedResumeDataAdmin(admin.ModelAdmin):
    list_display = (
        "job",
        "confidence_score",
        "extraction_method",
        "llm_model",
        "llm_tokens_used",
        "llm_cost",
        "created_at",
    )
    list_filter = ("extraction_method", "llm_model")
    search_fields = ("job__original_filename",)
    readonly_fields = (
        "id",
        "job",
        "raw_json",
        "validated_data",
        "confidence_score",
        "extraction_method",
        "llm_model",
        "llm_tokens_used",
        "llm_cost",
        "created_at",
    )
    ordering = ("-created_at",)
