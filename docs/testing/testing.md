# Resume Parser - Testing Guide

This document provides comprehensive guidance on testing the Resume Parser application.

---

## Table of Contents

1. [Testing Overview](#testing-overview)
2. [Test Setup](#test-setup)
3. [Running Tests](#running-tests)
4. [Test Categories](#test-categories)
5. [Writing Tests](#writing-tests)
6. [Test Fixtures](#test-fixtures)
7. [Mocking](#mocking)
8. [Coverage](#coverage)
9. [CI/CD Integration](#cicd-integration)
10. [Troubleshooting](#troubleshooting)

---

## Testing Overview

### Testing Philosophy

- **Test behavior, not implementation**: Focus on what the code does, not how
- **Write tests first** (TDD) when possible
- **Keep tests fast**: Slow tests don't get run
- **Test edge cases**: Don't just test the happy path
- **Maintain test quality**: Tests are code too

### Test Pyramid

```
         /\
        /  \
       / E2E \        <- Few end-to-end tests
      /------\
     /  Integ. \      <- Some integration tests
    /------------\
   /   Unit Tests \   <- Many unit tests
  /________________\
```

### Test Coverage Goals

| Component | Target Coverage |
|-----------|-----------------|
| Core modules | 90%+ |
| API endpoints | 85%+ |
| Utilities | 80%+ |
| Overall | 80%+ |

---

## Test Setup

### Install Test Dependencies

```bash
# Install test requirements
pip install -r requirements-dev.txt

# Or install individually
pip install pytest pytest-django pytest-cov pytest-asyncio
pip install factory-boy faker
pip install responses  # For mocking HTTP
```

### Configure pytest

**`pytest.ini`**:
```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
python_files = tests.py test_*.py *_tests.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
```

**`conftest.py`**:
```python
import pytest
from rest_framework.test import APIClient
from apps.parser.models import User


@pytest.fixture
def api_client():
    """Return an API client"""
    return APIClient()


@pytest.fixture
def user(db):
    """Create a test user"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def authenticated_client(api_client, user):
    """Return an authenticated API client"""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def sample_pdf(tmp_path):
    """Create a sample PDF for testing"""
    from reportlab.pdfgen import canvas

    pdf_path = tmp_path / "test_resume.pdf"
    c = canvas.Canvas(str(pdf_path))
    c.drawString(100, 750, "John Doe")
    c.drawString(100, 730, "john.doe@example.com")
    c.drawString(100, 710, "+1234567890")
    c.drawString(100, 690, "Software Engineer at Tech Corp")
    c.save()
    return str(pdf_path)
```

---

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_pdf_extractor.py

# Run specific test class
pytest tests/test_pdf_extractor.py::TestPDFExtractor

# Run specific test function
pytest tests/test_pdf_extractor.py::TestPDFExtractor::test_extract_text_success

# Run tests matching pattern
pytest -k "pdf"
pytest -k "test_upload or test_export"

# Run tests with specific markers
pytest -m "slow"
pytest -m "not slow"

# Run and stop on first failure
pytest -x

# Run last failed tests
pytest --lf

# Run with print statements visible
pytest -s
```

### With Coverage

```bash
# Run with coverage report
pytest --cov=apps

# Generate HTML coverage report
pytest --cov=apps --cov-report=html

# Show missing lines
pytest --cov=apps --cov-report=term-missing

# Enforce minimum coverage
pytest --cov=apps --cov-fail-under=80
```

### Parallel Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest -n auto  # Auto-detect CPU cores
pytest -n 4     # Use 4 workers
```

---

## Test Categories

### Unit Tests

Test individual functions and classes in isolation.

**Location**: `tests/unit/`

```python
# tests/unit/test_validators.py
from apps.parser.validators import ResumeValidator
from apps.parser.schemas import ParsedResume


class TestResumeValidator:
    def setup_method(self):
        self.validator = ResumeValidator()

    def test_validate_complete_resume(self):
        """Test validation of complete resume data"""
        data = {
            "contact": {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "+1234567890"
            },
            "experience": [],
            "education": [],
            "skills": {"technical": [], "soft": [], "tools": []}
        }

        result = self.validator.validate(data)

        assert result['valid'] is True
        assert isinstance(result['data'], ParsedResume)

    def test_validate_missing_required_field(self):
        """Test validation fails when name is missing"""
        data = {
            "contact": {
                "email": "john@example.com"
            }
        }

        result = self.validator.validate(data)

        assert result['valid'] is False
        assert len(result['errors']) > 0

    def test_confidence_score_calculation(self):
        """Test confidence score is calculated correctly"""
        data = {
            "contact": {
                "name": "John",
                "email": "j@e.com",
                "phone": "+1",
                "location": "NYC"
            },
            "summary": "Engineer",
            "experience": [{"company": "Corp", "title": "Dev"}],
            "education": [{"institution": "Uni", "degree": "BS"}],
            "skills": {"technical": ["Python"], "soft": [], "tools": []}
        }

        result = self.validator.validate(data)

        assert result['confidence_score'] >= 0.9
```

### Integration Tests

Test interaction between components.

**Location**: `tests/integration/`

```python
# tests/integration/test_parsing_pipeline.py
import pytest
from apps.parser.pdf_extractor import PDFExtractor
from apps.parser.llm_extractor import LLMExtractor
from apps.parser.validators import ResumeValidator


class TestParsingPipeline:
    @pytest.fixture
    def extractor(self):
        return PDFExtractor()

    @pytest.fixture
    def llm(self):
        return LLMExtractor(provider='openai')

    @pytest.fixture
    def validator(self):
        return ResumeValidator()

    @pytest.mark.integration
    def test_full_parsing_pipeline(self, sample_pdf, extractor, llm, validator):
        """Test complete parsing pipeline from PDF to validated data"""
        # Step 1: Extract text
        extraction_result = extractor.extract_text(sample_pdf)
        assert extraction_result['text']

        # Step 2: Call LLM
        structured_data = llm.extract_structured_data(extraction_result['text'])
        assert 'contact' in structured_data

        # Step 3: Validate
        validation_result = validator.validate(structured_data)
        assert validation_result['valid']
        assert validation_result['confidence_score'] > 0.5
```

### API Tests

Test REST API endpoints.

**Location**: `tests/api/`

```python
# tests/api/test_upload.py
import pytest
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile


class TestUploadEndpoint:
    def test_upload_requires_authentication(self, api_client):
        """Test that upload requires authentication"""
        response = api_client.post('/api/v1/resumes/upload')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_upload_pdf_success(self, authenticated_client, sample_pdf):
        """Test successful PDF upload"""
        with open(sample_pdf, 'rb') as f:
            file = SimpleUploadedFile(
                "resume.pdf",
                f.read(),
                content_type="application/pdf"
            )

        response = authenticated_client.post(
            '/api/v1/resumes/upload',
            {'file': file},
            format='multipart'
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert 'job_id' in response.data

    def test_upload_rejects_non_pdf(self, authenticated_client):
        """Test that non-PDF files are rejected"""
        file = SimpleUploadedFile(
            "document.txt",
            b"not a pdf",
            content_type="text/plain"
        )

        response = authenticated_client.post(
            '/api/v1/resumes/upload',
            {'file': file},
            format='multipart'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_upload_rejects_large_file(self, authenticated_client):
        """Test that files over 10MB are rejected"""
        large_content = b'x' * (11 * 1024 * 1024)  # 11MB
        file = SimpleUploadedFile(
            "large.pdf",
            large_content,
            content_type="application/pdf"
        )

        response = authenticated_client.post(
            '/api/v1/resumes/upload',
            {'file': file},
            format='multipart'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestJobsEndpoint:
    @pytest.fixture
    def parse_job(self, user, db):
        from apps.parser.models import ResumeParseJob
        return ResumeParseJob.objects.create(
            user=user,
            original_filename='test.pdf',
            file_url='https://s3.example.com/test.pdf',
            file_size_bytes=1024,
            status='completed'
        )

    def test_list_jobs(self, authenticated_client, parse_job):
        """Test listing user's jobs"""
        response = authenticated_client.get('/api/v1/resumes/jobs/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1

    def test_get_job_detail(self, authenticated_client, parse_job):
        """Test getting job details"""
        response = authenticated_client.get(f'/api/v1/resumes/jobs/{parse_job.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['original_filename'] == 'test.pdf'

    def test_cannot_access_other_users_job(self, api_client, parse_job, db):
        """Test that users cannot access other users' jobs"""
        from apps.parser.models import User
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='pass123'
        )
        api_client.force_authenticate(user=other_user)

        response = api_client.get(f'/api/v1/resumes/jobs/{parse_job.id}/')

        assert response.status_code == status.HTTP_404_NOT_FOUND
```

### End-to-End Tests

Test complete user workflows.

**Location**: `tests/e2e/`

```python
# tests/e2e/test_resume_workflow.py
import pytest
import time


@pytest.mark.e2e
class TestResumeWorkflow:
    def test_complete_resume_parsing_workflow(
        self, authenticated_client, sample_pdf
    ):
        """Test complete workflow: upload -> process -> retrieve"""
        # Step 1: Upload resume
        with open(sample_pdf, 'rb') as f:
            response = authenticated_client.post(
                '/api/v1/resumes/upload',
                {'file': f},
                format='multipart'
            )

        assert response.status_code == 202
        job_id = response.data['job_id']

        # Step 2: Wait for processing (with timeout)
        max_attempts = 30
        for _ in range(max_attempts):
            response = authenticated_client.get(f'/api/v1/resumes/jobs/{job_id}/')
            if response.data['status'] in ['completed', 'failed']:
                break
            time.sleep(2)

        assert response.data['status'] == 'completed'

        # Step 3: Retrieve parsed data
        data_id = response.data['result']['data_id']
        response = authenticated_client.get(f'/api/v1/resumes/data/{data_id}')

        assert response.status_code == 200
        assert 'contact' in response.data['data']
        assert response.data['confidence_score'] > 0
```

---

## Writing Tests

### Test Naming Conventions

```python
# Good: Descriptive test names
def test_extract_text_returns_content_from_valid_pdf():
    pass

def test_validate_raises_error_when_name_missing():
    pass

def test_upload_endpoint_rejects_files_over_10mb():
    pass

# Bad: Vague names
def test_extract():
    pass

def test_validate():
    pass

def test_upload():
    pass
```

### Test Structure (AAA Pattern)

```python
def test_example():
    # Arrange - Set up test data
    extractor = PDFExtractor()
    pdf_path = '/path/to/test.pdf'

    # Act - Perform the action
    result = extractor.extract_text(pdf_path)

    # Assert - Check the results
    assert result['text'] is not None
    assert result['method'] == 'pdfplumber'
```

### Parameterized Tests

```python
import pytest

@pytest.mark.parametrize("input_phone,expected", [
    ("+1 234 567 8900", "+12345678900"),
    ("(234) 567-8900", "+12345678900"),
    ("234.567.8900", "+12345678900"),
])
def test_phone_normalization(input_phone, expected):
    result = normalize_phone(input_phone)
    assert result == expected


@pytest.mark.parametrize("status", ["pending", "processing", "completed", "failed"])
def test_job_status_values(status, parse_job):
    parse_job.status = status
    parse_job.save()
    assert parse_job.status == status
```

### Testing Exceptions

```python
import pytest

def test_extract_raises_on_invalid_pdf():
    extractor = PDFExtractor()

    with pytest.raises(PDFExtractionError) as exc_info:
        extractor.extract_text('/invalid/path.pdf')

    assert "Failed to extract" in str(exc_info.value)


def test_validate_raises_on_missing_name():
    validator = ResumeValidator()
    data = {"contact": {"email": "test@example.com"}}

    result = validator.validate(data)

    assert result['valid'] is False
    assert 'name' in str(result['errors'])
```

---

## Test Fixtures

### Factory Boy

```python
# tests/factories.py
import factory
from apps.parser.models import User, ResumeParseJob, ParsedResumeData


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'password123')


class ResumeParseJobFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ResumeParseJob

    user = factory.SubFactory(UserFactory)
    original_filename = factory.Sequence(lambda n: f'resume_{n}.pdf')
    file_url = factory.LazyAttribute(
        lambda obj: f'https://s3.example.com/{obj.original_filename}'
    )
    file_size_bytes = 1024
    status = 'pending'


class ParsedResumeDataFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ParsedResumeData

    job = factory.SubFactory(ResumeParseJobFactory)
    raw_json = {'contact': {'name': 'Test User'}}
    validated_data = {'contact': {'name': 'Test User'}}
    confidence_score = 0.85
    extraction_method = 'pdfplumber'
    llm_model = 'gpt-4o-mini'
    llm_tokens_used = 1000
    llm_cost = 0.0006
```

### Using Factories

```python
from tests.factories import UserFactory, ResumeParseJobFactory

def test_with_factories(db):
    # Create a user
    user = UserFactory()

    # Create multiple jobs
    jobs = ResumeParseJobFactory.create_batch(5, user=user)

    # Create job with specific status
    completed_job = ResumeParseJobFactory(status='completed')
```

---

## Mocking

### Mocking External APIs

```python
import responses
import pytest
from apps.parser.llm_extractor import LLMExtractor


class TestLLMExtractor:
    @responses.activate
    def test_call_openai_api(self):
        """Test OpenAI API call with mocked response"""
        responses.add(
            responses.POST,
            "https://api.openai.com/v1/chat/completions",
            json={
                "choices": [{
                    "message": {
                        "content": '{"contact": {"name": "John Doe"}}'
                    }
                }]
            },
            status=200
        )

        extractor = LLMExtractor(provider='openai')
        result = extractor.extract_structured_data("Resume text")

        assert result['contact']['name'] == 'John Doe'


class TestS3Upload:
    @pytest.fixture
    def mock_s3(self, mocker):
        """Mock boto3 S3 client"""
        mock_client = mocker.patch('boto3.client')
        mock_client.return_value.upload_fileobj.return_value = None
        return mock_client

    def test_upload_to_s3(self, mock_s3):
        from apps.parser.upload_handler import UploadHandler

        handler = UploadHandler()
        result = handler.store_file(mock_file, user_id=1)

        assert mock_s3.return_value.upload_fileobj.called
```

### Mocking with pytest-mock

```python
def test_pdf_extraction_with_mock(mocker):
    """Test PDF extraction with mocked pdfplumber"""
    mock_page = mocker.Mock()
    mock_page.extract_text.return_value = "John Doe\njohn@example.com"

    mock_pdf = mocker.Mock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = mocker.Mock(return_value=mock_pdf)
    mock_pdf.__exit__ = mocker.Mock(return_value=False)

    mocker.patch('pdfplumber.open', return_value=mock_pdf)

    extractor = PDFExtractor()
    result = extractor.extract_text('/any/path.pdf')

    assert 'John Doe' in result['text']
```

---

## Coverage

### Configuration

**`.coveragerc`**:
```ini
[run]
source = apps
omit =
    */migrations/*
    */tests/*
    */__init__.py
    */admin.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError

[html]
directory = htmlcov
```

### Viewing Coverage

```bash
# Terminal report
pytest --cov=apps --cov-report=term-missing

# HTML report
pytest --cov=apps --cov-report=html
open htmlcov/index.html

# XML report (for CI)
pytest --cov=apps --cov-report=xml
```

---

## CI/CD Integration

### GitHub Actions

**`.github/workflows/test.yml`**:
```yaml
name: Tests

on: [push, pull_request]

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
        options: --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5

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

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
          CELERY_BROKER_URL: redis://localhost:6379/0
          SECRET_KEY: test-secret-key
        run: pytest --cov=apps --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Troubleshooting

### Common Issues

#### Tests not discovering

```bash
# Check pytest can find tests
pytest --collect-only

# Ensure __init__.py exists in test directories
touch tests/__init__.py
```

#### Database errors

```bash
# Ensure database is running
pg_isready

# Create test database
createdb test_resume_parser

# Run with fresh database
pytest --create-db
```

#### Import errors

```bash
# Install package in development mode
pip install -e .

# Check PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

#### Slow tests

```bash
# Run with timing info
pytest --durations=10

# Skip slow tests
pytest -m "not slow"

# Run in parallel
pytest -n auto
```

---

## Best Practices Summary

1. **Write tests first** when possible (TDD)
2. **Keep tests focused** - one assertion per test when practical
3. **Use descriptive names** that explain what's being tested
4. **Mock external dependencies** - don't call real APIs in tests
5. **Use fixtures** for common setup
6. **Maintain test quality** - review tests like production code
7. **Run tests frequently** - before every commit
8. **Keep tests fast** - slow tests get skipped

---

**Last Updated**: 2026-02-05
