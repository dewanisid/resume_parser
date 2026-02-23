# Resume Parser - Quick Reference Guide

> One-page reference for key concepts, commands, and troubleshooting

---

## System Flow (30 Second Overview)

```mermaid
flowchart LR
    A[PDF Upload] --> B[S3 Storage]
    B --> C[Celery Task]
    C --> D[PDF Extract]
    D --> E[LLM API]
    E --> F[Validate]
    F --> G[Save]
    G --> H[Return JSON]
```

---

## Essential Commands

### Development

```bash
# Start all services
python manage.py runserver          # Django API (port 8000)
celery -A config worker -l info     # Celery worker
redis-server                        # Redis (port 6379)

# Database
python manage.py makemigrations     # Create migrations
python manage.py migrate            # Apply migrations
python manage.py createsuperuser    # Create admin user

# Testing
python manage.py test               # Run all tests
coverage run --source='.' manage.py test  # With coverage
```

### Docker

```bash
docker-compose up -d                # Start all services
docker-compose logs -f api          # View logs
docker-compose exec api python manage.py migrate  # Run migrations
docker-compose down                 # Stop services
```

---

## Key Configuration

### Environment Variables (.env)

```bash
# Must have
DATABASE_URL=postgresql://user:pass@host:5432/dbname
OPENAI_API_KEY=sk-...
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=bucket-name

# Optional but recommended
CELERY_BROKER_URL=redis://localhost:6379/0
LLM_PROVIDER=openai  # or 'anthropic'
LLM_MODEL=gpt-4o-mini
DEBUG=False  # For production
```

### LLM Settings

| Model | Cost (per resume) | Speed | Accuracy |
|-------|------------------|-------|----------|
| GPT-4o-mini | $0.0006 | 8-12s | 90% |
| GPT-4o | $0.005 | 15-20s | 95% |
| Claude Haiku | $0.0003 | 6-10s | 88% |
| Claude Sonnet | $0.003 | 10-15s | 93% |

---

## API Endpoints (Quick Reference)

```http
POST   /api/v1/auth/login                 # Login
POST   /api/v1/resumes/upload              # Upload PDF
POST   /api/v1/resumes/batch-upload        # Upload multiple PDFs
GET    /api/v1/resumes/jobs/{id}           # Check status
GET    /api/v1/resumes/data/{id}           # Get parsed data
GET    /api/v1/resumes/list                # List all resumes
POST   /api/v1/resumes/export              # Export data
DELETE /api/v1/resumes/jobs/{id}           # Delete resume
```

**Authentication**: Include header `Authorization: Bearer <JWT_TOKEN>`

---

## Data Schema (Simplified)

```json
{
  "contact": {
    "name": "string (required)",
    "email": "email",
    "phone": "string",
    "location": "string"
  },
  "experience": [
    {
      "company": "string",
      "title": "string",
      "start_date": "YYYY-MM",
      "end_date": "YYYY-MM or Present",
      "achievements": ["string"]
    }
  ],
  "education": [...],
  "skills": {
    "technical": ["string"],
    "soft": ["string"],
    "tools": ["string"]
  }
}
```

---

## Common Issues & Quick Fixes

### 1. PDF Extraction Fails

**Symptom**: `Failed to extract text from PDF`

**Causes**:
- Scanned/image-based PDF
- Corrupted file
- Password-protected

**Fix**:
```bash
# Check if Tesseract is installed
tesseract --version

# Install if missing
# macOS: brew install tesseract
# Ubuntu: sudo apt-get install tesseract-ocr
```

### 2. LLM API Errors

**Symptom**: `Rate limit exceeded` or `API timeout`

**Fix**:
- Check API key is valid
- Verify API quota/limits
- System will auto-retry (3x with backoff)
- Consider upgrading API tier

### 3. Celery Tasks Not Running

**Symptom**: Jobs stuck in "pending" status

**Check**:
```bash
# Is Redis running?
redis-cli ping  # Should return "PONG"

# Are workers running?
celery -A config inspect active

# Restart worker
pkill -f 'celery worker'
celery -A config worker -l info
```

### 4. Database Connection Error

**Symptom**: `Could not connect to database`

**Fix**:
```bash
# Check PostgreSQL is running
pg_isready

# Test connection
psql postgresql://user:pass@localhost:5432/dbname

# Verify DATABASE_URL in .env
```

### 5. S3 Upload Fails

**Symptom**: `Access denied` or `Invalid credentials`

**Fix**:
- Verify AWS credentials in .env
- Check IAM permissions (s3:PutObject, s3:GetObject)
- Ensure bucket exists and region is correct

### 6. Low Confidence Scores

**Symptom**: Confidence < 0.7 on most resumes

**Causes**:
- Poor quality PDFs
- Unusual resume formats
- LLM not extracting all fields

**Fix**:
- Use GPT-4o for complex resumes
- Improve LLM prompt
- Add custom validation rules

---

## Performance Optimization

### Database Queries

```python
# Bad: N+1 query problem
for job in ResumeParseJob.objects.all():
    print(job.parsed_data.confidence_score)  # Hits DB each time

# Good: Use select_related
jobs = ResumeParseJob.objects.select_related('parsed_data').all()
```

### Caching

```python
from django.core.cache import cache

# Cache parsed data for 1 hour
data = cache.get(f'resume_{job_id}')
if not data:
    data = ParsedResumeData.objects.get(job_id=job_id)
    cache.set(f'resume_{job_id}', data, 3600)
```

