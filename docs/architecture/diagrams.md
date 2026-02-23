# Resume Parser - Architecture Diagrams Guide

This document provides visual representations of the system architecture and guidance on creating diagrams for presentations or documentation.

---

## Table of Contents
1. [System Architecture Diagram](#system-architecture-diagram)
2. [Data Flow Diagram](#data-flow-diagram)
3. [Database Schema](#database-schema)
4. [Sequence Diagrams](#sequence-diagrams)
5. [Deployment Architecture](#deployment-architecture)
6. [Creating Diagrams](#creating-diagrams)

---

## System Architecture Diagram

### High-Level Architecture

This shows the complete system from client to data storage:

```mermaid
flowchart TB
    subgraph Client
        Browser[Web Browser<br/>Client]
    end

    Browser -->|HTTPS| LB

    subgraph Edge["Edge Layer"]
        LB[Load Balancer / CDN<br/>Cloudflare]
    end

    LB --> API

    subgraph Application["Application Layer"]
        API[Django REST Framework]
        subgraph Middleware
            Auth[Authentication]
            Rate[Rate Limiting]
            CORS[CORS]
            Valid[Request Validation]
        end
    end

    API --> DB
    API --> Redis
    API --> S3

    subgraph Storage["Data Layer"]
        DB[(PostgreSQL<br/>Metadata)]
        S3[(S3 Storage<br/>PDF Files)]
    end

    subgraph Queue["Task Queue"]
        Redis[(Redis / Celery<br/>Task Queue)]
    end

    Redis --> Workers

    subgraph Processing["Processing Layer"]
        Workers[Celery Workers<br/>Auto-scaling]
        subgraph WorkerPool["Worker Pool"]
            W1[Worker 1]
            W2[Worker 2]
            W3[Worker 3]
        end
    end

    Workers --> PDF
    Workers --> LLM
    Workers --> Pydantic

    subgraph External["External Services"]
        PDF[pdfplumber/<br/>Tesseract<br/>Text Extract]
        LLM[OpenAI /<br/>Anthropic<br/>LLM Call]
        Pydantic[Pydantic<br/>Validator]
    end
```

### Component Responsibilities

| Component | Responsibility | Technology |
|-----------|---------------|------------|
| **Client** | UI, file upload, display results | React, TanStack Table |
| **Load Balancer** | Traffic distribution, SSL, DDoS | Cloudflare, AWS ALB |
| **API Server** | Request handling, auth, validation | Django REST Framework |
| **Task Queue** | Async job processing | Celery + Redis |
| **Workers** | PDF parsing, LLM calls | Python, OpenAI |
| **Database** | Store metadata, parsed data | PostgreSQL |
| **File Storage** | Store PDFs, exports | AWS S3, Cloudflare R2 |

---

## Data Flow Diagram

### Single Resume Upload Flow

```mermaid
flowchart TD
    User1([User]) -->|1. Upload PDF| API[API Server<br/>Django REST]

    API -->|2. Validate file<br/>Check size, type, scan malware| S3[(S3 Storage<br/>Save PDF)]

    S3 -->|3. Return S3 URL| DB1[(Database<br/>Create job record<br/>status = 'pending')]

    DB1 -->|4. Dispatch task| Queue[Celery Queue<br/>Job queued]

    Queue -->|5. Worker picks up| Worker

    subgraph Worker["Celery Worker"]
        Step1[Step 1: Download PDF from S3]
        Step2[Step 2: Extract Text<br/>Try pdfplumber<br/>Fallback to OCR]
        Step3[Step 3: Call LLM API<br/>Send prompt + text<br/>Receive JSON]
        Step4[Step 4: Validate<br/>Pydantic schema<br/>Calculate confidence]
        Step5[Step 5: Save to DB<br/>Store validated data<br/>Update job status]

        Step1 --> Step2 --> Step3 --> Step4 --> Step5
    end

    Worker --> DB2[(Database<br/>status='completed'<br/>+ parsed_data)]

    DB2 -->|6. User polls| User2([User<br/>Receives JSON])
```

### Error Flow

```mermaid
flowchart TD
    Task[Celery Task] --> PDF{Error: PDF corrupt?}
    Task --> LLM{Error: LLM rate limit?}
    Task --> Valid{Error: Validation fails?}

    PDF -->|Yes| OCR[Retry with OCR]
    OCR -->|Success| Continue[Continue Processing]
    OCR -->|Fail| Failed[Mark as failed]

    LLM -->|Yes| Backoff[Exponential backoff]
    Backoff --> Retry[Retry max 3x]

    Valid -->|Yes| Partial[Save partial data]
    Partial --> Review[Flag for manual review]
```

---

## Database Schema

### Entity Relationship Diagram

```mermaid
erDiagram
    USERS {
        uuid id PK
        string email
        string password_hash
        string company
        string role
        timestamp created_at
    }

    RESUME_PARSE_JOBS {
        uuid id PK
        uuid user_id FK
        string original_filename
        string file_url
        int file_size_bytes
        string status
        string error_message
        timestamp created_at
        timestamp started_at
        timestamp completed_at
        float processing_time
    }

    PARSED_RESUME_DATA {
        uuid id PK
        uuid job_id FK
        jsonb raw_json
        jsonb validated_data
        float confidence_score
        string extraction_method
        string llm_model
        int llm_tokens_used
        float llm_cost
        timestamp created_at
    }

    AUDIT_LOGS {
        uuid id PK
        uuid user_id FK
        uuid job_id FK
        string action
        jsonb details
        string ip_address
        string user_agent
        timestamp timestamp
    }

    USERS ||--o{ RESUME_PARSE_JOBS : "creates"
    RESUME_PARSE_JOBS ||--|| PARSED_RESUME_DATA : "produces"
    USERS ||--o{ AUDIT_LOGS : "generates"
    RESUME_PARSE_JOBS ||--o{ AUDIT_LOGS : "logs"
```

### Key Indexes

```sql
-- Resume parse jobs
CREATE INDEX idx_jobs_user_status ON resume_parse_jobs (user_id, status);
CREATE INDEX idx_jobs_created ON resume_parse_jobs (created_at DESC);

-- Parsed data (JSONB queries)
CREATE INDEX idx_parsed_name ON parsed_resume_data ((validated_data->'contact'->>'name'));
CREATE INDEX idx_parsed_email ON parsed_resume_data ((validated_data->'contact'->>'email'));
CREATE INDEX idx_parsed_skills ON parsed_resume_data USING GIN ((validated_data->'skills'->'technical'));
```

---

## Sequence Diagrams

### Authentication Flow

```mermaid
sequenceDiagram
    participant User
    participant API as API Server
    participant DB as Database
    participant JWT as JWT Service

    User->>API: Login (email/pass)
    API->>DB: Query (verify user)
    DB-->>API: User data
    API->>JWT: Generate JWT token
    JWT-->>API: Token
    API-->>User: 200 OK + JWT token

    Note over User,JWT: Authenticated Request

    User->>API: API call + JWT header
    API->>JWT: Verify token
    JWT-->>API: Valid
    API-->>User: Response
```

### Resume Parsing Sequence

```mermaid
sequenceDiagram
    participant User
    participant API
    participant S3
    participant Celery
    participant Worker
    participant LLM as LLM API
    participant Valid as Validator
    participant DB as Database

    User->>API: POST /upload
    API->>S3: Save PDF
    S3-->>API: URL
    API->>Celery: Queue task
    API-->>User: 202 Accepted

    Celery->>Worker: Pick task
    Worker->>Worker: Extract PDF text
    Worker->>LLM: Call LLM
    LLM-->>Worker: JSON response
    Worker->>Valid: Validate data
    Valid-->>Worker: Valid
    Worker->>DB: Save result
    DB-->>Worker: OK

    User->>API: GET /jobs/{id}
    API->>DB: Query
    DB-->>API: Result
    API-->>User: JSON data
```

---

## Deployment Architecture

### Production Infrastructure (AWS)

```mermaid
flowchart TB
    Internet([Internet Users])
    Internet --> CDN

    subgraph Edge["Edge Layer"]
        CDN[Cloudflare CDN<br/>SSL/TLS<br/>DDoS protect]
    end

    CDN --> ALB

    subgraph AWS["AWS Cloud"]
        ALB[AWS ALB<br/>Load Balancer]

        ALB --> ECS1 & ECS2 & ECS3

        subgraph ECSCluster["ECS Cluster - API"]
            ECS1[ECS Task 1<br/>Django]
            ECS2[ECS Task 2<br/>Django]
            ECS3[ECS Task 3<br/>Django]
        end

        ECS1 & ECS2 & ECS3 --> RDS & ElastiCache & S3

        subgraph DataLayer["Data Layer"]
            RDS[(RDS<br/>PostgreSQL)]
            ElastiCache[(ElastiCache<br/>Redis)]
            S3[(S3<br/>Bucket)]
        end

        ElastiCache --> Workers

        subgraph WorkerCluster["ECS Cluster - Workers"]
            Workers[ECS Tasks<br/>Celery Workers<br/>Auto-scale]
        end
    end
```

### Docker Container Architecture

```mermaid
flowchart TB
    subgraph DockerHost["Docker Host"]
        subgraph Containers["Containers"]
            C1[Container 1<br/>Django API<br/>Port: 8000]
            C2[Container 2<br/>Celery Worker<br/>Workers: 4]
            C3[(Container 3<br/>PostgreSQL<br/>Port: 5432)]
            C4[(Container 4<br/>Redis<br/>Port: 6379)]
        end

        subgraph Volumes["Volumes"]
            Vol[Shared Volume<br/>/var/lib/postgresql/data]
        end

        C1 <--> C3
        C1 <--> C4
        C2 <--> C4
        C3 <--> Vol
    end
```

---

## Creating Diagrams

### Tools for Creating Diagrams

#### 1. **Mermaid.js** (Recommended for documentation)

```mermaid
graph TD
    A[User] -->|Upload| B[API Server]
    B -->|Save| C[S3]
    B -->|Queue| D[Celery]
    D -->|Process| E[Worker]
    E -->|Extract| F[pdfplumber]
    E -->|Call| G[OpenAI]
    E -->|Validate| H[Pydantic]
    E -->|Save| I[Database]
```

**Usage**: Embed in Markdown, render in GitHub/GitLab

#### 2. **draw.io / diagrams.net** (For presentations)

- Free, web-based
- Export to PNG, SVG, PDF
- Templates available
- URL: https://app.diagrams.net/

#### 3. **Lucidchart** (Professional diagrams)

- Collaborative editing
- Cloud-based
- Extensive shape libraries
- URL: https://www.lucidchart.com/

#### 4. **PlantUML** (Code-based diagrams)

```plantuml
@startuml
actor User
User -> API: Upload PDF
API -> S3: Store file
API -> Celery: Queue task
Celery -> Worker: Process
Worker -> LLM: Extract data
Worker -> Database: Save result
Database --> User: Return JSON
@enduml
```

#### 5. **Excalidraw** (Hand-drawn style)

- Simple, fast
- Export to PNG/SVG
- URL: https://excalidraw.com/

### Diagram Best Practices

1. **Keep it simple**: One concept per diagram
2. **Use consistent shapes**: Rectangles for services, cylinders for databases
3. **Show data flow**: Use arrows with labels
4. **Include legends**: Explain colors/shapes
5. **Version control**: Store diagram source files in Git

### Recommended Diagram Types

| Purpose | Diagram Type | Tool |
|---------|-------------|------|
| System overview | Component diagram | draw.io |
| Request flow | Sequence diagram | PlantUML |
| Database design | ER diagram | dbdiagram.io |
| Deployment | Infrastructure diagram | AWS Architecture |
| Data processing | Flowchart | Mermaid |

---

## Interactive Diagrams

### Using Mermaid in GitHub

Create `.md` files with mermaid code blocks:

\`\`\`mermaid
sequenceDiagram
    User->>API: POST /upload
    API->>S3: Save PDF
    API->>Celery: Queue task
    Celery->>Worker: Process
    Worker->>LLM: Extract
    Worker->>DB: Save
    DB-->>User: JSON
\`\`\`

GitHub will render these automatically!

---

## Diagram Templates

All diagram templates are available in the `docs/diagrams/` directory:

- `system-architecture.drawio` - Main system diagram
- `data-flow.drawio` - Data flow diagram
- `database-schema.dbml` - Database schema (dbdiagram format)
- `deployment.drawio` - AWS deployment diagram
- `sequence-auth.puml` - Authentication sequence (PlantUML)

---

## Further Resources

- **AWS Architecture Icons**: https://aws.amazon.com/architecture/icons/
- **C4 Model**: https://c4model.com/ (Structured architecture diagrams)
- **UML Diagrams**: https://www.uml-diagrams.org/
- **System Design Primer**: https://github.com/donnemartin/system-design-primer

---

**Last Updated**: 2026-02-05
