"""
DRF serializers — convert Django model instances to/from JSON.

ResumeParseJobSerializer   → used by list and status endpoints
ParsedResumeDataSerializer → used by the detail (full data) endpoint
"""
from rest_framework import serializers
from .models import ResumeParseJob, ParsedResumeData


class ResumeParseJobSerializer(serializers.ModelSerializer):
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
