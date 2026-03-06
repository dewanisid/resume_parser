"""
DRF serializers — convert Django model instances to/from JSON.

ResumeParseJobSerializer   → used by list and status endpoints
ParsedResumeDataSerializer → used by the detail (full data) endpoint
"""
from rest_framework import serializers
from .models import ResumeParseJob, ParsedResumeData


class ResumeParseJobSerializer(serializers.ModelSerializer):
    # Included for completed jobs so the frontend can link to /results/:data_id.
    # Returns {"data_id": "...", "confidence_score": 0.95} or null.
    result = serializers.SerializerMethodField()

    def get_result(self, obj):
        if obj.status != ResumeParseJob.STATUS_COMPLETED:
            return None
        try:
            parsed = obj.parsed_data
            return {
                "data_id": str(parsed.id),
                "confidence_score": parsed.confidence_score,
            }
        except ParsedResumeData.DoesNotExist:
            return None

    class Meta:
        model = ResumeParseJob
        fields = [
            "id",
            "user_id",
            "original_filename",
            "file_size_bytes",
            "status",
            "error_message",
            "created_at",
            "started_at",
            "completed_at",
            "processing_time",
            "result",
        ]
        read_only_fields = fields


class ParsedResumeDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParsedResumeData
        fields = [
            "id",
            "job_id",
            "validated_data",
            "raw_json",
            "confidence_score",
            "extraction_method",
            "llm_model",
            "llm_tokens_used",
            "llm_cost",
            "created_at",
        ]
        read_only_fields = fields