### Celery Workers

```bash
# Auto-scale workers based on load
celery -A config worker --autoscale=10,3  # Max 10, min 3 workers
```

---

## Monitoring & Debugging

### Check System Health

```bash
# API health
curl http://localhost:8000/health

# Celery workers
celery -A config inspect active

# Redis connection
redis-cli ping

# Database connection
python manage.py check --database default
```

### View Logs

```bash
# Django logs
tail -f /var/log/resume_parser/app.log

# Celery logs
celery -A config events

# Docker logs
docker-compose logs -f --tail=100 api
```

### Django Admin

Access: `http://localhost:8000/admin`

**Quick Actions**:
- View all parsed resumes
- Check job statuses
- Inspect failed jobs
- View audit logs
- Manual data correction

---

## Cost Management

### Estimate Monthly Costs

| Component | Usage | Monthly Cost |
|-----------|-------|--------------|
| LLM API (10K resumes) | 10,000 × $0.0006 | $6 |
| PostgreSQL | RDS t3.micro | $20 |
| Redis | ElastiCache t3.micro | $15 |
| S3 Storage | 100GB @ $0.023/GB | $2 |
| Compute | 2 ECS tasks | $50 |
| **Total** | | **~$93** |

### Reduce Costs

1. **Use cheaper LLM**: Claude Haiku is 50% cheaper
2. **Compress PDFs**: Reduce S3 storage
3. **Delete old files**: Implement 30-day retention
4. **Cache results**: Avoid re-parsing duplicates
5. **Batch processing**: More efficient than real-time

---

## Testing Checklist

### Before Deployment

- [ ] All unit tests pass
- [ ] API endpoints work (Postman/curl)
- [ ] File upload works (text & scanned PDFs)
- [ ] Celery processes tasks
- [ ] Database migrations applied
- [ ] Environment variables set
- [ ] HTTPS configured
- [ ] Error logging works (Sentry)
- [ ] Rate limiting active
- [ ] Backup strategy in place

### Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test upload endpoint (100 requests, 10 concurrent)
ab -n 100 -c 10 -H "Authorization: Bearer TOKEN" \
   -p resume.pdf -T "multipart/form-data" \
   http://localhost:8000/api/v1/resumes/upload
```

---

## Security Checklist

- [ ] DEBUG=False in production
- [ ] SECRET_KEY is random and secret
- [ ] HTTPS only (no HTTP)
- [ ] CSRF protection enabled
- [ ] Rate limiting configured
- [ ] File upload size limited (10MB)
- [ ] Input sanitization active
- [ ] SQL injection protection (ORM)
- [ ] XSS protection (React escaping)
- [ ] Passwords hashed (Django default)
- [ ] JWT tokens expire (1 hour)
- [ ] Audit logging enabled
- [ ] CORS configured properly
- [ ] API keys in environment variables (not code)

---

## Code Snippets

### Upload Resume (Python)

```python
import requests

url = "http://localhost:8000/api/v1/resumes/upload"
headers = {"Authorization": "Bearer YOUR_JWT_TOKEN"}
files = {"file": open("resume.pdf", "rb")}

response = requests.post(url, headers=headers, files=files)
print(response.json())
# {'job_id': '123-456-789', 'status': 'pending'}
```

### Check Status (JavaScript)

```javascript
async function checkStatus(jobId) {
  const response = await fetch(
    `http://localhost:8000/api/v1/resumes/jobs/${jobId}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  const data = await response.json();
  return data.status; // 'pending', 'processing', 'completed', 'failed'
}
```

### Custom LLM Prompt

```python
# In llm_extractor.py, customize prompt:
CUSTOM_PROMPT = """
Extract resume data with SPECIAL FOCUS on:
- Security clearances
- Programming languages (separate from tools)
- Publications and patents

{standard_prompt_here}
"""
```

---

## Useful Links

- **Django Docs**: https://docs.djangoproject.com/
- **DRF Docs**: https://www.django-rest-framework.org/
- **Celery Docs**: https://docs.celeryproject.org/
- **OpenAI API**: https://platform.openai.com/docs
- **pdfplumber**: https://github.com/jsvine/pdfplumber
- **Pydantic**: https://docs.pydantic.dev/

---

## Getting Help

1. **Check logs first**: Most issues show up in logs
2. **Search documentation**: TECHNICAL_DESIGN.md has details
3. **Test locally**: Use Docker to reproduce issues
4. **Minimal example**: Isolate the problem
5. **GitHub Issues**: Report bugs with logs

---

## Key Takeaways

✅ **LLMs handle layout variations** - No regex needed
✅ **Celery enables scale** - Process hundreds of resumes in parallel
✅ **Pydantic catches errors** - Validation prevents bad data
✅ **OCR is essential** - 30%+ of resumes are scanned
✅ **Confidence scores matter** - Flag low-quality extractions
✅ **Cost is predictable** - ~$0.0006 per resume + infrastructure
✅ **Admin panel is gold** - Debug extractions visually

---

**Pro Tip**: Start with GPT-4o-mini for MVP. Upgrade to GPT-4o only for resumes with confidence < 0.7.

**Remember**: Perfect is the enemy of good. Ship MVP, iterate based on real data.

---

**Last Updated**: 2026-02-05
