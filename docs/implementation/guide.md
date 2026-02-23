# Resume Parser - Implementation Guide

## Prerequisites

Before starting, ensure you have:

- Python 3.11+
- Node.js 18+ (for frontend)
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose
- AWS account (for S3)
- OpenAI API key

---

## Phase 1: Project Setup

### Step 1.1: Initialize Django Project

```bash
# Create project directory
mkdir resume_parser
cd resume_parser

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Django and essential packages
pip install django djangorestframework django-cors-headers
pip install psycopg2-binary django-environ
pip install celery redis
pip install pdfplumber pytesseract pdf2image Pillow
pip install openai anthropic
pip install pydantic
pip install boto3 django-storages
pip install gunicorn

# Create Django project
django-admin startproject config .

# Create parser app
python manage.py startapp parser
mv parser backend/apps/parser  # Organize structure

# Create requirements.txt
pip freeze > requirements.txt
```

**`requirements.txt`**:
```txt
Django==5.0.1
djangorestframework==3.14.0
django-cors-headers==4.3.1
psycopg2-binary==2.9.9
django-environ==0.11.2
celery==5.3.4
redis==5.0.1
pdfplumber==0.10.3
pytesseract==0.3.10
pdf2image==1.16.3
Pillow==10.1.0
openai==1.7.0
anthropic==0.8.0
pydantic==2.5.3
boto3==1.34.10
django-storages==1.14.2
gunicorn==21.2.0
python-magic==0.4.27
django-ratelimit==4.1.0
sentry-sdk==1.39.2
structlog==24.1.0
```

### Step 1.2: Configure Django Settings

**`config/settings.py`**:

```python
import os
from pathlib import Path
import environ

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Environment variables
env = environ.Env(
    DEBUG=(bool, False)
)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'corsheaders',
    'storages',

    # Local apps
    'apps.parser',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': env.db('DATABASE_URL', default='postgresql://postgres:postgres@localhost:5432/resume_parser')
}

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# CORS
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    'http://localhost:3000',
    'http://localhost:5173',
])

# AWS S3
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', default='us-east-1')
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
AWS_DEFAULT_ACL = 'private'

# Celery
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = 'UTC'

# LLM Configuration
OPENAI_API_KEY = env('OPENAI_API_KEY')
ANTHROPIC_API_KEY = env('ANTHROPIC_API_KEY', default='')

LLM_SETTINGS = {
    'PROVIDER': env('LLM_PROVIDER', default='openai'),
    'MODEL': env('LLM_MODEL', default='gpt-4o-mini'),
    'MAX_TOKENS': 2000,
    'TEMPERATURE': 0.1,
    'TIMEOUT': 30,
    'MAX_RETRIES': 3,
}

# Upload settings
UPLOAD_SETTINGS = {
    'MAX_FILE_SIZE': 10 * 1024 * 1024,  # 10MB
    'ALLOWED_EXTENSIONS': ['.pdf'],
    'STORAGE_BACKEND': env('STORAGE_BACKEND', default='S3'),
}

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
```

