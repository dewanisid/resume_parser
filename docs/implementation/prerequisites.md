# Resume Parser - Knowledge Prerequisites

This document outlines all topics, technologies, and concepts a developer should understand before building this resume parser project. Items are categorized by **proficiency level** and **criticality** to help you identify knowledge gaps.

## Legend

### Proficiency Levels
- 🟢 **Beginner**: Basic understanding, can follow tutorials
- 🟡 **Intermediate**: Practical experience, can build features independently
- 🔴 **Advanced**: Deep expertise, can handle edge cases and optimize

### Criticality Levels
- ⭐⭐⭐ **CRITICAL**: Project will fail without this knowledge
- ⭐⭐ **IMPORTANT**: You'll struggle significantly without this
- ⭐ **NICE-TO-HAVE**: Helpful but can learn as you go

---

## 1. Python Fundamentals

### Core Python (⭐⭐⭐ CRITICAL)
| Topic | Proficiency | Why It Matters |
|-------|-------------|----------------|
| Python 3.11+ syntax | 🟡 Intermediate | Core language for backend |
| Object-Oriented Programming | 🟡 Intermediate | Django models, classes throughout |
| Type hints & annotations | 🟢 Beginner | Pydantic schemas, code clarity |
| Exception handling | 🟡 Intermediate | Error handling strategy |
| Context managers (`with` statements) | 🟡 Intermediate | File handling, database connections |
| Decorators | 🟡 Intermediate | Django views, Celery tasks |
| List/dict comprehensions | 🟢 Beginner | Data transformation |
| Async/await basics | 🟢 Beginner | Understanding task queues |

**Where you'll use it:**
- All backend modules
- Django models and views
- Celery task definitions
- Pydantic schemas

**Red flags if missing:**
- Can't understand Django class-based views
- Struggle with error handling in tasks
- Can't write validators or custom methods

---

## 2. Django & Django REST Framework

### Django Core (⭐⭐⭐ CRITICAL)
| Topic | Proficiency | Why It Matters |
|-------|-------------|----------------|
| Django project structure | 🟡 Intermediate | Project organization |
| Models & ORM | 🟡 Intermediate | Database schema definition |
| Migrations | 🟡 Intermediate | Database version control |
| QuerySets & database queries | 🟡 Intermediate | Data retrieval, filtering |
| Django admin | 🟢 Beginner | Quick admin interface |
| Settings & environment config | 🟡 Intermediate | Multi-environment setup |
| Django signals | 🟢 Beginner | Post-save actions |

### Django REST Framework (⭐⭐⭐ CRITICAL)
| Topic | Proficiency | Why It Matters |
|-------|-------------|----------------|
| APIView vs ViewSets | 🟡 Intermediate | API endpoint creation |
| Serializers | 🟡 Intermediate | JSON serialization/deserialization |
| Authentication (JWT, Token) | 🟡 Intermediate | User security |
| Permissions & authorization | 🟡 Intermediate | Access control |
| Request/Response objects | 🟢 Beginner | HTTP handling |
| Pagination | 🟢 Beginner | Large dataset handling |
| File uploads in DRF | 🟡 Intermediate | PDF upload handling |
| Error responses | 🟢 Beginner | API error handling |

**Where you'll use it:**
- All API endpoints
- User authentication
- Resume upload/download
- Serializing parsed data

**Red flags if missing:**
- Can't create RESTful endpoints
- Don't understand serializer validation
- Struggle with file upload handling
- Can't implement authentication

---

## 3. Database & PostgreSQL

### PostgreSQL (⭐⭐⭐ CRITICAL)
| Topic | Proficiency | Why It Matters |
|-------|-------------|----------------|
| Basic SQL (SELECT, INSERT, UPDATE) | 🟡 Intermediate | Understanding ORM queries |
| JSONB data type | 🟡 Intermediate | Storing parsed resume data |
| Indexes & performance | 🟡 Intermediate | Query optimization |
| GIN indexes for JSONB | 🔴 Advanced | Fast JSON searches |
| Transactions | 🟢 Beginner | Data consistency |
| Foreign keys & relationships | 🟡 Intermediate | Database design |
| Database migrations | 🟢 Beginner | Schema evolution |

