# Security Policy

## Overview

The Resume Parser application handles sensitive personal information (PII) from resumes. This document outlines our security practices, policies, and procedures for reporting vulnerabilities.

---

## Table of Contents

1. [Supported Versions](#supported-versions)
2. [Reporting a Vulnerability](#reporting-a-vulnerability)
3. [Security Measures](#security-measures)
4. [Data Protection](#data-protection)
5. [Compliance](#compliance)
6. [Security Best Practices](#security-best-practices)

---

## Supported Versions

| Version | Supported          | Security Updates |
|---------|--------------------|------------------|
| 1.0.x   | :white_check_mark: | Active           |
| 0.2.x   | :white_check_mark: | Critical only    |
| < 0.2   | :x:                | None             |

We recommend always using the latest version for the best security.

---

## Reporting a Vulnerability

### How to Report

**DO NOT** report security vulnerabilities through public GitHub issues.

Instead, please report them via:

1. **Email**: security@resumeparser.com
2. **Security Advisory**: [GitHub Security Advisories](https://github.com/yourusername/resume_parser/security/advisories/new)

### What to Include

- Type of vulnerability
- Full paths of affected files
- Steps to reproduce
- Proof-of-concept (if possible)
- Impact assessment
- Suggested fix (if any)

### Response Timeline

| Action | Timeline |
|--------|----------|
| Initial response | 24-48 hours |
| Triage and assessment | 72 hours |
| Fix development | 1-2 weeks |
| Security advisory | Upon fix release |

### Recognition

We acknowledge security researchers who responsibly disclose vulnerabilities:

- Credit in the security advisory
- Listing in SECURITY_ACKNOWLEDGMENTS.md
- Potential bug bounty (for critical vulnerabilities)

---

## Security Measures

### Authentication & Authorization

#### JWT Authentication
- Access tokens expire in 1 hour
- Refresh tokens expire in 7 days
- Tokens are signed with RS256
- Token rotation on refresh

```python
# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'RS256',
}
```

#### Password Security
- Minimum 8 characters required
- Passwords hashed with Argon2
- Rate limiting on login attempts
- Account lockout after 5 failed attempts

#### Permission Model
- Role-based access control (RBAC)
- Users can only access their own data
- Admin role for system management

### API Security

#### Rate Limiting
| Tier | Limit | Window |
|------|-------|--------|
| Free | 10 requests | 1 minute |
| Pro | 60 requests | 1 minute |
| Enterprise | 300 requests | 1 minute |

#### Input Validation
- All inputs validated with Pydantic
- File type validation (magic bytes, not extension)
- File size limits (10MB max)
- Content-type verification

#### CORS Configuration
```python
CORS_ALLOWED_ORIGINS = [
    "https://app.resumeparser.com",
]
CORS_ALLOW_CREDENTIALS = True
```

### Infrastructure Security

#### HTTPS/TLS
- TLS 1.2+ required
- HSTS enabled
- Strong cipher suites only

```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
ssl_prefer_server_ciphers off;
```

#### Security Headers
```python
# Django security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

#### Network Security
- Firewall rules restrict access
- VPC isolation for cloud deployments
- Private subnets for databases
- No public access to internal services

### Code Security

#### Dependency Management
- Regular dependency updates
- Automated vulnerability scanning with Dependabot
- Lock files for reproducible builds

#### Static Analysis
- Code linting with flake8
- Security scanning with Bandit
- Dependency checking with Safety

```bash
# Security scanning commands
bandit -r apps/
safety check
```

#### Secrets Management
- No secrets in code
- Environment variables for configuration
- AWS Secrets Manager for production
- .env files excluded from git

---

## Data Protection

### Data Handling

#### PII Categories
The application processes the following PII:
- Names
- Email addresses
- Phone numbers
- Addresses
- Employment history
- Education history
- Skills and certifications

#### Data Minimization
- Only collect necessary data
- Delete data when no longer needed
- 30-day retention for processed files

#### Data Encryption

**At Rest:**
- Database encryption (PostgreSQL)
- S3 server-side encryption (AES-256)
- Redis encryption (in production)

**In Transit:**
- TLS 1.2+ for all connections
- Encrypted API communications
- Encrypted database connections

### Data Access

#### Access Controls
- Role-based access
- Principle of least privilege
- Audit logging for all data access

#### Audit Logging
```python
class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50)
    details = models.JSONField()
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)
```

### Data Retention

| Data Type | Retention Period | Deletion Method |
|-----------|------------------|-----------------|
| Original PDFs | 30 days | Automatic deletion |
| Parsed data | Until user deletes | User-initiated |
| Audit logs | 1 year | Automatic archival |
| User accounts | Until account deletion | User-initiated |

### Data Subject Rights (GDPR)

#### Right to Access
Users can export their data via:
- GET /api/v1/users/me/data
- Admin panel data export

#### Right to Deletion
Users can delete their data via:
- DELETE /api/v1/users/me
- Admin panel account deletion

#### Right to Portability
Data export available in:
- JSON format
- CSV format

---

## Compliance

### GDPR Compliance

- [x] Data processing agreement available
- [x] Privacy policy published
- [x] Cookie consent implemented
- [x] Data subject rights implemented
- [x] Data breach notification procedure
- [x] DPO contact available

### SOC 2 Considerations

- [x] Access controls documented
- [x] Encryption implemented
- [x] Audit logging enabled
- [x] Incident response plan
- [x] Change management process

### OWASP Top 10 Mitigations

| Risk | Mitigation |
|------|------------|
| A01 Broken Access Control | RBAC, ownership checks |
| A02 Cryptographic Failures | TLS 1.2+, AES-256 |
| A03 Injection | Django ORM, parameterized queries |
| A04 Insecure Design | Security reviews, threat modeling |
| A05 Security Misconfiguration | Hardened defaults, security headers |
| A06 Vulnerable Components | Dependency scanning, updates |
| A07 Authentication Failures | JWT, rate limiting, MFA (planned) |
| A08 Integrity Failures | Code signing, CI/CD security |
| A09 Logging Failures | Audit logging, monitoring |
| A10 SSRF | URL validation, allowlists |

---

## Security Best Practices

### For Developers

1. **Never commit secrets**
   ```bash
   # Use pre-commit hooks
   pip install pre-commit
   pre-commit install
   ```

2. **Keep dependencies updated**
   ```bash
   pip install -U -r requirements.txt
   npm audit fix
   ```

3. **Run security scans**
   ```bash
   bandit -r apps/
   safety check
   ```

4. **Use parameterized queries**
   ```python
   # Good
   User.objects.filter(email=email)

   # Bad
   User.objects.raw(f"SELECT * FROM users WHERE email = '{email}'")
   ```

5. **Validate all inputs**
   ```python
   from pydantic import BaseModel, EmailStr

   class UserInput(BaseModel):
       email: EmailStr
       name: str = Field(..., min_length=2, max_length=100)
   ```

### For Operators

1. **Use strong passwords for all services**
2. **Enable MFA for admin accounts**
3. **Keep systems patched and updated**
4. **Monitor logs for suspicious activity**
5. **Regular backup and recovery testing**
6. **Restrict network access**
7. **Use secrets management**

### For Users

1. **Use strong, unique passwords**
2. **Enable two-factor authentication (when available)**
3. **Don't share API keys**
4. **Review access logs periodically**
5. **Report suspicious activity**

---

## Incident Response

### Response Procedure

1. **Detection**: Automated monitoring or user report
2. **Containment**: Isolate affected systems
3. **Investigation**: Determine scope and impact
4. **Remediation**: Fix vulnerability, patch systems
5. **Recovery**: Restore services
6. **Post-Incident**: Review and improve

### Contact

- **Security Team**: security@resumeparser.com
- **Emergency**: +1-XXX-XXX-XXXX (24/7)

### Notification

In case of a data breach:
- Affected users notified within 72 hours
- Regulatory authorities notified as required
- Public disclosure as appropriate

---

## Security Updates

Subscribe to security announcements:
- GitHub Security Advisories
- Email list: security-announce@resumeparser.com

---

## Acknowledgments

We thank the following security researchers for responsibly disclosing vulnerabilities:

*No disclosures yet*

---

**Last Updated**: 2026-02-05
**Security Contact**: security@resumeparser.com
