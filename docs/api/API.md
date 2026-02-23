# Resume Parser - API Documentation

## Overview

The Resume Parser API provides RESTful endpoints for uploading, processing, and retrieving parsed resume data. All endpoints return JSON responses and require authentication unless otherwise noted.

**Base URL**: `https://api.resumeparser.com/v1` (Production)
**Local Development**: `http://localhost:8000/api/v1`

---

## Authentication

### Overview

The API uses JWT (JSON Web Tokens) for authentication. Include the access token in the `Authorization` header for all protected endpoints.

```
Authorization: Bearer <access_token>
```

### Login

Authenticate and receive access/refresh tokens.

```http
POST /api/v1/auth/login
Content-Type: application/json
```

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "your_password"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

**Error Response** (401 Unauthorized):
```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid email or password"
  }
}
```

### Refresh Token

Get a new access token using a refresh token.

```http
POST /api/v1/auth/refresh
Content-Type: application/json
```

**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600
}
```

---

## Resume Endpoints

### Upload Single Resume

Upload a single PDF resume for parsing.

```http
POST /api/v1/resumes/upload
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

**Request Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file | File | Yes | PDF file (max 10MB) |
| priority | String | No | `normal` or `high` (default: `normal`) |

**cURL Example**:
```bash
curl -X POST https://api.resumeparser.com/v1/resumes/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/resume.pdf" \
  -F "priority=normal"
```

**Response** (202 Accepted):
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "pending",
  "message": "Resume queued for processing",
  "estimated_time": 15
}
```

**Error Responses**:

| Status | Code | Description |
|--------|------|-------------|
| 400 | INVALID_FILE_TYPE | Only PDF files are allowed |
| 400 | FILE_TOO_LARGE | File size exceeds 10MB limit |
| 401 | UNAUTHORIZED | Invalid or missing token |
| 413 | PAYLOAD_TOO_LARGE | Request body too large |
| 429 | RATE_LIMIT_EXCEEDED | Too many requests |

---

### Batch Upload

Upload multiple PDF resumes at once (max 50 files).

```http
POST /api/v1/resumes/batch-upload
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

**Request Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| files | File[] | Yes | Array of PDF files |
| priority | String | No | `normal` or `high` |

**cURL Example**:
```bash
curl -X POST https://api.resumeparser.com/v1/resumes/batch-upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "files=@resume1.pdf" \
  -F "files=@resume2.pdf" \
  -F "files=@resume3.pdf"
```

**Response** (202 Accepted):
```json
{
  "batch_id": "batch_abc123xyz",
  "job_ids": [
    "123e4567-e89b-12d3-a456-426614174000",
    "223e4567-e89b-12d3-a456-426614174001",
    "323e4567-e89b-12d3-a456-426614174002"
  ],
  "total_files": 3,
  "status": "processing",
  "estimated_time": 45
}
```

---

### Get Job Status

Check the status of a parsing job.

```http
GET /api/v1/resumes/jobs/{job_id}
Authorization: Bearer <token>
```

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| job_id | UUID | The job ID returned from upload |

