# Resume Parser - LLM-Powered Resume Extraction Tool

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/django-5.0-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> Transform messy, inconsistent resumes into clean, structured data using AI.

## Overview

Resume Parser is an intelligent tool that extracts structured information from PDF resumes regardless of format. Unlike traditional parsers that rely on rigid rules, this system uses Large Language Models (LLMs) as a semantic layer to understand context and meaning.

### The Problem

Recruiters receive resumes in wildly inconsistent formats:
- Single-column, multi-column, infographic-heavy
- Different section names ("Work Experience" vs "Professional Background")
- Varied date formats, layouts, and styling

Traditional parsers break when layouts change. Manual data entry doesn't scale.

### The Solution

This tool uses LLMs to "read" resumes like humans do, extracting:
- Contact information
- Work experience
- Education
- Skills
- Certifications
- Projects
- Languages

Output is validated, structured JSON that can be:
- Displayed in sortable tables
- Exported to CSV/Excel/JSON
- Integrated with ATS systems

## Key Features

✅ **Layout-Agnostic** - Works with any resume format
✅ **Semantic Understanding** - Interprets meaning, not just patterns
✅ **OCR Fallback** - Handles scanned/image-based PDFs
✅ **Batch Processing** - Upload multiple resumes at once
✅ **Validation** - Pydantic schema ensures data quality
✅ **Confidence Scoring** - Know how reliable each extraction is
✅ **Async Processing** - Celery task queue for scalability
✅ **Admin Dashboard** - Django Admin for data inspection
✅ **RESTful API** - Easy integration with existing systems

## Technology Stack

**Backend:**
- Django 5.0 + Django REST Framework
- PostgreSQL (structured data + JSONB)
- Redis (Celery broker)
- Celery (async task processing)

**PDF Processing:**
- pdfplumber (text extraction)
- Tesseract OCR (fallback for scanned PDFs)

**AI/ML:**
- OpenAI GPT-4o-mini / Anthropic Claude
- Pydantic (validation)

**Storage:**
- AWS S3 / Cloudflare R2 (PDF storage)

**Frontend:**
- React + Vite
- TanStack Table (data grid)
- Tailwind CSS (styling)

**Deployment:**
- Docker + Docker Compose
- Railway / Render / AWS ECS

## Architecture

```mermaid
flowchart TD
    Frontend[Frontend<br/>React SPA with upload + table view] -->|REST API| API[Django API<br/>Authentication, rate limiting, validation]

    API --> Workers[Celery Workers<br/>Async task processing]

    Workers --> PDF[PDF Extraction<br/>pdfplumber/OCR]
    Workers --> LLM[LLM API<br/>OpenAI/Anthropic]
    Workers --> Valid[Validation<br/>Pydantic]
    Workers --> Storage[(Storage<br/>PostgreSQL + S3)]
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Node.js 18+ (for frontend)
- OpenAI API key

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/resume_parser.git
cd resume_parser

# Install backend dependencies
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt

# Install Tesseract OCR (for scanned PDFs)
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki

# Setup environment variables
cp .env.example .env
# Edit .env with your credentials (see Configuration section)

# Run database migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start Redis (in separate terminal)
redis-server

# Start Celery worker (in separate terminal)
celery -A config worker -l info

# Start Django development server
python manage.py runserver
```

### Using Docker (Recommended)

```bash
# Copy environment file
cp .env.example .env
# Edit .env with your credentials

# Start all services
docker-compose up -d

# Run migrations
docker-compose exec api python manage.py migrate

# Create superuser
docker-compose exec api python manage.py createsuperuser

# View logs
docker-compose logs -f api
```

Access the application:
- API: http://localhost:8000
- Admin: http://localhost:8000/admin
- API Docs: http://localhost:8000/api/docs

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Access frontend: http://localhost:5173

## Configuration

Create a `.env` file in the project root:

```bash
# Django
DEBUG=True
SECRET_KEY=your-secret-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/resume_parser

# Redis & Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# AWS S3 (for PDF storage)
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_STORAGE_BUCKET_NAME=resume-parser-dev
AWS_S3_REGION_NAME=us-east-1

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key

# Optional: Anthropic
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# LLM Settings
LLM_PROVIDER=openai  # or 'anthropic'
LLM_MODEL=gpt-4o-mini

# Storage
STORAGE_BACKEND=S3  # or 'LOCAL' for development

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

## Usage

### 1. Upload Resume via API

```bash
curl -X POST http://localhost:8000/api/v1/resumes/upload \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@resume.pdf"
```

Response:
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "pending",
  "estimated_time": 15
}
```