**`.env.example`**:
```bash
DEBUG=True
SECRET_KEY=your-secret-key-here-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1

DATABASE_URL=postgresql://postgres:postgres@localhost:5432/resume_parser

CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_STORAGE_BUCKET_NAME=resume-parser-dev
AWS_S3_REGION_NAME=us-east-1

OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini

STORAGE_BACKEND=S3

CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Step 1.3: Setup Celery

**`config/celery.py`**:

```python
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('resume_parser')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    'cleanup-old-files': {
        'task': 'apps.parser.tasks.cleanup_old_files',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
```

**`config/__init__.py`**:
```python
from .celery import app as celery_app

__all__ = ('celery_app',)
```

---

## Phase 2: Database Models

### Step 2.1: Create Models

**`apps/parser/models.py`**:

```python
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    """Extended user model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.CharField(max_length=100, blank=True)
    role = models.CharField(
        max_length=20,
        choices=[('recruiter', 'Recruiter'), ('admin', 'Admin')],
        default='recruiter'
    )

    class Meta:
        db_table = 'users'


class ResumeParseJob(models.Model):
    """Tracks resume parsing jobs"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='parse_jobs')
    original_filename = models.CharField(max_length=255)
    file_url = models.URLField(max_length=500)
    file_size_bytes = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    processing_time = models.IntegerField(null=True, blank=True, help_text="Processing time in seconds")

    class Meta:
        db_table = 'resume_parse_jobs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.original_filename} - {self.status}"

    @property
    def is_complete(self):
        return self.status in ['completed', 'failed']


class ParsedResumeData(models.Model):
    """Stores extracted and validated resume data"""
    EXTRACTION_METHODS = [
        ('pdfplumber', 'PDFPlumber'),
        ('ocr', 'OCR'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.OneToOneField(
        ResumeParseJob,
        on_delete=models.CASCADE,
        related_name='parsed_data'
    )
    raw_json = models.JSONField(help_text="Raw LLM output")
    validated_data = models.JSONField(help_text="Pydantic validated data")
    confidence_score = models.FloatField()
    extraction_method = models.CharField(max_length=20, choices=EXTRACTION_METHODS)
    llm_model = models.CharField(max_length=50)
    llm_tokens_used = models.IntegerField()
    llm_cost = models.DecimalField(max_digits=10, decimal_places=6)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'parsed_resume_data'
        indexes = [
            models.Index(fields=['confidence_score']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Parsed data for {self.job.original_filename}"

    @property
    def candidate_name(self):
        return self.validated_data.get('contact', {}).get('name', 'Unknown')

    @property
    def candidate_email(self):
        return self.validated_data.get('contact', {}).get('email', '')


class AuditLog(models.Model):
    """Audit trail for all actions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    job = models.ForeignKey(ResumeParseJob, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=50)
    details = models.JSONField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        return f"{self.action} by {self.user} at {self.timestamp}"
```

### Step 2.2: Create Migrations

```bash
# Update config/settings.py to use custom user model
AUTH_USER_MODEL = 'parser.User'

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

---

## Phase 3: Core Modules

### Step 3.1: Pydantic Schemas

**`apps/parser/schemas.py`**:

```python
from pydantic import BaseModel, EmailStr, HttpUrl, Field, validator
from typing import Optional, List


class Contact(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, regex=r'^\+?[1-9]\d{1,14}$')
    location: Optional[str] = None
    linkedin: Optional[HttpUrl] = None
    github: Optional[HttpUrl] = None
    portfolio: Optional[HttpUrl] = None

    @validator('phone')
    def normalize_phone(cls, v):
        if v:
            return v.strip().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        return v


class Experience(BaseModel):
    company: str = Field(..., min_length=2)
    title: str = Field(..., min_length=2)
    start_date: Optional[str] = Field(None, regex=r'^\d{4}-\d{2}$|^Present$')
    end_date: Optional[str] = Field(None, regex=r'^\d{4}-\d{2}$|^Present$')
    location: Optional[str] = None
    description: Optional[str] = None
    achievements: List[str] = Field(default_factory=list)

    @validator('end_date')
    def validate_dates(cls, v, values):
        if 'start_date' in values and v and v != 'Present':
            if values['start_date'] and values['start_date'] != 'Present':
                if v < values['start_date']:
                    raise ValueError('end_date must be after start_date')
        return v


class Education(BaseModel):
    institution: str = Field(..., min_length=2)
    degree: str
    field: Optional[str] = None
    start_date: Optional[str] = Field(None, regex=r'^\d{4}-\d{2}$')
    end_date: Optional[str] = Field(None, regex=r'^\d{4}-\d{2}$')
    gpa: Optional[str] = None
    location: Optional[str] = None


class Skills(BaseModel):
    technical: List[str] = Field(default_factory=list)
    soft: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)


class Certification(BaseModel):
    name: str
    issuer: str
    date: Optional[str] = Field(None, regex=r'^\d{4}-\d{2}$')
    credential_id: Optional[str] = None


class Project(BaseModel):
    name: str
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    url: Optional[HttpUrl] = None


class Language(BaseModel):
    language: str
    proficiency: str = Field(..., regex=r'^(Native|Fluent|Professional|Basic)$')


class ParsedResume(BaseModel):
    contact: Contact
    summary: Optional[str] = Field(None, max_length=1000)
    experience: List[Experience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    skills: Skills = Field(default_factory=Skills)
    certifications: List[Certification] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    languages: List[Language] = Field(default_factory=list)

    @validator('experience')
    def sort_experience_by_date(cls, v):
        return sorted(v, key=lambda x: x.start_date or '0000-00', reverse=True)

    class Config:
        schema_extra = {
            "example": {
                "contact": {
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "phone": "+1234567890",
                    "location": "San Francisco, USA"
                }
            }
        }
```

### Step 3.2: PDF Extractor

**`apps/parser/pdf_extractor.py`**:

```python
import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extract text from PDF with OCR fallback"""

    def __init__(self, ocr_threshold: int = 100):
        """
        Args:
            ocr_threshold: Minimum characters per page to consider PDF readable
        """
        self.ocr_threshold = ocr_threshold

    def extract_text(self, pdf_path: str) -> Dict:
        """
        Extract text from PDF

        Returns:
            {
                "text": str,
                "pages": int,
                "method": "pdfplumber" | "ocr",
                "confidence": float
            }
        """
        try:
            # Try pdfplumber first
            text, pages = self._extract_with_pdfplumber(pdf_path)

            # Check if enough text was extracted
            if len(text.strip()) > self.ocr_threshold:
                logger.info(f"Extracted {len(text)} chars using pdfplumber")
                return {
                    "text": text,
                    "pages": pages,
                    "method": "pdfplumber",
                    "confidence": 1.0
                }

            # Fallback to OCR
            logger.info("Text density too low, falling back to OCR")
            text = self._extract_with_ocr(pdf_path)

            return {
                "text": text,
                "pages": pages,
                "method": "ocr",
                "confidence": 0.8
            }

        except Exception as e:
            logger.error(f"PDF extraction failed: {str(e)}")
            raise

    def _extract_with_pdfplumber(self, pdf_path: str) -> tuple:
        """Extract text using pdfplumber"""
        text_parts = []

        with pdfplumber.open(pdf_path) as pdf:
            num_pages = len(pdf.pages)

            for page in pdf.pages:
                page_text = page.extract_text(
                    x_tolerance=3,
                    y_tolerance=3,
                    layout=True
                )
                if page_text:
                    text_parts.append(page_text)

        return '\n\n'.join(text_parts), num_pages

    def _extract_with_ocr(self, pdf_path: str) -> str:
        """Extract text using Tesseract OCR"""
        images = convert_from_path(pdf_path)
        text_parts = []

        for i, image in enumerate(images):
            logger.info(f"OCR processing page {i+1}/{len(images)}")
            text = pytesseract.image_to_string(image)
            text_parts.append(text)

        return '\n\n'.join(text_parts)

    def detect_scan(self, pdf_path: str) -> bool:
        """Detect if PDF is scanned/image-based"""
        with pdfplumber.open(pdf_path) as pdf:
            first_page_text = pdf.pages[0].extract_text()
            return len(first_page_text or '') < self.ocr_threshold
```

### Step 3.3: LLM Extractor

**`apps/parser/llm_extractor.py`**:

```python
import openai
import anthropic
from django.conf import settings
from typing import Dict
import json
import logging
import time

logger = logging.getLogger(__name__)


class LLMExtractor:
    """Extract structured data from resume text using LLM"""

    EXTRACTION_PROMPT = """
You are a resume parser. Extract the following information from the resume text below and return it as valid JSON.

Required JSON structure:
{
  "contact": {
    "name": "Full name",
    "email": "email@example.com",
    "phone": "+1234567890",
    "location": "City, Country",
    "linkedin": "https://linkedin.com/in/...",
    "github": "https://github.com/...",
    "portfolio": "https://..."
  },
  "summary": "Professional summary or objective (2-3 sentences)",
  "experience": [
    {
      "company": "Company name",
      "title": "Job title",
      "start_date": "YYYY-MM",
      "end_date": "YYYY-MM or Present",
      "location": "City, Country",
      "description": "Brief description",
      "achievements": ["Achievement 1", "Achievement 2"]
    }
  ],
  "education": [
    {
      "institution": "University name",
      "degree": "Degree type",
      "field": "Field of study",
      "start_date": "YYYY-MM",
      "end_date": "YYYY-MM",
      "gpa": "3.5/4.0",
      "location": "City, Country"
    }
  ],
  "skills": {
    "technical": ["Python", "JavaScript", "SQL"],
    "soft": ["Leadership", "Communication"],
    "tools": ["Git", "Docker", "AWS"]
  },
  "certifications": [
    {
      "name": "Certification name",
      "issuer": "Issuing organization",
      "date": "YYYY-MM",
      "credential_id": "ABC123"
    }
  ],
  "projects": [
    {
      "name": "Project name",
      "description": "Brief description",
      "technologies": ["Tech1", "Tech2"],
      "url": "https://..."
    }
  ],
  "languages": [
    {
      "language": "Language name",
      "proficiency": "Native/Fluent/Professional/Basic"
    }
  ]
}

CRITICAL RULES:
1. Use null for missing information - DO NOT make up data
2. Preserve original date formats, then normalize to YYYY-MM
3. Extract achievements as separate array items
4. If multiple phone numbers exist, use the primary one
5. Standardize location format: "City, Country"
6. For "Present" employment, use "Present" as end_date
7. Return ONLY valid JSON, no explanations

Resume text:
---
{resume_text}
---

Output (JSON only):
"""

    def __init__(self, provider: str = None, model: str = None):
        self.provider = provider or settings.LLM_SETTINGS['PROVIDER']
        self.model = model or settings.LLM_SETTINGS['MODEL']
        self.max_retries = settings.LLM_SETTINGS['MAX_RETRIES']
        self.timeout = settings.LLM_SETTINGS['TIMEOUT']

        if self.provider == 'openai':
            openai.api_key = settings.OPENAI_API_KEY
        elif self.provider == 'anthropic':
            self.anthropic_client = anthropic.Anthropic(
                api_key=settings.ANTHROPIC_API_KEY
            )

    def extract_structured_data(self, resume_text: str) -> Dict:
        """
        Extract structured data from resume text

        Returns: Dictionary matching ParsedResume schema
        """
        prompt = self.EXTRACTION_PROMPT.format(resume_text=resume_text)

        for attempt in range(self.max_retries):
            try:
                if self.provider == 'openai':
                    response = self._call_openai(prompt)
                elif self.provider == 'anthropic':
                    response = self._call_anthropic(prompt)
                else:
                    raise ValueError(f"Unknown provider: {self.provider}")

                # Parse JSON response
                data = json.loads(response)
                logger.info("Successfully extracted structured data")
                return data

            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode error (attempt {attempt + 1}): {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise

            except Exception as e:
                logger.error(f"LLM extraction failed (attempt {attempt + 1}): {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        response = openai.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a precise resume parser that outputs only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=settings.LLM_SETTINGS['TEMPERATURE'],
            max_tokens=settings.LLM_SETTINGS['MAX_TOKENS'],
            response_format={"type": "json_object"}  # Force JSON output
        )

        return response.choices[0].message.content

    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API"""
        response = self.anthropic_client.messages.create(
            model=self.model,
            max_tokens=settings.LLM_SETTINGS['MAX_TOKENS'],
            temperature=settings.LLM_SETTINGS['TEMPERATURE'],
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return response.content[0].text
```

### Step 3.4: Validator

**`apps/parser/validators.py`**:

```python
from typing import Dict
from pydantic import ValidationError
from .schemas import ParsedResume
import logging

logger = logging.getLogger(__name__)


class ResumeValidator:
    """Validate LLM output using Pydantic"""

    def validate(self, llm_output: Dict) -> Dict:
        """
        Validate LLM output against schema

        Returns:
            {
                "valid": bool,
                "data": ParsedResume | None,
                "errors": List[str],
                "confidence_score": float
            }
        """
        try:
            validated = ParsedResume(**llm_output)
            confidence = self._calculate_confidence(validated)

            logger.info(f"Validation successful, confidence: {confidence}")

            return {
                "valid": True,
                "data": validated,
                "errors": [],
                "confidence_score": confidence
            }

        except ValidationError as e:
            errors = [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
            logger.warning(f"Validation failed: {errors}")

            return {
                "valid": False,
                "data": None,
                "errors": errors,
                "confidence_score": 0.0
            }

    def _calculate_confidence(self, resume: ParsedResume) -> float:
        """
        Calculate confidence score based on data completeness

        Scoring:
        - Contact info complete: 30%
        - Has experience: 25%
        - Has education: 20%
        - Has skills: 15%
        - Has summary: 10%
        """
        score = 0.0

        # Contact completeness
        contact_fields = ['email', 'phone', 'location']
        filled = sum(1 for f in contact_fields if getattr(resume.contact, f))
        score += (filled / len(contact_fields)) * 0.3

        # Has experience
        if resume.experience:
            score += 0.25

        # Has education
        if resume.education:
            score += 0.2

        # Has skills
        if resume.skills.technical or resume.skills.soft:
            score += 0.15

        # Has summary
        if resume.summary:
            score += 0.1

        return round(score, 2)
```

---

## Phase 4: Celery Tasks

**`apps/parser/tasks.py`**:

```python
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import ResumeParseJob, ParsedResumeData
from .pdf_extractor import PDFExtractor
from .llm_extractor import LLMExtractor
from .validators import ResumeValidator
import logging
import requests
from decimal import Decimal

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def parse_resume_task(self, job_id: str):
    """
    Parse a single resume

    Steps:
    1. Update job status to processing
    2. Download PDF from S3
    3. Extract text
    4. Call LLM
    5. Validate
    6. Save results
    7. Update job status
    """
    try:
        job = ResumeParseJob.objects.get(id=job_id)
        job.status = 'processing'
        job.started_at = timezone.now()
        job.save()

        logger.info(f"Processing job {job_id}: {job.original_filename}")

        # Step 1: Download PDF
        pdf_path = f"/tmp/{job_id}.pdf"
        response = requests.get(job.file_url)
        with open(pdf_path, 'wb') as f:
            f.write(response.content)

        # Step 2: Extract text
        extractor = PDFExtractor()
        extraction_result = extractor.extract_text(pdf_path)

        if not extraction_result['text']:
            raise Exception("Failed to extract text from PDF")

        # Step 3: Call LLM
        llm = LLMExtractor()
        structured_data = llm.extract_structured_data(extraction_result['text'])

        # Step 4: Validate
        validator = ResumeValidator()
        validation_result = validator.validate(structured_data)

        if not validation_result['valid']:
            job.status = 'failed'
            job.error_message = f"Validation errors: {', '.join(validation_result['errors'])}"
            job.completed_at = timezone.now()
            job.processing_time = (job.completed_at - job.started_at).seconds
            job.save()
            return

        # Step 5: Save results
        ParsedResumeData.objects.create(
            job=job,
            raw_json=structured_data,
            validated_data=validation_result['data'].dict(),
            confidence_score=validation_result['confidence_score'],
            extraction_method=extraction_result['method'],
            llm_model=llm.model,
            llm_tokens_used=0,  # TODO: Get from API response
            llm_cost=Decimal('0.0006')  # Approximate
        )

        # Step 6: Update job
        job.status = 'completed'
        job.completed_at = timezone.now()
        job.processing_time = (job.completed_at - job.started_at).seconds
        job.save()

        logger.info(f"Successfully completed job {job_id}")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}")
        job.status = 'failed'
        job.error_message = str(e)
        job.completed_at = timezone.now()
        if job.started_at:
            job.processing_time = (job.completed_at - job.started_at).seconds
        job.save()

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@shared_task
def parse_batch_resumes(job_ids: list):
    """Process batch of resumes"""
    logger.info(f"Processing batch of {len(job_ids)} resumes")

    for job_id in job_ids:
        parse_resume_task.delay(job_id)


@shared_task
def cleanup_old_files():
    """Clean up old PDFs from S3"""
    cutoff = timezone.now() - timedelta(days=30)

    old_jobs = ResumeParseJob.objects.filter(
        created_at__lt=cutoff,
        status='completed'
    )

    count = 0
    for job in old_jobs:
        # TODO: Delete from S3
        # boto3.client('s3').delete_object(Bucket=..., Key=...)
        job.delete()
        count += 1

    logger.info(f"Cleaned up {count} old jobs")
```

---

## Phase 5: API Views & Serializers

### Step 5.1: DRF Serializers

**`apps/parser/serializers.py`**:

```python
from rest_framework import serializers
from .models import User, ResumeParseJob, ParsedResumeData, AuditLog


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'company', 'role', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password_confirm', 'company']

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class ResumeParseJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeParseJob
        fields = [
            'id', 'original_filename', 'file_url', 'file_size_bytes',
            'status', 'error_message', 'created_at', 'started_at',
            'completed_at', 'processing_time'
        ]
        read_only_fields = ['id', 'status', 'error_message', 'created_at',
                           'started_at', 'completed_at', 'processing_time']


class ResumeParseJobListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    candidate_name = serializers.SerializerMethodField()
    candidate_email = serializers.SerializerMethodField()
    confidence_score = serializers.SerializerMethodField()

    class Meta:
        model = ResumeParseJob
        fields = [
            'id', 'original_filename', 'status', 'created_at',
            'candidate_name', 'candidate_email', 'confidence_score'
        ]

    def get_candidate_name(self, obj):
        if hasattr(obj, 'parsed_data') and obj.parsed_data:
            return obj.parsed_data.validated_data.get('contact', {}).get('name')
        return None

    def get_candidate_email(self, obj):
        if hasattr(obj, 'parsed_data') and obj.parsed_data:
            return obj.parsed_data.validated_data.get('contact', {}).get('email')
        return None

    def get_confidence_score(self, obj):
        if hasattr(obj, 'parsed_data') and obj.parsed_data:
            return obj.parsed_data.confidence_score
        return None


class ParsedResumeDataSerializer(serializers.ModelSerializer):
    job = ResumeParseJobSerializer(read_only=True)

    class Meta:
        model = ParsedResumeData
        fields = [
            'id', 'job', 'validated_data', 'confidence_score',
            'extraction_method', 'llm_model', 'llm_tokens_used',
            'llm_cost', 'created_at'
        ]


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    priority = serializers.ChoiceField(
        choices=['normal', 'high'],
        default='normal',
        required=False
    )

    def validate_file(self, value):
        # Check file extension
        if not value.name.lower().endswith('.pdf'):
            raise serializers.ValidationError("Only PDF files are allowed")

        # Check file size (10MB max)
        max_size = 10 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("File size must be less than 10MB")

        return value


class BatchUploadSerializer(serializers.Serializer):
    files = serializers.ListField(
        child=serializers.FileField(),
        max_length=50
    )
    priority = serializers.ChoiceField(
        choices=['normal', 'high'],
        default='normal',
        required=False
    )


class ExportSerializer(serializers.Serializer):
    format = serializers.ChoiceField(choices=['csv', 'json', 'xlsx'])
    job_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True
    )
    fields = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    filters = serializers.DictField(required=False)


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'job', 'action', 'details', 'ip_address', 'timestamp']
```

### Step 5.2: API Views

**`apps/parser/views.py`**:

```python
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
import boto3
import csv
import json
import io
from uuid import uuid4

from .models import ResumeParseJob, ParsedResumeData, AuditLog
from .serializers import (
    ResumeParseJobSerializer, ResumeParseJobListSerializer,
    ParsedResumeDataSerializer, FileUploadSerializer,
    BatchUploadSerializer, ExportSerializer
)
from .tasks import parse_resume_task, parse_batch_resumes
from django.conf import settings


class IsOwnerOrAdmin(permissions.BasePermission):
    """Custom permission to allow only owners or admins"""

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        return obj.user == request.user


class ResumeUploadView(APIView):
    """Handle single file uploads"""
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticated]

    @method_decorator(ratelimit(key='user', rate='10/m', method='POST'))
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file = serializer.validated_data['file']
        priority = serializer.validated_data.get('priority', 'normal')

        # Upload to S3
        file_key = f"resumes/{request.user.id}/{uuid4()}/{file.name}"
        s3_client = boto3.client('s3')

        try:
            s3_client.upload_fileobj(
                file,
                settings.AWS_STORAGE_BUCKET_NAME,
                file_key,
                ExtraArgs={'ContentType': 'application/pdf'}
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to upload file: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        file_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{file_key}"

        # Create job record
        job = ResumeParseJob.objects.create(
            user=request.user,
            original_filename=file.name,
            file_url=file_url,
            file_size_bytes=file.size,
            status='pending'
        )

        # Log action
        AuditLog.objects.create(
            user=request.user,
            job=job,
            action='upload',
            details={'filename': file.name, 'size': file.size},
            ip_address=request.META.get('REMOTE_ADDR', '0.0.0.0'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:255]
        )

        # Queue parsing task
        parse_resume_task.delay(str(job.id))

        return Response({
            'job_id': str(job.id),
            'status': 'pending',
            'message': 'Resume queued for processing',
            'estimated_time': 15
        }, status=status.HTTP_202_ACCEPTED)


class BatchUploadView(APIView):
    """Handle batch file uploads"""
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticated]

    @method_decorator(ratelimit(key='user', rate='5/m', method='POST'))
    def post(self, request):
        serializer = BatchUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        files = serializer.validated_data['files']
        job_ids = []

        s3_client = boto3.client('s3')

        for file in files:
            # Upload each file to S3
            file_key = f"resumes/{request.user.id}/{uuid4()}/{file.name}"

            try:
                s3_client.upload_fileobj(
                    file,
                    settings.AWS_STORAGE_BUCKET_NAME,
                    file_key,
                    ExtraArgs={'ContentType': 'application/pdf'}
                )
            except Exception as e:
                continue  # Skip failed uploads

            file_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{file_key}"

            # Create job record
            job = ResumeParseJob.objects.create(
                user=request.user,
                original_filename=file.name,
                file_url=file_url,
                file_size_bytes=file.size,
                status='pending'
            )
            job_ids.append(str(job.id))

        # Queue batch processing
        if job_ids:
            parse_batch_resumes.delay(job_ids)

        return Response({
            'batch_id': str(uuid4()),
            'job_ids': job_ids,
            'total_files': len(job_ids),
            'status': 'processing',
            'estimated_time': len(job_ids) * 15
        }, status=status.HTTP_202_ACCEPTED)


class ResumeJobViewSet(viewsets.ModelViewSet):
    """ViewSet for resume parse jobs"""
    serializer_class = ResumeParseJobSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return ResumeParseJob.objects.all()
        return ResumeParseJob.objects.filter(user=user)

    def get_serializer_class(self):
        if self.action == 'list':
            return ResumeParseJobListSerializer
        return ResumeParseJobSerializer

    @action(detail=True, methods=['post'])
    def reparse(self, request, pk=None):
        """Reparse an existing resume"""
        job = self.get_object()

        # Create new job with same file
        new_job = ResumeParseJob.objects.create(
            user=request.user,
            original_filename=job.original_filename,
            file_url=job.file_url,
            file_size_bytes=job.file_size_bytes,
            status='pending'
        )

        parse_resume_task.delay(str(new_job.id))

        return Response({
            'new_job_id': str(new_job.id),
            'status': 'pending'
        }, status=status.HTTP_202_ACCEPTED)


class ParsedDataView(APIView):
    """Get parsed resume data"""
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get(self, request, data_id):
        parsed_data = get_object_or_404(ParsedResumeData, id=data_id)

        # Check permissions
        if request.user.role != 'admin' and parsed_data.job.user != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ParsedResumeDataSerializer(parsed_data)
        return Response(serializer.data)


class ExportView(APIView):
    """Export parsed resume data"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ExportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        export_format = serializer.validated_data['format']
        job_ids = serializer.validated_data.get('job_ids', [])
        fields = serializer.validated_data.get('fields', [])
        filters = serializer.validated_data.get('filters', {})

        # Get data
        queryset = ParsedResumeData.objects.filter(job__user=request.user)

        if job_ids:
            queryset = queryset.filter(job_id__in=job_ids)

        if filters.get('min_confidence'):
            queryset = queryset.filter(
                confidence_score__gte=filters['min_confidence']
            )

        data = list(queryset.values_list('validated_data', flat=True))

        # Generate export
        if export_format == 'json':
            response = HttpResponse(
                json.dumps(data, indent=2),
                content_type='application/json'
            )
            response['Content-Disposition'] = 'attachment; filename="resumes.json"'
            return response

        elif export_format == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)

            # Header
            headers = ['name', 'email', 'phone', 'location', 'skills']
            writer.writerow(headers)

            # Data rows
            for item in data:
                contact = item.get('contact', {})
                skills = item.get('skills', {})
                technical_skills = ', '.join(skills.get('technical', []))

                writer.writerow([
                    contact.get('name', ''),
                    contact.get('email', ''),
                    contact.get('phone', ''),
                    contact.get('location', ''),
                    technical_skills
                ])

            response = HttpResponse(output.getvalue(), content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="resumes.csv"'
            return response

        return Response({'error': 'Unsupported format'}, status=400)


class HealthCheckView(APIView):
    """Health check endpoint"""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({'status': 'healthy', 'version': '1.0.0'})
```

### Step 5.3: URL Configuration

**`apps/parser/urls.py`**:

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'jobs', views.ResumeJobViewSet, basename='jobs')

urlpatterns = [
    path('upload', views.ResumeUploadView.as_view(), name='upload'),
    path('batch-upload', views.BatchUploadView.as_view(), name='batch-upload'),
    path('data/<uuid:data_id>', views.ParsedDataView.as_view(), name='parsed-data'),
    path('export', views.ExportView.as_view(), name='export'),
    path('', include(router.urls)),
]
```

**`config/urls.py`**:

```python
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from apps.parser.views import HealthCheckView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health', HealthCheckView.as_view(), name='health'),

    # Authentication
    path('api/v1/auth/login', TokenObtainPairView.as_view(), name='token_obtain'),
    path('api/v1/auth/refresh', TokenRefreshView.as_view(), name='token_refresh'),

    # Resume parser API
    path('api/v1/resumes/', include('apps.parser.urls')),
]
```

---

## Phase 6: Frontend Implementation

### Step 6.1: Initialize React Project

```bash
# Create frontend directory
mkdir frontend
cd frontend

# Initialize Vite + React + TypeScript
npm create vite@latest . -- --template react-ts

# Install dependencies
npm install
npm install axios @tanstack/react-query @tanstack/react-table
npm install react-router-dom
npm install tailwindcss postcss autoprefixer
npm install react-dropzone
npm install lucide-react

# Initialize Tailwind
npx tailwindcss init -p
```

### Step 6.2: Configure Tailwind

**`frontend/tailwind.config.js`**:

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

**`frontend/src/index.css`**:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### Step 6.3: API Client

**`frontend/src/api/client.ts`**:

```typescript
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Try to refresh token
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          localStorage.setItem('access_token', response.data.access_token);
          error.config.headers.Authorization = `Bearer ${response.data.access_token}`;
          return apiClient.request(error.config);
        } catch {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;

// API functions
export const resumeApi = {
  upload: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post('/resumes/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  getJobStatus: (jobId: string) => {
    return apiClient.get(`/resumes/jobs/${jobId}`);
  },

  getParsedData: (dataId: string) => {
    return apiClient.get(`/resumes/data/${dataId}`);
  },

  listResumes: (params?: { page?: number; status?: string }) => {
    return apiClient.get('/resumes/jobs/', { params });
  },

  exportData: (format: 'csv' | 'json', jobIds?: string[]) => {
    return apiClient.post('/resumes/export', { format, job_ids: jobIds }, {
      responseType: 'blob',
    });
  },

  deleteJob: (jobId: string) => {
    return apiClient.delete(`/resumes/jobs/${jobId}`);
  },
};

export const authApi = {
  login: (email: string, password: string) => {
    return apiClient.post('/auth/login', { email, password });
  },

  refresh: (refreshToken: string) => {
    return apiClient.post('/auth/refresh', { refresh_token: refreshToken });
  },
};
```

### Step 6.4: Upload Component

**`frontend/src/components/Upload.tsx`**:

```tsx
import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload as UploadIcon, File, CheckCircle, XCircle, Loader } from 'lucide-react';
import { resumeApi } from '../api/client';

interface UploadedFile {
  file: File;
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'failed';
  jobId?: string;
  error?: string;
}

export const Upload: React.FC = () => {
  const [files, setFiles] = useState<UploadedFile[]>([]);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const newFiles: UploadedFile[] = acceptedFiles.map((file) => ({
      file,
      status: 'pending',
    }));

    setFiles((prev) => [...prev, ...newFiles]);

    // Upload each file
    for (let i = 0; i < newFiles.length; i++) {
      const fileIndex = files.length + i;

      setFiles((prev) =>
        prev.map((f, idx) =>
          idx === fileIndex ? { ...f, status: 'uploading' } : f
        )
      );

      try {
        const response = await resumeApi.upload(newFiles[i].file);
        setFiles((prev) =>
          prev.map((f, idx) =>
            idx === fileIndex
              ? { ...f, status: 'processing', jobId: response.data.job_id }
              : f
          )
        );

        // Poll for completion
        pollJobStatus(response.data.job_id, fileIndex);
      } catch (error: any) {
        setFiles((prev) =>
          prev.map((f, idx) =>
            idx === fileIndex
              ? { ...f, status: 'failed', error: error.message }
              : f
          )
        );
      }
    }
  }, [files.length]);

  const pollJobStatus = async (jobId: string, fileIndex: number) => {
    const maxAttempts = 60;
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await resumeApi.getJobStatus(jobId);
        const status = response.data.status;

        if (status === 'completed') {
          setFiles((prev) =>
            prev.map((f, idx) =>
              idx === fileIndex ? { ...f, status: 'completed' } : f
            )
          );
        } else if (status === 'failed') {
          setFiles((prev) =>
            prev.map((f, idx) =>
              idx === fileIndex
                ? { ...f, status: 'failed', error: response.data.error }
                : f
            )
          );
        } else if (attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, 2000);
        }
      } catch (error) {
        setFiles((prev) =>
          prev.map((f, idx) =>
            idx === fileIndex ? { ...f, status: 'failed', error: 'Polling failed' } : f
          )
        );
      }
    };

    poll();
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  const getStatusIcon = (status: UploadedFile['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="text-green-500" size={20} />;
      case 'failed':
        return <XCircle className="text-red-500" size={20} />;
      case 'uploading':
      case 'processing':
        return <Loader className="text-blue-500 animate-spin" size={20} />;
      default:
        return <File className="text-gray-400" size={20} />;
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
          ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}`}
      >
        <input {...getInputProps()} />
        <UploadIcon className="mx-auto text-gray-400 mb-4" size={48} />
        {isDragActive ? (
          <p className="text-blue-500">Drop the PDF files here...</p>
        ) : (
          <>
            <p className="text-gray-600">Drag & drop PDF resumes here</p>
            <p className="text-sm text-gray-400 mt-2">or click to select files</p>
          </>
        )}
      </div>

      {files.length > 0 && (
        <div className="mt-6">
          <h3 className="font-medium text-gray-700 mb-3">Uploaded Files</h3>
          <ul className="space-y-2">
            {files.map((file, index) => (
              <li
                key={index}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center space-x-3">
                  {getStatusIcon(file.status)}
                  <span className="text-sm text-gray-700">{file.file.name}</span>
                </div>
                <span className="text-xs text-gray-500 capitalize">{file.status}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
```

### Step 6.5: Resume Table Component

**`frontend/src/components/ResumeTable.tsx`**:

```tsx
import React, { useMemo, useState } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getPaginationRowModel,
  getFilteredRowModel,
  flexRender,
  ColumnDef,
  SortingState,
} from '@tanstack/react-table';
import { useQuery } from '@tanstack/react-query';
import { resumeApi } from '../api/client';
import { ChevronUp, ChevronDown, Download, Trash2, Eye } from 'lucide-react';

interface Resume {
  id: string;
  original_filename: string;
  status: string;
  created_at: string;
  candidate_name: string | null;
  candidate_email: string | null;
  confidence_score: number | null;
}

export const ResumeTable: React.FC = () => {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [globalFilter, setGlobalFilter] = useState('');

  const { data, isLoading, error } = useQuery({
    queryKey: ['resumes'],
    queryFn: () => resumeApi.listResumes().then((res) => res.data.results),
    refetchInterval: 5000, // Poll every 5 seconds
  });

  const columns = useMemo<ColumnDef<Resume>[]>(
    () => [
      {
        accessorKey: 'original_filename',
        header: 'Filename',
        cell: (info) => (
          <span className="font-medium">{info.getValue() as string}</span>
        ),
      },
      {
        accessorKey: 'candidate_name',
        header: 'Name',
        cell: (info) => info.getValue() || '-',
      },
      {
        accessorKey: 'candidate_email',
        header: 'Email',
        cell: (info) => info.getValue() || '-',
      },
      {
        accessorKey: 'status',
        header: 'Status',
        cell: (info) => {
          const status = info.getValue() as string;
          const colors: Record<string, string> = {
            completed: 'bg-green-100 text-green-800',
            processing: 'bg-blue-100 text-blue-800',
            pending: 'bg-yellow-100 text-yellow-800',
            failed: 'bg-red-100 text-red-800',
          };
          return (
            <span className={`px-2 py-1 rounded-full text-xs ${colors[status] || ''}`}>
              {status}
            </span>
          );
        },
      },
      {
        accessorKey: 'confidence_score',
        header: 'Confidence',
        cell: (info) => {
          const score = info.getValue() as number | null;
          if (!score) return '-';
          const percentage = Math.round(score * 100);
          return (
            <div className="flex items-center">
              <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                <div
                  className={`h-2 rounded-full ${
                    percentage >= 80 ? 'bg-green-500' : percentage >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${percentage}%` }}
                />
              </div>
              <span className="text-xs text-gray-600">{percentage}%</span>
            </div>
          );
        },
      },
      {
        accessorKey: 'created_at',
        header: 'Uploaded',
        cell: (info) => new Date(info.getValue() as string).toLocaleDateString(),
      },
      {
        id: 'actions',
        header: 'Actions',
        cell: ({ row }) => (
          <div className="flex space-x-2">
            <button
              className="p-1 hover:bg-gray-100 rounded"
              title="View details"
              onClick={() => handleView(row.original.id)}
            >
              <Eye size={16} />
            </button>
            <button
              className="p-1 hover:bg-gray-100 rounded"
              title="Delete"
              onClick={() => handleDelete(row.original.id)}
            >
              <Trash2 size={16} />
            </button>
          </div>
        ),
      },
    ],
    []
  );

  const table = useReactTable({
    data: data || [],
    columns,
    state: { sorting, globalFilter },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  const handleView = (id: string) => {
    // Navigate to detail view
    window.location.href = `/resumes/${id}`;
  };

  const handleDelete = async (id: string) => {
    if (confirm('Are you sure you want to delete this resume?')) {
      await resumeApi.deleteJob(id);
    }
  };

  const handleExport = async (format: 'csv' | 'json') => {
    const response = await resumeApi.exportData(format);
    const blob = new Blob([response.data], {
      type: format === 'csv' ? 'text/csv' : 'application/json',
    });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `resumes.${format}`;
    a.click();
  };

  if (isLoading) return <div className="text-center py-8">Loading...</div>;
  if (error) return <div className="text-center py-8 text-red-500">Error loading data</div>;

  return (
    <div className="w-full">
      {/* Toolbar */}
      <div className="flex justify-between items-center mb-4">
        <input
          type="text"
          placeholder="Search resumes..."
          value={globalFilter}
          onChange={(e) => setGlobalFilter(e.target.value)}
          className="px-4 py-2 border rounded-lg w-64"
        />
        <div className="flex space-x-2">
          <button
            onClick={() => handleExport('csv')}
            className="flex items-center px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
          >
            <Download size={16} className="mr-2" />
            Export CSV
          </button>
          <button
            onClick={() => handleExport('json')}
            className="flex items-center px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
          >
            <Download size={16} className="mr-2" />
            Export JSON
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto border rounded-lg">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                    onClick={header.column.getToggleSortingHandler()}
                  >
                    <div className="flex items-center">
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      {header.column.getIsSorted() === 'asc' ? (
                        <ChevronUp size={14} className="ml-1" />
                      ) : header.column.getIsSorted() === 'desc' ? (
                        <ChevronDown size={14} className="ml-1" />
                      ) : null}
                    </div>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {table.getRowModel().rows.map((row) => (
              <tr key={row.id} className="hover:bg-gray-50">
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between mt-4">
        <div className="text-sm text-gray-500">
          Showing {table.getRowModel().rows.length} of {data?.length || 0} results
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            className="px-3 py-1 border rounded disabled:opacity-50"
          >
            Previous
          </button>
          <button
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            className="px-3 py-1 border rounded disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
};
```

### Step 6.6: Main App Component

**`frontend/src/App.tsx`**:

```tsx
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Upload } from './components/Upload';
import { ResumeTable } from './components/ResumeTable';
import './index.css';

const queryClient = new QueryClient();

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-xl font-bold text-gray-800">Resume Parser</h1>
            <div className="flex space-x-4">
              <a href="/upload" className="text-gray-600 hover:text-gray-900">Upload</a>
              <a href="/resumes" className="text-gray-600 hover:text-gray-900">Resumes</a>
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-4 py-8">{children}</main>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Navigate to="/upload" replace />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/resumes" element={<ResumeTable />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
```

---

## Phase 7: Testing

### Step 7.1: Unit Tests

**`tests/test_pdf_extractor.py`**:

```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from apps.parser.pdf_extractor import PDFExtractor


class TestPDFExtractor:
    def setup_method(self):
        self.extractor = PDFExtractor()

    @patch('apps.parser.pdf_extractor.pdfplumber')
    def test_extract_text_success(self, mock_pdfplumber):
        # Mock PDF with text
        mock_page = Mock()
        mock_page.extract_text.return_value = "John Doe\njohn@example.com\nSoftware Engineer"

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)

        mock_pdfplumber.open.return_value = mock_pdf

        result = self.extractor.extract_text('/path/to/resume.pdf')

        assert result['text'] == "John Doe\njohn@example.com\nSoftware Engineer"
        assert result['method'] == 'pdfplumber'
        assert result['pages'] == 1
        assert result['confidence'] == 1.0

    @patch('apps.parser.pdf_extractor.pdfplumber')
    @patch('apps.parser.pdf_extractor.convert_from_path')
    @patch('apps.parser.pdf_extractor.pytesseract')
    def test_extract_with_ocr_fallback(self, mock_tesseract, mock_convert, mock_pdfplumber):
        # Mock PDF with minimal text (triggers OCR)
        mock_page = Mock()
        mock_page.extract_text.return_value = "ab"  # Below threshold

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)

        mock_pdfplumber.open.return_value = mock_pdf

        # Mock OCR
        mock_image = Mock()
        mock_convert.return_value = [mock_image]
        mock_tesseract.image_to_string.return_value = "OCR extracted text"

        result = self.extractor.extract_text('/path/to/scanned.pdf')

        assert result['method'] == 'ocr'
        assert result['confidence'] == 0.8
        assert 'OCR extracted text' in result['text']


class TestPDFExtractorIntegration:
    """Integration tests with real PDF files"""

    @pytest.fixture
    def sample_pdf_path(self, tmp_path):
        # Create a simple test PDF
        from reportlab.pdfgen import canvas

        pdf_path = tmp_path / "test_resume.pdf"
        c = canvas.Canvas(str(pdf_path))
        c.drawString(100, 750, "John Doe")
        c.drawString(100, 730, "john.doe@example.com")
        c.drawString(100, 710, "Software Engineer at Tech Corp")
        c.save()
        return str(pdf_path)

    def test_extract_real_pdf(self, sample_pdf_path):
        extractor = PDFExtractor()
        result = extractor.extract_text(sample_pdf_path)

        assert 'John Doe' in result['text']
        assert result['method'] == 'pdfplumber'
```

**`tests/test_llm_extractor.py`**:

```python
import pytest
from unittest.mock import Mock, patch
from apps.parser.llm_extractor import LLMExtractor


class TestLLMExtractor:
    @patch('apps.parser.llm_extractor.openai')
    @patch('apps.parser.llm_extractor.settings')
    def test_extract_structured_data_success(self, mock_settings, mock_openai):
        # Configure settings
        mock_settings.LLM_SETTINGS = {
            'PROVIDER': 'openai',
            'MODEL': 'gpt-4o-mini',
            'MAX_TOKENS': 2000,
            'TEMPERATURE': 0.1,
            'TIMEOUT': 30,
            'MAX_RETRIES': 3,
        }
        mock_settings.OPENAI_API_KEY = 'test-key'

        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        {
            "contact": {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "+1234567890"
            },
            "experience": [],
            "education": [],
            "skills": {"technical": [], "soft": [], "tools": []}
        }
        '''
        mock_openai.chat.completions.create.return_value = mock_response

        extractor = LLMExtractor(provider='openai')
        result = extractor.extract_structured_data("John Doe\njohn@example.com")

        assert result['contact']['name'] == 'John Doe'
        assert result['contact']['email'] == 'john@example.com'

    @patch('apps.parser.llm_extractor.openai')
    @patch('apps.parser.llm_extractor.settings')
    def test_extract_handles_invalid_json(self, mock_settings, mock_openai):
        mock_settings.LLM_SETTINGS = {
            'PROVIDER': 'openai',
            'MODEL': 'gpt-4o-mini',
            'MAX_TOKENS': 2000,
            'TEMPERATURE': 0.1,
            'TIMEOUT': 30,
            'MAX_RETRIES': 3,
        }
        mock_settings.OPENAI_API_KEY = 'test-key'

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = 'invalid json'
        mock_openai.chat.completions.create.return_value = mock_response

        extractor = LLMExtractor(provider='openai')

        with pytest.raises(Exception):
            extractor.extract_structured_data("resume text")
```

**`tests/test_validators.py`**:

```python
import pytest
from apps.parser.validators import ResumeValidator
from apps.parser.schemas import ParsedResume


class TestResumeValidator:
    def setup_method(self):
        self.validator = ResumeValidator()

    def test_validate_complete_resume(self):
        data = {
            "contact": {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "+1234567890",
                "location": "San Francisco, USA"
            },
            "summary": "Experienced software engineer",
            "experience": [
                {
                    "company": "Tech Corp",
                    "title": "Senior Engineer",
                    "start_date": "2020-01",
                    "end_date": "Present"
                }
            ],
            "education": [
                {
                    "institution": "MIT",
                    "degree": "B.S.",
                    "field": "Computer Science"
                }
            ],
            "skills": {
                "technical": ["Python", "Django"],
                "soft": ["Leadership"],
                "tools": ["Git"]
            }
        }

        result = self.validator.validate(data)

        assert result['valid'] is True
        assert result['confidence_score'] >= 0.9
        assert isinstance(result['data'], ParsedResume)

    def test_validate_missing_required_field(self):
        data = {
            "contact": {
                "email": "john@example.com"
                # Missing required 'name' field
            }
        }

        result = self.validator.validate(data)

        assert result['valid'] is False
        assert len(result['errors']) > 0

    def test_validate_invalid_email(self):
        data = {
            "contact": {
                "name": "John Doe",
                "email": "invalid-email"
            }
        }

        result = self.validator.validate(data)

        assert result['valid'] is False

    def test_confidence_score_calculation(self):
        # Minimal data - low confidence
        minimal_data = {
            "contact": {"name": "John Doe"}
        }

        result = self.validator.validate(minimal_data)
        assert result['confidence_score'] < 0.5

        # Complete data - high confidence
        complete_data = {
            "contact": {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "+1234567890",
                "location": "NYC"
            },
            "summary": "Engineer",
            "experience": [{"company": "Corp", "title": "Dev", "start_date": "2020-01"}],
            "education": [{"institution": "Uni", "degree": "BS"}],
            "skills": {"technical": ["Python"], "soft": [], "tools": []}
        }

        result = self.validator.validate(complete_data)
        assert result['confidence_score'] >= 0.9
```

**`tests/test_api.py`**:

```python
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from apps.parser.models import User, ResumeParseJob


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def test_user(db):
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def authenticated_client(api_client, test_user):
    api_client.force_authenticate(user=test_user)
    return api_client


class TestUploadEndpoint:
    def test_upload_requires_authentication(self, api_client):
        response = api_client.post('/api/v1/resumes/upload')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_upload_rejects_non_pdf(self, authenticated_client, tmp_path):
        # Create a non-PDF file
        test_file = tmp_path / "test.txt"
        test_file.write_text("not a pdf")

        with open(test_file, 'rb') as f:
            response = authenticated_client.post(
                '/api/v1/resumes/upload',
                {'file': f},
                format='multipart'
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestJobsEndpoint:
    @pytest.fixture
    def test_job(self, test_user):
        return ResumeParseJob.objects.create(
            user=test_user,
            original_filename='test.pdf',
            file_url='https://s3.example.com/test.pdf',
            file_size_bytes=1024,
            status='completed'
        )

    def test_list_jobs(self, authenticated_client, test_job):
        response = authenticated_client.get('/api/v1/resumes/jobs/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1

    def test_get_job_detail(self, authenticated_client, test_job):
        response = authenticated_client.get(f'/api/v1/resumes/jobs/{test_job.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['original_filename'] == 'test.pdf'

    def test_user_cannot_access_other_jobs(self, api_client, test_job, db):
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='pass123'
        )
        api_client.force_authenticate(user=other_user)

        response = api_client.get(f'/api/v1/resumes/jobs/{test_job.id}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestHealthEndpoint:
    def test_health_check(self, api_client):
        response = api_client.get('/health')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'healthy'
```

### Step 7.2: Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps --cov-report=html

# Run specific test file
pytest tests/test_pdf_extractor.py

# Run with verbose output
pytest -v

# Run tests matching pattern
pytest -k "test_upload"
```

### Step 7.3: CI/CD Configuration

**`.github/workflows/ci.yml`**:

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Tesseract OCR
        run: sudo apt-get install -y tesseract-ocr

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-django

      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
          CELERY_BROKER_URL: redis://localhost:6379/0
          SECRET_KEY: test-secret-key
          DEBUG: 'True'
        run: |
          pytest --cov=apps --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install linters
        run: |
          pip install flake8 black isort

      - name: Run linters
        run: |
          flake8 apps/ --max-line-length=100
          black --check apps/
          isort --check-only apps/
```

---

## Phase 8: Deployment

### Step 8.1: Docker Configuration

**`Dockerfile`**:

```dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Run as non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Default command
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

**`docker-compose.yml`**:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: resume_parser
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build:
      context: .
      dockerfile: Dockerfile
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
    ports:
      - "8000:8000"
    environment:
      - DEBUG=True
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/resume_parser
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY:-dev-secret-key}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - AWS_STORAGE_BUCKET_NAME=${AWS_STORAGE_BUCKET_NAME}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  celery_worker:
    build:
      context: .
      dockerfile: Dockerfile
    command: celery -A config worker -l info -c 4
    volumes:
      - .:/app
    environment:
      - DEBUG=True
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/resume_parser
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY:-dev-secret-key}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - AWS_STORAGE_BUCKET_NAME=${AWS_STORAGE_BUCKET_NAME}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  celery_beat:
    build:
      context: .
      dockerfile: Dockerfile
    command: celery -A config beat -l info
    volumes:
      - .:/app
    environment:
      - DEBUG=True
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/resume_parser
      - CELERY_BROKER_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY:-dev-secret-key}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

volumes:
  postgres_data:
  static_volume:
```

### Step 8.2: Production Docker Compose

**`docker-compose.prod.yml`**:

```yaml
version: '3.8'

services:
  api:
    image: ${DOCKER_REGISTRY}/resume-parser:${VERSION:-latest}
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
    environment:
      - DEBUG=False
      - DATABASE_URL=${DATABASE_URL}
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
      - CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND}
      - SECRET_KEY=${SECRET_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - AWS_STORAGE_BUCKET_NAME=${AWS_STORAGE_BUCKET_NAME}
      - SENTRY_DSN=${SENTRY_DSN}
    ports:
      - "8000:8000"
    restart: always
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1'
          memory: 1G

  celery_worker:
    image: ${DOCKER_REGISTRY}/resume-parser:${VERSION:-latest}
    command: celery -A config worker -l info --autoscale=10,3
    environment:
      - DEBUG=False
      - DATABASE_URL=${DATABASE_URL}
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
      - CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND}
      - SECRET_KEY=${SECRET_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - AWS_STORAGE_BUCKET_NAME=${AWS_STORAGE_BUCKET_NAME}
    restart: always
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

### Step 8.3: Deployment Scripts

**`scripts/deploy.sh`**:

```bash
#!/bin/bash
set -e

echo "Building Docker image..."
docker build -t resume-parser:latest .

echo "Running migrations..."
docker-compose exec api python manage.py migrate

echo "Collecting static files..."
docker-compose exec api python manage.py collectstatic --noinput

echo "Restarting services..."
docker-compose up -d

echo "Deployment complete!"
```

**`scripts/backup.sh`**:

```bash
#!/bin/bash
set -e

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

echo "Creating database backup..."
docker-compose exec db pg_dump -U postgres resume_parser > "${BACKUP_DIR}/db_${DATE}.sql"

echo "Compressing backup..."
gzip "${BACKUP_DIR}/db_${DATE}.sql"

echo "Cleaning old backups (keeping last 7 days)..."
find "${BACKUP_DIR}" -name "db_*.sql.gz" -mtime +7 -delete

echo "Backup complete: ${BACKUP_DIR}/db_${DATE}.sql.gz"
```

---

## Summary

This implementation guide has covered:

1. **Phase 1**: Project setup with Django, PostgreSQL, Redis
2. **Phase 2**: Database models and migrations
3. **Phase 3**: Core modules (PDF extraction, LLM integration, validation)
4. **Phase 4**: Celery task queue for async processing
5. **Phase 5**: REST API with DRF
6. **Phase 6**: React frontend with upload and table components
7. **Phase 7**: Testing with pytest
8. **Phase 8**: Docker deployment

### Next Steps

1. Review all code files
2. Run tests to ensure everything works
3. Deploy to staging environment
4. Test with real resumes
5. Monitor and optimize

### Useful Commands

```bash
# Development
python manage.py runserver
celery -A config worker -l info
npm run dev  # Frontend

# Testing
pytest --cov=apps
npm test  # Frontend

# Docker
docker-compose up -d
docker-compose logs -f api

# Production
./scripts/deploy.sh
./scripts/backup.sh
```

---

**Last Updated**: 2026-02-05
**Version**: 1.0
