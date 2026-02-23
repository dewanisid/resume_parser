# Contributing to Resume Parser

Thank you for your interest in contributing to the Resume Parser project! This document provides guidelines and instructions for contributing.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [How to Contribute](#how-to-contribute)
5. [Coding Standards](#coding-standards)
6. [Commit Guidelines](#commit-guidelines)
7. [Pull Request Process](#pull-request-process)
8. [Testing Requirements](#testing-requirements)
9. [Documentation](#documentation)
10. [Community](#community)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment. All contributors are expected to:

- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment, discrimination, or offensive comments
- Personal attacks or trolling
- Publishing others' private information
- Other conduct deemed inappropriate in a professional setting

### Enforcement

Violations may result in temporary or permanent bans. Report issues to: conduct@resumeparser.com

---

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Python 3.11+
- Node.js 18+ (for frontend)
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose
- Git

### Fork and Clone

```bash
# Fork the repository on GitHub

# Clone your fork
git clone https://github.com/YOUR_USERNAME/resume_parser.git
cd resume_parser

# Add upstream remote
git remote add upstream https://github.com/original/resume_parser.git
```

---

## Development Setup

### Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Copy environment file
cp .env.example .env

# Start services (PostgreSQL, Redis)
docker-compose up -d db redis

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver

# Start Celery worker (new terminal)
celery -A config worker -l info
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Using Docker

```bash
# Build and start all services
docker-compose up -d

# Run migrations
docker-compose exec api python manage.py migrate

# View logs
docker-compose logs -f
```

---

## How to Contribute

### Types of Contributions

We welcome various types of contributions:

1. **Bug Fixes**: Fix reported issues
2. **New Features**: Implement new functionality
3. **Documentation**: Improve or add documentation
4. **Tests**: Add or improve test coverage
5. **Performance**: Optimize existing code
6. **Refactoring**: Improve code quality

### Finding Issues

- Check [GitHub Issues](https://github.com/yourusername/resume_parser/issues)
- Look for issues labeled `good first issue` or `help wanted`
- Check the project roadmap for planned features

### Creating Issues

Before creating an issue:

1. Search existing issues to avoid duplicates
2. Use the appropriate issue template
3. Provide as much detail as possible

**Bug Report Template**:
```markdown
## Description
Brief description of the bug

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS:
- Python version:
- Browser (if applicable):

## Additional Context
Any other relevant information
```

---

## Coding Standards

### Python Style Guide

We follow PEP 8 with the following tools:

```bash
# Format code with Black
black apps/

# Sort imports with isort
isort apps/

# Lint with flake8
flake8 apps/ --max-line-length=100

# Type check with mypy (optional)
mypy apps/
```

### Key Conventions

```python
# Use descriptive variable names
parsed_resume_data = {...}  # Good
prd = {...}                 # Bad

# Use docstrings for functions
def extract_text(pdf_path: str) -> dict:
    """
    Extract text from a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Dictionary containing extracted text and metadata

    Raises:
        PDFExtractionError: If extraction fails
    """
    pass

# Use type hints
def process_resume(job_id: str, user: User) -> ParsedResumeData:
    pass

# Use constants for magic values
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
SUPPORTED_FORMATS = ['.pdf']
```

### JavaScript/TypeScript Style Guide

```bash
# Format with Prettier
npm run format

# Lint with ESLint
npm run lint
```

### Key Conventions

```typescript
// Use TypeScript interfaces
interface Resume {
  id: string;
  name: string;
  email?: string;
}

// Use descriptive names
const parsedResumes = await fetchResumes();  // Good
const data = await fetch();                   // Bad

// Use async/await over .then()
const result = await apiClient.upload(file);  // Good
apiClient.upload(file).then(r => ...);        // Avoid
```

---

## Commit Guidelines

### Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Code style (formatting, etc.) |
| `refactor` | Code refactoring |
| `test` | Adding or fixing tests |
| `chore` | Maintenance tasks |
| `perf` | Performance improvements |

### Examples

```bash
# Feature
feat(parser): add OCR fallback for scanned PDFs

# Bug fix
fix(api): handle empty file upload gracefully

# Documentation
docs(readme): update installation instructions

# With body and footer
feat(export): add Excel export support

Implement XLSX export functionality using openpyxl library.
Supports all parsed fields with formatting.

Closes #123
```

### Commit Best Practices

- Keep commits atomic (one logical change per commit)
- Write clear, concise commit messages
- Reference issue numbers when applicable
- Don't commit commented-out code
- Don't commit sensitive data

---

## Pull Request Process

### Before Submitting

1. **Sync with upstream**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow coding standards
   - Write tests
   - Update documentation

4. **Run tests locally**
   ```bash
   pytest
   npm test  # Frontend
   ```

5. **Lint your code**
   ```bash
   black apps/
   isort apps/
   flake8 apps/
   ```

### Submitting the PR

1. **Push your branch**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request on GitHub**
   - Use the PR template
   - Link related issues
   - Add appropriate labels

3. **PR Template**
   ```markdown
   ## Description
   Brief description of changes

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update

   ## How Has This Been Tested?
   Describe tests you ran

   ## Checklist
   - [ ] My code follows the style guidelines
   - [ ] I have performed a self-review
   - [ ] I have commented my code where necessary
   - [ ] I have updated the documentation
   - [ ] My changes generate no new warnings
   - [ ] I have added tests
   - [ ] All tests pass locally
   ```

### Review Process

1. Maintainers will review your PR
2. Address any requested changes
3. Once approved, a maintainer will merge
4. Delete your feature branch after merge

### PR Review Criteria

- Code follows project standards
- Tests are included and passing
- Documentation is updated
- No security vulnerabilities
- No breaking changes (unless discussed)
- CI/CD checks pass

---

## Testing Requirements

### Backend Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps --cov-report=html

# Run specific test file
pytest tests/test_pdf_extractor.py

# Run tests matching pattern
pytest -k "test_upload"
```

### Test Coverage Requirements

- New features must include tests
- Bug fixes should include regression tests
- Minimum coverage: 80%
- Critical paths must be tested

### Test Structure

```python
# tests/test_example.py
import pytest
from apps.parser.pdf_extractor import PDFExtractor


class TestPDFExtractor:
    """Tests for PDF extraction functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.extractor = PDFExtractor()

    def test_extract_text_success(self):
        """Test successful text extraction"""
        result = self.extractor.extract_text('test.pdf')
        assert result['text']
        assert result['method'] == 'pdfplumber'

    def test_extract_handles_error(self):
        """Test error handling for invalid PDF"""
        with pytest.raises(PDFExtractionError):
            self.extractor.extract_text('invalid.pdf')
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm test -- --coverage

# Run in watch mode
npm test -- --watch
```

---

## Documentation

### When to Update Documentation

- Adding new features
- Changing existing behavior
- Modifying API endpoints
- Updating configuration options
- Fixing documentation errors

### Documentation Files

| File | Purpose |
|------|---------|
| README.md | Project overview |
| TECHNICAL_DESIGN.md | Architecture and design |
| IMPLEMENTATION_GUIDE.md | Build instructions |
| docs/API.md | API reference |
| docs/DEPLOYMENT.md | Deployment guide |
| CONTRIBUTING.md | This file |

### Documentation Style

- Use clear, concise language
- Include code examples
- Keep examples up to date
- Use proper markdown formatting
- Add screenshots when helpful

---

## Community

### Communication Channels

- **GitHub Issues**: Bug reports, feature requests
- **GitHub Discussions**: Questions, ideas, general discussion
- **Email**: support@resumeparser.com

### Getting Help

1. Check existing documentation
2. Search closed issues
3. Ask in GitHub Discussions
4. Create a new issue if needed

### Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Eligible for contributor badges

---

## Quick Reference

### Common Commands

```bash
# Backend
python manage.py runserver          # Start server
python manage.py test               # Run tests
python manage.py makemigrations     # Create migrations
celery -A config worker -l info     # Start worker

# Frontend
npm run dev                         # Start dev server
npm test                            # Run tests
npm run build                       # Build for production

# Docker
docker-compose up -d                # Start services
docker-compose logs -f              # View logs
docker-compose down                 # Stop services

# Code Quality
black apps/                         # Format Python
isort apps/                         # Sort imports
flake8 apps/                        # Lint Python
npm run lint                        # Lint JavaScript
```

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation
- `refactor/description` - Code refactoring

---

## Thank You!

Thank you for contributing to Resume Parser! Your efforts help make this project better for everyone.

If you have questions about contributing, feel free to ask in GitHub Discussions.

---

**Last Updated**: 2026-02-05
