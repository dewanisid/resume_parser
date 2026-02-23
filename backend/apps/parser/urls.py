from django.urls import path
from . import views

urlpatterns = [
    # Upload a PDF and get back a job_id
    path("upload", views.ResumeUploadView.as_view(), name="resume-upload"),

    # Check if a job is pending/processing/completed/failed
    path("jobs/<uuid:job_id>", views.JobStatusView.as_view(), name="job-status"),

    # Delete a job and its uploaded file
    path("jobs/<uuid:job_id>/delete", views.JobDeleteView.as_view(), name="job-delete"),

    # Get the full structured resume data for a completed job
    path("data/<uuid:data_id>", views.ParsedDataDetailView.as_view(), name="parsed-data-detail"),

    # Paginated list of all jobs
    path("list", views.JobListView.as_view(), name="resume-list"),
]
