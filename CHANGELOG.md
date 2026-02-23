# Changelog

All notable changes to the Resume Parser project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- Multi-language resume support (Spanish, French, German)
- Custom field extraction configuration
- Resume scoring and ranking
- Duplicate detection
- ATS integration (Greenhouse, Lever)
- GraphQL API
- WebSocket real-time updates

---

## [1.0.0] - 2026-02-05

### Added
- Initial release of Resume Parser
- PDF upload and processing
  - Single file upload via REST API
  - Batch upload (up to 50 files)
  - Support for text-based PDFs
  - OCR fallback for scanned PDFs using Tesseract
- LLM-powered extraction
  - OpenAI GPT-4o-mini integration
  - Anthropic Claude support
  - Structured JSON output
  - Configurable prompts
- Data extraction fields
  - Contact information (name, email, phone, location, links)
  - Professional summary
  - Work experience with achievements
  - Education history
  - Skills (technical, soft, tools)
  - Certifications
  - Projects
  - Languages
- Validation system
  - Pydantic schema validation
  - Confidence scoring
  - Error reporting
- REST API
  - JWT authentication
  - Rate limiting
  - Pagination and filtering
  - Search functionality
- Export functionality
  - CSV export
  - JSON export
- Async processing
  - Celery task queue
  - Redis message broker
  - Background job processing
- Frontend application
  - React + Vite
  - File upload with drag-and-drop
  - TanStack Table for data display
  - Tailwind CSS styling
- Admin interface
  - Django Admin integration
  - Job management
  - User management
- Storage
  - AWS S3 integration
  - Cloudflare R2 support
- Deployment
  - Docker support
  - Docker Compose configuration
  - Production deployment guides
- Documentation
  - Technical design document
  - Implementation guide
  - API documentation
  - Deployment guide
  - Quick reference

### Security
- JWT token authentication
- CORS configuration
- Rate limiting (10 req/min free, 60 req/min pro)
- File type validation
- File size limits (10MB)
- Input sanitization
- SQL injection protection via Django ORM

---

## [0.2.0] - 2026-01-20 (Beta)

### Added
- Batch upload support
- CSV export functionality
- Confidence scoring system
- User authentication
- Rate limiting

### Changed
- Improved LLM prompt for better extraction accuracy
- Enhanced error handling with detailed messages
- Optimized PDF text extraction

### Fixed
- Fixed date parsing for various formats
- Fixed phone number normalization
- Fixed memory leak in Celery workers

---

## [0.1.0] - 2026-01-05 (Alpha)

### Added
- Basic PDF upload
- Single resume parsing
- OpenAI integration
- PostgreSQL storage
- Basic API endpoints
- Django Admin

### Known Issues
- OCR not implemented
- No batch processing
- Limited error handling

---

## Version History Summary

| Version | Date | Type | Highlights |
|---------|------|------|------------|
| 1.0.0 | 2026-02-05 | Release | Production-ready, full feature set |
| 0.2.0 | 2026-01-20 | Beta | Batch upload, exports, auth |
| 0.1.0 | 2026-01-05 | Alpha | Initial implementation |

---

## Migration Notes

### Upgrading to 1.0.0

1. **Database migrations**
   ```bash
   python manage.py migrate
   ```

2. **Environment variables**
   - Add `LLM_PROVIDER` and `LLM_MODEL` settings
   - Configure rate limiting settings

3. **Breaking changes**
   - API response format changed for error handling
   - Authentication switched from session to JWT

### Upgrading from 0.1.0 to 0.2.0

1. **New dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Database migrations**
   ```bash
   python manage.py migrate
   ```

3. **Configuration changes**
   - Add Celery Beat configuration
   - Configure rate limiting

---

## Release Schedule

- **Major releases** (x.0.0): Quarterly
- **Minor releases** (0.x.0): Monthly
- **Patch releases** (0.0.x): As needed

---

## Deprecation Policy

- Features are deprecated with at least one minor version notice
- Deprecated features are removed in the next major version
- Breaking changes are documented in migration notes

---

## Support Policy

| Version | Support Status | End of Support |
|---------|---------------|----------------|
| 1.0.x | Active | TBD |
| 0.2.x | Maintenance | 2026-04-01 |
| 0.1.x | End of Life | 2026-02-01 |

---

## Links

- [GitHub Releases](https://github.com/yourusername/resume_parser/releases)
- [Documentation](https://docs.resumeparser.com)
- [API Changelog](https://api.resumeparser.com/changelog)

---

**Maintained by**: Resume Parser Team
**Last Updated**: 2026-02-05