### Django ORM (⭐⭐⭐ CRITICAL)
| Topic | Proficiency | Why It Matters |
|-------|-------------|----------------|
| Model field types | 🟡 Intermediate | Schema definition |
| JSONField usage | 🟡 Intermediate | Storing parsed data |
| Query optimization (select_related, prefetch_related) | 🟡 Intermediate | N+1 query prevention |
| Custom model methods | 🟢 Beginner | Business logic |
| Model validators | 🟡 Intermediate | Data validation |

**Where you'll use it:**
- ResumeParseJob model
- ParsedResumeData with JSONB
- User model
- Audit logging
- Querying/filtering parsed resumes

**Red flags if missing:**
- Don't know how to store JSON in database
- Can't write efficient queries
- Struggle with JSONB indexing
- Create N+1 query problems

---

## 4. Pydantic

### Pydantic (⭐⭐⭐ CRITICAL)
| Topic | Proficiency | Why It Matters |
|-------|-------------|----------------|
| BaseModel classes | 🟡 Intermediate | Schema definition |
| Field validators | 🟡 Intermediate | Data validation |
| Custom validators (@validator) | 🟡 Intermediate | Complex validation logic |
| Type coercion | 🟢 Beginner | Automatic type conversion |
| Nested models | 🟡 Intermediate | Complex data structures |
| Optional fields | 🟢 Beginner | Missing data handling |
| Model serialization (.dict(), .json()) | 🟢 Beginner | Data export |
| ValidationError handling | 🟡 Intermediate | Error management |

**Where you'll use it:**
- Validating LLM outputs
- Resume schema definition
- Confidence score calculation
- Data normalization

**Red flags if missing:**
- Can't validate LLM outputs
- Don't understand schema design
- Can't handle missing fields
- Struggle with nested data validation

---

## 5. PDF Processing

### pdfplumber (⭐⭐⭐ CRITICAL)
| Topic | Proficiency | Why It Matters |
|-------|-------------|----------------|
| Opening PDFs | 🟢 Beginner | Basic extraction |
| Text extraction with layout | 🟡 Intermediate | Maintaining structure |
| Table extraction | 🟢 Beginner | Structured data |
| Detecting text density | 🟡 Intermediate | Scan detection |
| Character-level extraction | 🔴 Advanced | Complex layouts |

### Tesseract OCR (⭐⭐ IMPORTANT)
| Topic | Proficiency | Why It Matters |
|-------|-------------|----------------|
| Basic OCR usage | 🟢 Beginner | Scanned PDF handling |
| pytesseract Python wrapper | 🟢 Beginner | Python integration |
| pdf2image conversion | 🟢 Beginner | PDF to image |
| OCR accuracy limitations | 🟢 Beginner | Setting expectations |

**Where you'll use it:**
- PDFExtractor module
- Text-based vs scanned PDF detection
- Fallback extraction strategy

**Red flags if missing:**
- Can't extract text from PDFs
- Don't understand layout preservation
- Can't handle scanned PDFs
- Struggle with multi-column layouts

---

## 6. LLM Integration

### OpenAI API (⭐⭐⭐ CRITICAL)
| Topic | Proficiency | Why It Matters |
|-------|-------------|----------------|
| API authentication | 🟢 Beginner | Making requests |
| Chat completions API | 🟡 Intermediate | Sending prompts |
| System vs user messages | 🟡 Intermediate | Prompt engineering |
| Temperature parameter | 🟢 Beginner | Output consistency |
| Token counting | 🟡 Intermediate | Cost estimation |
| Error handling (rate limits, timeouts) | 🟡 Intermediate | Reliability |
| Streaming responses | 🟢 Beginner | Not used here, but good to know |

### Prompt Engineering (⭐⭐⭐ CRITICAL)
| Topic | Proficiency | Why It Matters |
|-------|-------------|----------------|
| Clear instruction writing | 🟡 Intermediate | Getting good outputs |
| Few-shot examples | 🟢 Beginner | Improving accuracy |
| Output format specification | 🟡 Intermediate | JSON structure enforcement |
| Handling null values | 🟡 Intermediate | Missing data |
| Prompt injection prevention | 🟡 Intermediate | Security |