**Response** (200 OK):
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "john_doe_resume.pdf",
  "status": "completed",
  "progress": 100,
  "created_at": "2024-01-15T10:30:00Z",
  "started_at": "2024-01-15T10:30:01Z",
  "completed_at": "2024-01-15T10:30:12Z",
  "processing_time": 11,
  "error": null,
  "result": {
    "data_id": "parsed_456def",
    "confidence_score": 0.92
  }
}
```

**Job Status Values**:

| Status | Description |
|--------|-------------|
| `pending` | Job is queued, waiting to be processed |
| `processing` | Job is currently being processed |
| `completed` | Job finished successfully |
| `failed` | Job failed (see `error` field) |

**Error Response** (404 Not Found):
```json
{
  "error": {
    "code": "JOB_NOT_FOUND",
    "message": "Job with ID 123e4567... not found"
  }
}
```

---

### Get Parsed Data

Retrieve the extracted resume data.

```http
GET /api/v1/resumes/data/{data_id}
Authorization: Bearer <token>
```

**Response** (200 OK):
```json
{
  "id": "parsed_456def",
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "confidence_score": 0.92,
  "extraction_method": "pdfplumber",
  "data": {
    "contact": {
      "name": "John Doe",
      "email": "john.doe@example.com",
      "phone": "+1234567890",
      "location": "San Francisco, USA",
      "linkedin": "https://linkedin.com/in/johndoe",
      "github": "https://github.com/johndoe",
      "portfolio": null
    },
    "summary": "Experienced software engineer with 5+ years of expertise in full-stack development, specializing in Python and React applications.",
    "experience": [
      {
        "company": "Tech Corp",
        "title": "Senior Software Engineer",
        "start_date": "2020-01",
        "end_date": "Present",
        "location": "San Francisco, USA",
        "description": "Led team of 5 engineers building microservices architecture",
        "achievements": [
          "Reduced API latency by 40%",
          "Implemented CI/CD pipeline",
          "Mentored 3 junior developers"
        ]
      },
      {
        "company": "Startup Inc",
        "title": "Software Engineer",
        "start_date": "2018-06",
        "end_date": "2019-12",
        "location": "New York, USA",
        "description": "Full-stack development using Django and React",
        "achievements": [
          "Built real-time notification system",
          "Improved test coverage from 40% to 85%"
        ]
      }
    ],
    "education": [
      {
        "institution": "Stanford University",
        "degree": "B.S.",
        "field": "Computer Science",
        "start_date": "2014-09",
        "end_date": "2018-06",
        "gpa": "3.8/4.0",
        "location": "Stanford, USA"
      }
    ],
    "skills": {
      "technical": ["Python", "JavaScript", "TypeScript", "SQL", "GraphQL"],
      "soft": ["Leadership", "Communication", "Problem Solving"],
      "tools": ["Git", "Docker", "AWS", "Kubernetes", "Jenkins"]
    },
    "certifications": [
      {
        "name": "AWS Solutions Architect",
        "issuer": "Amazon Web Services",
        "date": "2022-03",
        "credential_id": "AWS-SAA-123456"
      }
    ],
    "projects": [
      {
        "name": "Open Source CLI Tool",
        "description": "Command-line tool for data processing with 1000+ GitHub stars",
        "technologies": ["Python", "Click", "Rich"],
        "url": "https://github.com/johndoe/cli-tool"
      }
    ],
    "languages": [
      {
        "language": "English",
        "proficiency": "Native"
      },
      {
        "language": "Spanish",
        "proficiency": "Professional"
      }
    ]
  },
  "metadata": {
    "llm_model": "gpt-4o-mini",
    "tokens_used": 1250,
    "cost": 0.0025,
    "parsed_at": "2024-01-15T10:30:12Z"
  }
}
```

---

### List All Resumes

Get a paginated list of all parsed resumes.

```http
GET /api/v1/resumes/list
Authorization: Bearer <token>
```

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | Integer | 1 | Page number |
| page_size | Integer | 20 | Results per page (max 100) |
| status | String | - | Filter by status: `completed`, `failed`, `processing` |
| min_confidence | Float | - | Minimum confidence score (0.0 - 1.0) |
| search | String | - | Search in name, email, location |
| sort_by | String | created_at | Sort field: `created_at`, `confidence_score`, `name` |
| order | String | desc | Sort order: `asc` or `desc` |

**Example Request**:
```bash
curl "https://api.resumeparser.com/v1/resumes/list?status=completed&min_confidence=0.8&page=1&page_size=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response** (200 OK):
```json
{
  "total": 150,
  "page": 1,
  "page_size": 10,
  "total_pages": 15,
  "results": [
    {
      "id": "parsed_456def",
      "job_id": "123e4567-e89b-12d3-a456-426614174000",
      "filename": "john_doe_resume.pdf",
      "name": "John Doe",
      "email": "john.doe@example.com",
      "location": "San Francisco, USA",
      "confidence_score": 0.92,
      "status": "completed",
      "parsed_at": "2024-01-15T10:30:12Z"
    },
    {
      "id": "parsed_789ghi",
      "job_id": "223e4567-e89b-12d3-a456-426614174001",
      "filename": "jane_smith_resume.pdf",
      "name": "Jane Smith",
      "email": "jane.smith@example.com",
      "location": "New York, USA",
      "confidence_score": 0.88,
      "status": "completed",
      "parsed_at": "2024-01-15T11:15:30Z"
    }
  ]
}
```

---

### Export Data

Export parsed resume data in various formats.

