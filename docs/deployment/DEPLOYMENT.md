# Resume Parser - Deployment Guide

This guide covers deploying the Resume Parser application to various environments.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Cloud Deployment](#cloud-deployment)
5. [Production Checklist](#production-checklist)
6. [Monitoring & Logging](#monitoring--logging)
7. [Backup & Recovery](#backup--recovery)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- Python 3.11+
- Node.js 18+ (for frontend)
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (for containerized deployment)
- Tesseract OCR

### Required Accounts

- AWS Account (for S3 storage)
- OpenAI API Key (for LLM)
- Domain name (for production)
- SSL Certificate (Let's Encrypt or similar)

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Django Settings
DEBUG=False
SECRET_KEY=your-super-secret-key-min-50-chars-random
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DATABASE_URL=postgresql://user:password@host:5432/resume_parser

# Redis & Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# AWS S3
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_STORAGE_BUCKET_NAME=resume-parser-production
AWS_S3_REGION_NAME=us-east-1

# LLM
OPENAI_API_KEY=sk-your-openai-api-key
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini

# CORS (frontend URL)
CORS_ALLOWED_ORIGINS=https://yourdomain.com

# Monitoring (optional)
SENTRY_DSN=https://your-sentry-dsn
```

---

## Local Development

### Quick Start

```bash
# 1. Clone repository
git clone https://github.com/yourusername/resume_parser.git
cd resume_parser

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment file
cp .env.example .env
# Edit .env with your settings

# 5. Start PostgreSQL and Redis
# Using Docker:
docker run -d --name postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:15
docker run -d --name redis -p 6379:6379 redis:7

# 6. Run migrations
python manage.py migrate

# 7. Create superuser
python manage.py createsuperuser

# 8. Start Django server
python manage.py runserver

# 9. Start Celery worker (new terminal)
celery -A config worker -l info

# 10. Start frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Access Points

- API: http://localhost:8000
- Admin: http://localhost:8000/admin
- Frontend: http://localhost:5173

---

## Docker Deployment

### Development with Docker Compose

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Run migrations
docker-compose exec api python manage.py migrate

# Create superuser
docker-compose exec api python manage.py createsuperuser

# Stop services
docker-compose down
```

### Production Docker Setup

**`docker-compose.prod.yml`**:

```yaml
version: '3.8'

services:
  api:
    image: resume-parser:latest
    build:
      context: .
      dockerfile: Dockerfile
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120
    environment:
      - DEBUG=False
      - DATABASE_URL=${DATABASE_URL}
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
      - SECRET_KEY=${SECRET_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - AWS_STORAGE_BUCKET_NAME=${AWS_STORAGE_BUCKET_NAME}
    ports:
      - "8000:8000"
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  celery_worker:
    image: resume-parser:latest
    command: celery -A config worker -l info --autoscale=10,3
    environment:
      - DEBUG=False
      - DATABASE_URL=${DATABASE_URL}
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
      - SECRET_KEY=${SECRET_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - AWS_STORAGE_BUCKET_NAME=${AWS_STORAGE_BUCKET_NAME}
    restart: always

  celery_beat:
    image: resume-parser:latest
    command: celery -A config beat -l info
    environment:
      - DEBUG=False
      - DATABASE_URL=${DATABASE_URL}
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
      - SECRET_KEY=${SECRET_KEY}
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - static_volume:/var/www/static
    depends_on:
      - api
    restart: always

volumes:
  static_volume:
```

### Nginx Configuration

**`nginx.conf`**:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream api {
        server api:8000;
    }

    server {
        listen 80;
        server_name yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com;

        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;

        # SSL configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
        ssl_prefer_server_ciphers off;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        location / {
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # Upload size limit
            client_max_body_size 10M;
        }

        location /static/ {
            alias /var/www/static/;
        }
    }
}
```

---

## Cloud Deployment

### AWS Deployment

#### Architecture

```mermaid
flowchart TB
    DNS[Route 53<br/>DNS]
    CDN[CloudFront<br/>CDN]
    ALB[ALB<br/>Load Balancer]

    DNS --> CDN
    CDN --> ALB

    ALB --> ECS1 & ECS2 & ECS3

    subgraph ECS["ECS Cluster"]
        ECS1[ECS<br/>API]
        ECS2[ECS<br/>API]
        ECS3[ECS<br/>Worker]
    end

    ECS1 & ECS2 & ECS3 --> RDS & Redis & S3

    subgraph Data["Data Layer"]
        RDS[(RDS<br/>PostgreSQL)]
        Redis[(ElastiCache<br/>Redis)]
        S3[(S3<br/>Storage)]
    end
```

#### Setup Steps

1. **Create VPC and Subnets**
```bash
# Using AWS CLI
aws ec2 create-vpc --cidr-block 10.0.0.0/16
```

2. **Create RDS Instance**
```bash
aws rds create-db-instance \
    --db-instance-identifier resume-parser-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --master-username admin \
    --master-user-password your-password \
    --allocated-storage 20
```

3. **Create ElastiCache Redis**
```bash
aws elasticache create-cache-cluster \
    --cache-cluster-id resume-parser-redis \
    --cache-node-type cache.t3.micro \
    --engine redis \
    --num-cache-nodes 1
```

4. **Create S3 Bucket**
```bash
aws s3 mb s3://resume-parser-production
aws s3api put-bucket-policy --bucket resume-parser-production --policy file://bucket-policy.json
```

5. **Create ECS Cluster**
```bash
aws ecs create-cluster --cluster-name resume-parser
```

6. **Create Task Definition**

**`task-definition.json`**:
```json
{
  "family": "resume-parser",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "your-ecr-repo/resume-parser:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "DEBUG", "value": "False"},
        {"name": "DATABASE_URL", "value": "postgresql://..."}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/resume-parser",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Railway Deployment

Railway provides simple deployment for Django applications.

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Add PostgreSQL
railway add -p postgresql

# Add Redis
railway add -p redis

# Set environment variables
railway variables set OPENAI_API_KEY=sk-...
railway variables set SECRET_KEY=your-secret-key
railway variables set AWS_ACCESS_KEY_ID=...
railway variables set AWS_SECRET_ACCESS_KEY=...

# Deploy
railway up
```

**`railway.json`**:
```json
{
  "build": {
    "builder": "DOCKERFILE"
  },
  "deploy": {
    "startCommand": "gunicorn config.wsgi:application --bind 0.0.0.0:$PORT",
    "healthcheckPath": "/health",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

### Render Deployment

**`render.yaml`**:
```yaml
services:
  - type: web
    name: resume-parser-api
    env: docker
    dockerfilePath: ./Dockerfile
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: resume-parser-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          type: redis
          name: resume-parser-redis
          property: connectionString
      - key: SECRET_KEY
        generateValue: true
      - key: OPENAI_API_KEY
        sync: false

  - type: worker
    name: resume-parser-worker
    env: docker
    dockerfilePath: ./Dockerfile
    dockerCommand: celery -A config worker -l info
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: resume-parser-db
          property: connectionString

databases:
  - name: resume-parser-db
    plan: starter

services:
  - type: redis
    name: resume-parser-redis
    plan: starter
```

---

## Production Checklist

### Security

- [ ] `DEBUG=False` in production
- [ ] Strong `SECRET_KEY` (50+ random characters)
- [ ] HTTPS only (redirect HTTP to HTTPS)
- [ ] CORS configured for frontend domain only
- [ ] Rate limiting enabled
- [ ] SQL injection protection (ORM)
- [ ] XSS protection (React escaping)
- [ ] CSRF protection enabled
- [ ] File upload validation
- [ ] API keys in environment variables
- [ ] Database credentials secure
- [ ] Firewall rules configured

### Performance

- [ ] Database connection pooling
- [ ] Redis caching enabled
- [ ] Celery workers scaled appropriately
- [ ] Static files served via CDN
- [ ] Gzip compression enabled
- [ ] Database indexes created
- [ ] Query optimization done

### Reliability

- [ ] Health check endpoint configured
- [ ] Auto-restart on failure
- [ ] Database backups scheduled
- [ ] Log rotation configured
- [ ] Monitoring alerts set up
- [ ] Error tracking (Sentry) configured
- [ ] Load balancer health checks

### Scaling

- [ ] Horizontal scaling ready
- [ ] Database read replicas (if needed)
- [ ] Redis cluster (if needed)
- [ ] CDN for static assets
- [ ] Auto-scaling policies defined

---

## Monitoring & Logging

### Sentry Integration

```python
# settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    integrations=[
        DjangoIntegration(),
        CeleryIntegration(),
    ],
    traces_sample_rate=0.1,
    send_default_pii=False,
)
```

### Prometheus Metrics

```python
# Install django-prometheus
# pip install django-prometheus

# settings.py
INSTALLED_APPS = [
    ...
    'django_prometheus',
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    ...
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]
```

### Logging Configuration

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/resume_parser/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

---

## Backup & Recovery

### Database Backup Script

**`scripts/backup.sh`**:
```bash
#!/bin/bash
set -e

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="resume_parser"

# Create backup
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME | gzip > "${BACKUP_DIR}/db_${DATE}.sql.gz"

# Upload to S3
aws s3 cp "${BACKUP_DIR}/db_${DATE}.sql.gz" "s3://resume-parser-backups/db/"

# Clean old local backups (keep 7 days)
find "${BACKUP_DIR}" -name "db_*.sql.gz" -mtime +7 -delete

echo "Backup completed: db_${DATE}.sql.gz"
```

### Database Restore

```bash
# Download from S3
aws s3 cp s3://resume-parser-backups/db/db_20240115.sql.gz .

# Restore
gunzip -c db_20240115.sql.gz | psql -h $DB_HOST -U $DB_USER -d $DB_NAME
```

### Automated Backup with Cron

```bash
# Add to crontab
0 2 * * * /app/scripts/backup.sh >> /var/log/backup.log 2>&1
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed

```
Error: could not connect to server: Connection refused
```

**Solution**:
- Check DATABASE_URL is correct
- Verify PostgreSQL is running
- Check firewall/security groups

#### 2. Celery Workers Not Processing

```
Error: No workers are running
```

**Solution**:
```bash
# Check worker status
celery -A config inspect active

# Restart workers
docker-compose restart celery_worker
```

#### 3. S3 Upload Failed

```
Error: Access Denied
```

**Solution**:
- Verify AWS credentials
- Check IAM permissions
- Verify bucket policy

#### 4. LLM API Timeout

```
Error: Request timed out
```

**Solution**:
- Check OpenAI API status
- Verify API key is valid
- Increase timeout setting

### Health Check Endpoints

```bash
# API health
curl http://localhost:8000/health

# Database health
docker-compose exec api python manage.py check --database default

# Redis health
docker-compose exec redis redis-cli ping

# Celery health
docker-compose exec api celery -A config inspect ping
```

### Log Locations

| Service | Log Location |
|---------|--------------|
| Django | `/var/log/resume_parser/app.log` |
| Nginx | `/var/log/nginx/access.log` |
| Celery | Docker logs or `/var/log/celery/` |
| PostgreSQL | `/var/log/postgresql/` |

---

## Rollback Procedure

### Docker Rollback

```bash
# List available images
docker images resume-parser

# Rollback to previous version
docker-compose stop api celery_worker
docker tag resume-parser:previous resume-parser:latest
docker-compose up -d api celery_worker
```

### Database Rollback

```bash
# Check migration history
python manage.py showmigrations

# Rollback to specific migration
python manage.py migrate parser 0005_previous_migration
```

---

## Support

- **Documentation**: See other docs in this repository
- **Issues**: https://github.com/yourusername/resume_parser/issues
- **Email**: support@resumeparser.com

---

**Last Updated**: 2026-02-05
**Version**: 1.0