### LLM Limitations (⭐⭐ IMPORTANT)
| Topic | Proficiency | Why It Matters |
|-------|-------------|----------------|
| Hallucinations | 🟡 Intermediate | Why validation matters |
| Context window limits | 🟢 Beginner | Long resume handling |
| Inconsistent outputs | 🟡 Intermediate | Why validation matters |
| Cost considerations | 🟡 Intermediate | Model selection |

**Where you'll use it:**
- LLMExtractor module
- Prompt template design
- Error handling and retries
- Cost optimization

**Red flags if missing:**
- Can't write effective prompts
- Don't understand token limits
- Can't handle API errors
- Don't validate LLM outputs

---

## 7. Celery & Async Processing

### Celery (⭐⭐⭐ CRITICAL)
| Topic | Proficiency | Why It Matters |
|-------|-------------|----------------|
| Task definition with @shared_task | 🟡 Intermediate | Creating async tasks |
| Task states (PENDING, STARTED, SUCCESS, FAILURE) | 🟡 Intermediate | Job status tracking |
| Task retry logic | 🟡 Intermediate | Handling failures |
| Task routing | 🟢 Beginner | Worker organization |
| Celery Beat (scheduled tasks) | 🟡 Intermediate | Periodic cleanup |
| Task timeouts | 🟢 Beginner | Preventing hangs |
| Task result backends | 🟢 Beginner | Storing results |

### Redis (⭐⭐ IMPORTANT)
| Topic | Proficiency | Why It Matters |
|-------|-------------|----------------|
| Redis as message broker | 🟢 Beginner | Task queue |
| Redis as result backend | 🟢 Beginner | Task results |
| Connection management | 🟢 Beginner | Configuration |
| Redis CLI basics | 🟢 Beginner | Debugging |

### Async Concepts (⭐⭐ IMPORTANT)
| Topic | Proficiency | Why It Matters |
|-------|-------------|----------------|
| Synchronous vs asynchronous | 🟢 Beginner | Architecture understanding |
| Message queues | 🟡 Intermediate | How Celery works |
| Worker pools | 🟡 Intermediate | Concurrency |
| Task prioritization | 🟢 Beginner | High-priority jobs |

**Where you'll use it:**
- parse_resume_task
- Batch processing
- Cleanup tasks
- Status polling

**Red flags if missing:**
- Don't understand why async is needed
- Can't debug stuck tasks
- Struggle with retry logic
- Can't scale workers

---

## 8. AWS Services

### AWS S3 (⭐⭐⭐ CRITICAL)
| Topic | Proficiency | Why It Matters |
|-------|-------------|----------------|
| Buckets & objects | 🟢 Beginner | File storage |
| boto3 Python SDK | 🟡 Intermediate | Upload/download |
| Presigned URLs | 🟡 Intermediate | Secure downloads |
| Access control (IAM policies) | 🟡 Intermediate | Security |
| Storage classes | 🟢 Beginner | Cost optimization |
| Lifecycle policies | 🟢 Beginner | Auto-deletion |

### Alternative: Cloudflare R2 (⭐⭐ IMPORTANT)
| Topic | Proficiency | Why It Matters |
|-------|-------------|----------------|
| S3-compatible API | 🟢 Beginner | Alternative storage |
| R2 pricing model | 🟢 Beginner | Cost comparison |

**Where you'll use it:**
- PDF file storage
- Export file storage
- File cleanup

**Red flags if missing:**
- Can't upload/download files programmatically
- Don't understand bucket permissions
- Can't generate secure download URLs
- Security vulnerabilities with public access

---

## 9. Security

### Application Security (⭐⭐⭐ CRITICAL)
| Topic | Proficiency | Why It Matters |
|-------|-------------|----------------|
| Authentication vs Authorization | 🟡 Intermediate | User access |
| JWT tokens | 🟡 Intermediate | API authentication |
| Password hashing | 🟢 Beginner | User security |
| File upload validation | 🟡 Intermediate | Preventing malicious files |
| Magic byte validation | 🟡 Intermediate | File type verification |
| Input sanitization | 🟡 Intermediate | XSS/injection prevention |
| SQL injection prevention | 🟢 Beginner | Django ORM handles this |
| Rate limiting | 🟡 Intermediate | DDoS prevention |
| CORS configuration | 🟡 Intermediate | Frontend integration |