```http
POST /api/v1/resumes/export
Content-Type: application/json
Authorization: Bearer <token>
```

**Request Body**:
```json
{
  "format": "csv",
  "job_ids": ["job_id_1", "job_id_2"],
  "fields": ["name", "email", "phone", "skills"],
  "filters": {
    "min_confidence": 0.8,
    "status": "completed"
  }
}
```

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| format | String | Yes | `csv`, `json`, or `xlsx` |
| job_ids | String[] | No | Specific job IDs (exports all if empty) |
| fields | String[] | No | Fields to include (all if empty) |
| filters | Object | No | Additional filters |

**Response** (200 OK) - For small exports:
```
Returns file directly with appropriate Content-Type header
```

**Response** (202 Accepted) - For large exports:
```json
{
  "export_id": "export_abc123",
  "status": "processing",
  "download_url": null,
  "estimated_time": 30
}
```

**Get Export Status**:
```http
GET /api/v1/resumes/exports/{export_id}
```

**Response when ready** (200 OK):
```json
{
  "export_id": "export_abc123",
  "status": "completed",
  "download_url": "https://s3.amazonaws.com/exports/file.csv",
  "expires_at": "2024-01-16T10:30:00Z",
  "file_size": 1024000
}
```

---

### Delete Resume

Delete a resume and its parsed data.

```http
DELETE /api/v1/resumes/jobs/{job_id}
Authorization: Bearer <token>
```

**Response** (204 No Content):
```
No response body
```

**Error Response** (404 Not Found):
```json
{
  "error": {
    "code": "JOB_NOT_FOUND",
    "message": "Job not found or already deleted"
  }
}
```

---

### Reparse Resume

Request a fresh parse of an existing resume.

```http
POST /api/v1/resumes/jobs/{job_id}/reparse
Content-Type: application/json
Authorization: Bearer <token>
```

**Request Body** (optional):
```json
{
  "llm_model": "gpt-4o",
  "force": true
}
```

**Response** (202 Accepted):
```json
{
  "new_job_id": "new_123xyz",
  "status": "pending",
  "message": "Resume queued for reparsing"
}
```

---

## Data Schema

### Parsed Resume Schema

The complete schema for extracted resume data:

```typescript
interface ParsedResume {
  contact: {
    name: string;          // Required, 2-100 characters
    email?: string;        // Valid email format
    phone?: string;        // E.164 format recommended
    location?: string;     // "City, Country" format
    linkedin?: string;     // Valid URL
    github?: string;       // Valid URL
    portfolio?: string;    // Valid URL
  };
  summary?: string;        // Max 1000 characters
  experience: Experience[];
  education: Education[];
  skills: {
    technical: string[];
    soft: string[];
    tools: string[];
  };
  certifications: Certification[];
  projects: Project[];
  languages: Language[];
}

interface Experience {
  company: string;         // Required
  title: string;           // Required
  start_date?: string;     // YYYY-MM format
  end_date?: string;       // YYYY-MM or "Present"
  location?: string;
  description?: string;
  achievements: string[];
}

interface Education {
  institution: string;     // Required
  degree: string;          // Required
  field?: string;
  start_date?: string;     // YYYY-MM format
  end_date?: string;       // YYYY-MM format
  gpa?: string;
  location?: string;
}

interface Certification {
  name: string;            // Required
  issuer: string;          // Required
  date?: string;           // YYYY-MM format
  credential_id?: string;
}

interface Project {
  name: string;            // Required
  description?: string;
  technologies: string[];
  url?: string;            // Valid URL
}

interface Language {
  language: string;        // Required
  proficiency: "Native" | "Fluent" | "Professional" | "Basic";
}
```

---

## Error Handling

### Error Response Format

All errors follow a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": "Additional details (optional)",
    "retry_possible": true,
    "suggestion": "How to fix the issue (optional)"
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_abc123xyz"
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Missing or invalid authentication |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `INVALID_FILE_TYPE` | 400 | Uploaded file is not a PDF |
| `FILE_TOO_LARGE` | 400 | File exceeds size limit |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `EXTRACTION_FAILED` | 500 | PDF text extraction failed |
| `LLM_ERROR` | 500 | LLM API call failed |
| `VALIDATION_ERROR` | 400 | Data validation failed |
| `SERVER_ERROR` | 500 | Internal server error |