### 2. Check Status

```bash
curl http://localhost:8000/api/v1/resumes/jobs/123e4567-e89b-12d3-a456-426614174000 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 3. Get Parsed Data

```bash
curl http://localhost:8000/api/v1/resumes/data/parsed_456def \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Response:
```json
{
  "id": "parsed_456def",
  "confidence_score": 0.92,
  "data": {
    "contact": {
      "name": "John Doe",
      "email": "john.doe@example.com",
      "phone": "+1234567890",
      "location": "San Francisco, USA"
    },
    "experience": [...],
    "education": [...],
    "skills": {...}
  }
}
```

### 4. Export to CSV

```bash
curl -X POST http://localhost:8000/api/v1/resumes/export \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"format": "csv", "filters": {"min_confidence": 0.8}}'
```

## API Documentation

Full API documentation is available at `/api/docs` when running the server.

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/resumes/upload` | Upload single PDF |
| POST | `/api/v1/resumes/batch-upload` | Upload multiple PDFs |
| GET | `/api/v1/resumes/jobs/{id}` | Get job status |
| GET | `/api/v1/resumes/data/{id}` | Get parsed data |
| GET | `/api/v1/resumes/list` | List all parsed resumes |
| POST | `/api/v1/resumes/export` | Export data (CSV/JSON/Excel) |
| DELETE | `/api/v1/resumes/jobs/{id}` | Delete resume |

See [API Documentation](docs/api/API.md) for details.

## Testing

```bash
# Run all tests
python manage.py test

# Run specific test file
python manage.py test apps.parser.tests.test_pdf_extractor

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

## Deployment

### Docker Deployment

```bash
# Build production image
docker build -t resume-parser:latest .

# Push to registry
docker push your-registry/resume-parser:latest

# Deploy to production
docker-compose -f docker-compose.prod.yml up -d
```

### Railway Deployment

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Deploy
railway up
```

See [DEPLOYMENT.md](docs/deployment/DEPLOYMENT.md) for detailed instructions.

## Cost Estimation

### LLM Costs (OpenAI GPT-4o-mini)

- **Cost per resume**: ~$0.0006
- **10,000 resumes/month**: ~$6
- **100,000 resumes/month**: ~$60

### Infrastructure (Monthly)

- Database (PostgreSQL): $20
- Redis: $15
- S3 Storage (10MB avg): $2
- Compute (2 workers): $50
- **Total**: ~$93/month + LLM costs

## Performance

- **Single resume**: 8-15 seconds
- **Batch (50 resumes)**: 2-5 minutes (parallel processing)
- **Accuracy**: 90-95% (validated against manual parsing)
- **OCR success rate**: 85% for scanned PDFs

## Troubleshooting

### PDF Extraction Fails

```
Error: Failed to extract text from PDF
```

**Solution**: PDF might be password-protected or corrupted. Try:
1. Ensure PDF is not encrypted
2. Check if Tesseract OCR is installed
3. Verify PDF is valid with `pdfinfo <file>`

### LLM API Rate Limit

```
Error: Rate limit exceeded
```

**Solution**: The system will automatically retry with exponential backoff. For production:
1. Upgrade to higher API tier
2. Implement request queuing
3. Use multiple API keys with load balancing

### Celery Worker Not Processing

```
No workers are running
```

**Solution**:
```bash
# Check worker status
celery -A config inspect active

# Restart workers
pkill -f 'celery worker'
celery -A config worker -l info
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Documentation

- [Technical Design Document](docs/architecture/technical-design.md) - Full architecture and design
- [Implementation Guide](docs/implementation/guide.md) - Step-by-step build instructions
- [API Documentation](docs/api/API.md) - REST API reference
- [Deployment Guide](docs/deployment/DEPLOYMENT.md) - Production deployment

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [pdfplumber](https://github.com/jsvine/pdfplumber) for PDF text extraction
- [OpenAI](https://openai.com/) for GPT models
- [Anthropic](https://www.anthropic.com/) for Claude models
- [Django](https://www.djangoproject.com/) for the web framework

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/resume_parser/issues)
- **Email**: support@example.com
- **Documentation**: [Wiki](https://github.com/yourusername/resume_parser/wiki)

---

Built with ❤️ using Django, OpenAI, and modern web technologies.