### LLM Security (⭐⭐ IMPORTANT)
| Topic | Proficiency | Why It Matters |
|-------|-------------|----------------|
| Prompt injection attacks | 🟡 Intermediate | Resume manipulation |
| Output validation | 🟡 Intermediate | Preventing hallucinations |
| API key management | 🟡 Intermediate | Credential security |

### Data Privacy (⭐⭐ IMPORTANT)
| Topic | Proficiency | Why It Matters |
|-------|-------------|----------------|
| PII handling | 🟡 Intermediate | Resume data is sensitive |
| GDPR compliance basics | 🟢 Beginner | Right to deletion |
| Data encryption (at rest, in transit) | 🟡 Intermediate | Security requirements |

**Where you'll use it:**
- File upload handler
- API authentication
- User data deletion
- Access control

**Red flags if missing:**
- Accept any file type
- Don't validate file contents
- Store passwords in plaintext
- Don't sanitize user inputs
- Allow unauthorized access

---

## 10. Frontend (React)

### React Basics (⭐⭐ IMPORTANT)
| Topic | Proficiency | Why It Matters |
|-------|-------------|----------------|
| JSX syntax | 🟢 Beginner | Component writing |
| useState, useEffect | 🟡 Intermediate | State management |
| Component composition | 🟢 Beginner | UI building |
| Props & prop drilling | 🟢 Beginner | Data passing |
| Event handling | 🟢 Beginner | User interactions |
| Conditional rendering | 🟢 Beginner | UI logic |

### Advanced React (⭐⭐ IMPORTANT)
| Topic | Proficiency | Why It Matters |
|-------|-------------|----------------|
| React Query / TanStack Query | 🟡 Intermediate | API data fetching |
| File upload handling | 🟡 Intermediate | Resume upload UI |
| Table libraries (TanStack Table) | 🟡 Intermediate | Resume results display |
| Form handling | 🟡 Intermediate | Upload forms |
| Error boundaries | 🟢 Beginner | Error handling |

### TypeScript (⭐⭐ IMPORTANT)
| Topic | Proficiency | Why It Matters |
|-------|-------------|----------------|
| Basic types | 🟢 Beginner | Type safety |
| Interfaces | 🟢 Beginner | API response types |
| Type inference | 🟢 Beginner | Less typing |
| Generics | 🟡 Intermediate | Reusable components |

**Where you'll use it:**
- Upload interface
- Resume results table
- Export functionality
- Job status polling

**Red flags if missing:**
- Can't build file upload UI
- Don't understand API integration
- Can't display tabular data
- No error handling

---

## 11. Docker & Deployment

### Docker (⭐⭐⭐ CRITICAL)
| Topic | Proficiency | Why It Matters |
|-------|-------------|----------------|
| Dockerfile syntax | 🟡 Intermediate | Container building |
| Docker Compose | 🟡 Intermediate | Multi-service orchestration |
| Container networking | 🟡 Intermediate | Service communication |
| Volume mounting | 🟡 Intermediate | Data persistence |
| Environment variables | 🟢 Beginner | Configuration |
| Multi-stage builds | 🟡 Intermediate | Image optimization |

### Deployment (⭐⭐ IMPORTANT)
| Topic | Proficiency | Why It Matters |
|-------|-------------|----------------|
| Environment separation (dev/staging/prod) | 🟡 Intermediate | Proper deployment |
| Health checks | 🟢 Beginner | Monitoring |
| Log aggregation | 🟡 Intermediate | Debugging |
| Zero-downtime deployments | 🔴 Advanced | Production stability |

### Platform-Specific (⭐ NICE-TO-HAVE)
| Topic | Proficiency | Why It Matters |
|-------|-------------|----------------|
| Railway deployment | 🟢 Beginner | Easy hosting |
| Render deployment | 🟢 Beginner | Alternative hosting |
| AWS ECS | 🔴 Advanced | Scalable hosting |

**Where you'll use it:**
- Local development environment
- Production deployment
- CI/CD pipeline

**Red flags if missing:**
- Can't run project locally
- Don't understand service dependencies
- Can't debug container issues
- Deployment failures