---

## Rate Limiting

### Limits

| Tier | Requests/Minute | Parses/Day | Concurrent Jobs |
|------|-----------------|------------|-----------------|
| Free | 10 | 100 | 5 |
| Pro | 60 | Unlimited | 20 |
| Enterprise | 300 | Unlimited | 100 |

### Rate Limit Headers

All responses include rate limit information:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1634567890
```

### Handling Rate Limits

When rate limited, you'll receive:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 30
```

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded",
    "retry_after": 30
  }
}
```

**Recommendation**: Implement exponential backoff with jitter.

---

## Webhooks (Coming Soon)

Configure webhooks to receive notifications when parsing completes:

```http
POST /api/v1/webhooks
Content-Type: application/json
Authorization: Bearer <token>
```

```json
{
  "url": "https://your-server.com/webhook",
  "events": ["job.completed", "job.failed"],
  "secret": "your_webhook_secret"
}
```

**Webhook Payload**:
```json
{
  "event": "job.completed",
  "timestamp": "2024-01-15T10:30:12Z",
  "data": {
    "job_id": "123e4567-e89b-12d3-a456-426614174000",
    "status": "completed",
    "confidence_score": 0.92
  }
}
```

---

## SDK Examples

### Python

```python
import requests

class ResumeParserClient:
    def __init__(self, api_key: str, base_url: str = "https://api.resumeparser.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}"
        })

    def upload(self, file_path: str) -> dict:
        with open(file_path, 'rb') as f:
            response = self.session.post(
                f"{self.base_url}/resumes/upload",
                files={"file": f}
            )
        response.raise_for_status()
        return response.json()

    def get_status(self, job_id: str) -> dict:
        response = self.session.get(f"{self.base_url}/resumes/jobs/{job_id}")
        response.raise_for_status()
        return response.json()

    def get_parsed_data(self, data_id: str) -> dict:
        response = self.session.get(f"{self.base_url}/resumes/data/{data_id}")
        response.raise_for_status()
        return response.json()

    def wait_for_completion(self, job_id: str, timeout: int = 120) -> dict:
        import time
        start = time.time()
        while time.time() - start < timeout:
            status = self.get_status(job_id)
            if status['status'] in ['completed', 'failed']:
                return status
            time.sleep(2)
        raise TimeoutError("Job did not complete in time")

# Usage
client = ResumeParserClient("your_api_key")
result = client.upload("resume.pdf")
job = client.wait_for_completion(result['job_id'])
if job['status'] == 'completed':
    data = client.get_parsed_data(job['result']['data_id'])
    print(data['data']['contact']['name'])
```

### JavaScript

```javascript
class ResumeParserClient {
  constructor(apiKey, baseUrl = 'https://api.resumeparser.com/v1') {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
  }

  async upload(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/resumes/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`
      },
      body: formData
    });

    if (!response.ok) throw new Error(`Upload failed: ${response.status}`);
    return response.json();
  }

  async getStatus(jobId) {
    const response = await fetch(`${this.baseUrl}/resumes/jobs/${jobId}`, {
      headers: {
        'Authorization': `Bearer ${this.apiKey}`
      }
    });

    if (!response.ok) throw new Error(`Status check failed: ${response.status}`);
    return response.json();
  }

  async waitForCompletion(jobId, timeout = 120000) {
    const start = Date.now();
    while (Date.now() - start < timeout) {
      const status = await this.getStatus(jobId);
      if (['completed', 'failed'].includes(status.status)) {
        return status;
      }
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
    throw new Error('Job did not complete in time');
  }
}

// Usage
const client = new ResumeParserClient('your_api_key');
const result = await client.upload(fileInput.files[0]);
const job = await client.waitForCompletion(result.job_id);
console.log(job);
```

---

## Changelog

### v1.0.0 (2024-01-15)
- Initial API release
- Single and batch upload support
- PDF extraction with OCR fallback
- LLM-powered structured data extraction
- CSV and JSON export
- JWT authentication

---

## Support

- **Documentation**: https://docs.resumeparser.com
- **API Status**: https://status.resumeparser.com
- **Support Email**: api-support@resumeparser.com
- **GitHub Issues**: https://github.com/yourusername/resume_parser/issues

---

**Last Updated**: 2026-02-05
**API Version**: 1.0.0