---

## 12. Testing

### Testing Fundamentals (⭐⭐ IMPORTANT)
| Topic | Proficiency | Why It Matters |
|-------|-------------|----------------|
| Unit testing concepts | 🟡 Intermediate | Component testing |
| Integration testing | 🟡 Intermediate | End-to-end flows |
| Mocking & patching | 🟡 Intermediate | Isolating tests |
| Test fixtures | 🟢 Beginner | Test data |

### Python Testing (⭐⭐ IMPORTANT)
| Topic | Proficiency | Why It Matters |
|-------|-------------|----------------|
| pytest basics | 🟡 Intermediate | Test runner |
| Django test client | 🟡 Intermediate | API testing |
| Factory Boy | 🟢 Beginner | Test data generation |
| Coverage.py | 🟢 Beginner | Code coverage |

**Where you'll use it:**
- PDF extractor tests
- LLM extractor tests
- API endpoint tests
- Validator tests

**Red flags if missing:**
- No tests written
- Can't mock external APIs
- Don't test edge cases
- No CI/CD validation

---

## 13. Monitoring & Observability

### Error Tracking (⭐⭐ IMPORTANT)
| Topic | Proficiency | Why It Matters |
|-------|-------------|----------------|
| Sentry integration | 🟢 Beginner | Error tracking |
| Error context capture | 🟢 Beginner | Debugging |
| Error alerting | 🟢 Beginner | Quick response |

### Logging (⭐⭐ IMPORTANT)
| Topic | Proficiency | Why It Matters |
|-------|-------------|----------------|
| Python logging module | 🟡 Intermediate | Structured logging |
| Log levels (DEBUG, INFO, ERROR) | 🟢 Beginner | Appropriate logging |
| Structured logging | 🟡 Intermediate | Searchable logs |

### Metrics (⭐ NICE-TO-HAVE)
| Topic | Proficiency | Why It Matters |
|-------|-------------|----------------|
| Prometheus metrics | 🔴 Advanced | System health |
| Custom metrics | 🔴 Advanced | Business insights |

**Where you'll use it:**
- Error tracking
- Performance monitoring
- Cost tracking
- Usage analytics

---

## 14. Version Control & Collaboration

### Git (⭐⭐⭐ CRITICAL)
| Topic | Proficiency | Why It Matters |
|-------|-------------|----------------|
| Basic commands (commit, push, pull) | 🟢 Beginner | Code management |
| Branching & merging | 🟡 Intermediate | Feature development |
| Resolving conflicts | 🟡 Intermediate | Team collaboration |
| .gitignore | 🟢 Beginner | Excluding files |
| Git workflows | 🟡 Intermediate | Team process |

**Red flags if missing:**
- Commit credentials to repo
- Can't resolve merge conflicts
- No branching strategy
- Lose work frequently

---

## 15. Performance & Optimization

### Backend Performance (⭐⭐ IMPORTANT)
| Topic | Proficiency | Why It Matters |
|-------|-------------|----------------|
| Database query optimization | 🟡 Intermediate | Response times |
| N+1 query problem | 🟡 Intermediate | Common pitfall |
| Caching strategies | 🟡 Intermediate | Performance |
| Connection pooling | 🟡 Intermediate | Database efficiency |
| Async task optimization | 🟡 Intermediate | Throughput |

### Cost Optimization (⭐⭐ IMPORTANT)
| Topic | Proficiency | Why It Matters |
|-------|-------------|----------------|
| LLM token counting | 🟡 Intermediate | Cost control |
| Model selection (mini vs full) | 🟡 Intermediate | Cost vs accuracy |
| S3 storage classes | 🟢 Beginner | Storage costs |
| Database connection limits | 🟡 Intermediate | Resource management |

---

## Learning Path by Role

### Backend-Focused Developer
**Must learn (in order):**
1. Django & DRF (⭐⭐⭐)
2. PostgreSQL & Django ORM (⭐⭐⭐)
3. Pydantic (⭐⭐⭐)
4. Celery (⭐⭐⭐)
5. AWS S3 (⭐⭐⭐)
6. OpenAI API (⭐⭐⭐)
7. PDF Processing (⭐⭐⭐)
8. Security (⭐⭐⭐)
9. Docker (⭐⭐⭐)

**Can learn as you go:**
- Testing
- Monitoring
- Frontend basics

### Full-Stack Developer
**Must learn (in order):**
1. All backend topics above (80% focus)
2. React basics (⭐⭐)
3. TypeScript (⭐⭐)
4. API integration (⭐⭐)
5. File upload UI (⭐⭐)

### DevOps-Focused Developer
**Must learn (in order):**
1. Docker (⭐⭐⭐)
2. AWS services (⭐⭐⭐)
3. Environment configuration (⭐⭐⭐)
4. Monitoring & logging (⭐⭐)
5. CI/CD pipelines (⭐⭐)

---

## Common Pitfalls & Blockers

### You'll Get Stuck If You Don't Know:

#### 🚨 Critical Blockers
1. **Django models & migrations** → Can't define database schema
2. **Celery task management** → Can't implement async processing
3. **Pydantic validation** → Can't validate LLM outputs
4. **S3 file operations** → Can't store/retrieve PDFs
5. **OpenAI API usage** → Can't extract data from text
6. **Django REST serializers** → Can't build API endpoints

#### ⚠️ Major Slowdowns
1. **PostgreSQL JSONB** → Struggle storing parsed data efficiently
2. **Error handling in async tasks** → Tasks fail silently
3. **File upload security** → Security vulnerabilities
4. **Docker networking** → Services can't communicate
5. **Database query optimization** → Slow API responses

#### 💡 Minor Annoyances
1. **React state management** → Clunky UI
2. **TypeScript types** → Type errors everywhere
3. **Git workflows** → Merge conflicts
4. **Logging** → Hard to debug issues

---

## Recommended Learning Resources

### Essential Courses/Docs
1. **Django**: Official Django tutorial + Django REST Framework docs
2. **Celery**: Celery documentation + Real Python Celery guide
3. **Pydantic**: Official Pydantic docs (excellent examples)
4. **OpenAI API**: OpenAI Cookbook
5. **Docker**: Docker Getting Started guide
6. **PostgreSQL**: PostgreSQL Tutorial (postgresqltutorial.com)

### Time Investment Estimates
- **If you know Django**: 2-3 weeks to learn new concepts
- **If you know Python but not Django**: 4-6 weeks
- **If you're new to Python**: 8-12 weeks

---

## Pre-Development Checklist

Before starting, ensure you can answer "yes" to:

### Environment Setup
- [ ] Can run Django projects locally
- [ ] Can connect to PostgreSQL database
- [ ] Can run Redis locally
- [ ] Can use Docker Compose
- [ ] Have OpenAI API key

### Core Knowledge
- [ ] Understand Django models & migrations
- [ ] Can build REST API endpoints with DRF
- [ ] Know how to validate data with Pydantic
- [ ] Understand async task queues conceptually
- [ ] Can upload/download files from S3
- [ ] Can call OpenAI API and get responses

### Security Awareness
- [ ] Know how to validate file uploads
- [ ] Understand authentication vs authorization
- [ ] Know basic security best practices
- [ ] Understand environment variable management

### Testing & Deployment
- [ ] Can write basic unit tests
- [ ] Understand Docker basics
- [ ] Know how to read logs for debugging

---

## Summary

### Most Critical Gaps to Address First:
1. **Django REST Framework** - Core framework
2. **Celery** - Async processing foundation
3. **Pydantic** - LLM output validation
4. **PostgreSQL JSONB** - Data storage strategy
5. **OpenAI API** - AI integration
6. **Security basics** - File upload safety

### Timeline Expectations:
- **Strong Python/Django dev**: Ready in 1-2 weeks of learning new concepts
- **Python dev, new to Django**: Ready in 4-6 weeks
- **New to Python**: Ready in 2-3 months

### Recommended Approach:
1. Build a simple Django + Celery project first
2. Practice calling OpenAI API separately
3. Learn Pydantic validation with examples
4. Then tackle this project

---

**Good luck!** 🚀 Use this as a checklist to identify what you need to learn before starting. Focus on CRITICAL items first, then IMPORTANT, then NICE-TO-HAVE.
