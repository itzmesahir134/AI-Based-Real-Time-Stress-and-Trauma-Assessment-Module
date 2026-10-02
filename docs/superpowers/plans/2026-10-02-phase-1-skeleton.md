# Phase 1: Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish the foundational skeleton of SAATHI-AI: shared domain schemas, configuration loader, local containerized infrastructure (PostgreSQL, Redis, MinIO), FastAPI backend service with Sessions, Consent, and Cases CRUD, automated test suite, and Next.js frontend scaffold with caller consent & responder queue shell.

---

## Architecture & File Map

```
c:\Projects\SaathiAI/
├── packages/
│   ├── schemas/                     # Single source of truth contracts (Pydantic v2)
│   │   ├── __init__.py
│   │   ├── common.py                # UUIDs, timestamps, RiskBand, AssessmentStatus enums
│   │   ├── session.py               # SessionCreate, SessionResponse, ChannelEnum
│   │   ├── consent.py               # ConsentCreate, ConsentResponse, ConsentTypeEnum
│   │   ├── case.py                  # CaseCreate, CaseResponse, CaseStatusEnum
│   │   └── assessment.py            # MasterAssessmentObject, SVIResult, ModalityScores
│   ├── config/                      # Unified settings (pydantic-settings)
│   │   ├── __init__.py
│   │   └── settings.py              # Environment variables parser with validation
│   └── utils/                       # Shared helper utilities
│       ├── __init__.py
│       └── logging.py               # Structured logging configuration
├── infra/
│   └── compose/
│       └── docker-compose.yml       # PostgreSQL 16, Redis 7, MinIO local services
├── services/
│   └── api/
│       ├── __init__.py
│       ├── main.py                  # FastAPI application entrypoint with lifespan
│       ├── db/
│       │   ├── __init__.py
│       │   ├── session.py           # Async SQLAlchemy engine & sessionmaker
│       │   └── models.py            # PostgreSQL table definitions
│       └── routers/
│           ├── __init__.py
│           ├── health.py            # GET /health, GET /ready
│           ├── sessions.py          # POST /api/v1/sessions, GET /api/v1/sessions/{id}
│           ├── consent.py           # POST /api/v1/consent, GET /api/v1/consent/{session_id}
│           └── cases.py             # CRUD /api/v1/cases, GET /api/v1/cases/queue
├── apps/
│   └── web/                         # Next.js 14+ App Router frontend
│       ├── package.json
│       ├── tsconfig.json
│       ├── next.config.mjs
│       ├── src/
│       │   ├── app/
│       │   │   ├── layout.tsx
│       │   │   ├── page.tsx         # Welcome & Channel Selector
│       │   │   ├── caller/
│       │   │   │   └── page.tsx     # Consent capture & triage entry
│       │   │   └── responder/
│       │   │       └── page.tsx     # Responder queue skeleton
│       │   └── types/               # TypeScript schemas matching API
└── tests/
    ├── unit/
    │   ├── test_schemas.py          # Pydantic contract validation tests
    │   └── test_config.py           # Settings loading tests
    └── integration/
        ├── test_health_api.py       # Health check API test
        └── test_sessions_api.py     # Sessions & Consent lifecycle integration test
```

---

## Tasks

### Task 1: Core Domain Schemas (`packages/schemas`)
- [ ] Create `packages/schemas/common.py` defining `RiskBand` (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`), `AssessmentStatus` (`IN_PROGRESS`, `COMPLETE`, `INSUFFICIENT_EVIDENCE`), and base schemas.
- [ ] Create `packages/schemas/session.py` defining `ChannelEnum` (`VOICE_CALL`, `WEB_AUDIO`, `CHAT_TEXT`, `WHATSAPP`, `WALK_IN`), `SessionStatusEnum`, `SessionCreate`, and `SessionResponse`.
- [ ] Create `packages/schemas/consent.py` defining `ConsentType` (`AUDIO_RECORDING`, `AI_ASSESSMENT`, `DATA_RETENTION`), `ConsentRecord`, `ConsentCreate`, and `ConsentResponse`.
- [ ] Create `packages/schemas/case.py` defining `CaseStatus` (`OPEN`, `IN_REVIEW`, `ESCALATED`, `RESOLVED`, `CLOSED`), `CaseCreate`, and `CaseResponse`.
- [ ] Create `packages/schemas/assessment.py` defining `MasterAssessmentObject`, `SVIResult`, `ModalityScores`, `QualityFactors`, and `ModalityContributions` according to Spec §21.
- [ ] Create `packages/schemas/__init__.py` exporting all models.
- [ ] Write unit tests in `tests/unit/test_schemas.py` verifying schema validation and serialization.
- [ ] Run pytest to verify schema tests pass.

### Task 2: Shared Config & Logging (`packages/config`, `packages/utils`)
- [ ] Create `packages/config/settings.py` with `Settings` extending `BaseSettings` covering DB, Redis, LiveKit, Google AI, MinIO, and App settings with default fallbacks.
- [ ] Create `packages/utils/logging.py` configuring structured JSON logging with `structlog` (guaranteeing no PII is logged per Spec §39).
- [ ] Write unit test `tests/unit/test_config.py` validating environment overrides.
- [ ] Run pytest to verify config tests pass.

### Task 3: Infrastructure Docker Compose (`infra/compose/docker-compose.yml`)
- [ ] Create `infra/compose/docker-compose.yml` defining `postgres` (PostgreSQL 16 Alpine with healthcheck), `redis` (Redis 7 Alpine with healthcheck), and `minio` (MinIO S3-compatible storage with default buckets).
- [ ] Verify Compose file syntax with `docker compose -f infra/compose/docker-compose.yml config`.

### Task 4: Database Layer & SQLAlchemy Models (`services/api/db`)
- [ ] Create `services/api/db/session.py` with async SQLAlchemy engine and async session dependency `get_db`.
- [ ] Create `services/api/db/models.py` defining ORM models for `SessionModel`, `ConsentModel`, `CaseModel`, `SVIResultModel`, and `AuditLogModel` matching Spec §22 & §23.
- [ ] Write DB connection initialization helper with table auto-creation for development.

### Task 5: FastAPI Backend Service (`services/api`)
- [ ] Create `services/api/routers/health.py` with `/health` and `/ready` endpoints verifying DB & Redis connectivity.
- [ ] Create `services/api/routers/sessions.py` with `POST /api/v1/sessions` and `GET /api/v1/sessions/{session_id}`.
- [ ] Create `services/api/routers/consent.py` with `POST /api/v1/consent` and `GET /api/v1/consent/{session_id}`.
- [ ] Create `services/api/routers/cases.py` with `POST /api/v1/cases`, `GET /api/v1/cases`, and `GET /api/v1/cases/{case_id}`.
- [ ] Create `services/api/main.py` assembling routers, CORS middleware, exception handlers, and lifespan hooks.
- [ ] Write integration tests in `tests/integration/test_health_api.py` and `tests/integration/test_sessions_api.py` using `httpx.AsyncClient`.
- [ ] Run pytest to ensure all unit and integration tests pass.

### Task 6: Frontend Scaffold (`apps/web`)
- [ ] Initialize Next.js 14+ app in `apps/web` with TypeScript and Tailwind CSS.
- [ ] Configure `apps/web/src/types/api.ts` with TypeScript contracts mirroring Pydantic schemas.
- [ ] Implement `apps/web/src/app/page.tsx` (channel selection landing page).
- [ ] Implement `apps/web/src/app/caller/page.tsx` (multilingual consent and start assessment interface).
- [ ] Implement `apps/web/src/app/responder/page.tsx` (triage queue shell with real-time refresh placeholder).
- [ ] Verify frontend build with `npm run build` or Next.js check.

### Task 7: Verification & Push
- [ ] Run `ruff check .` and `mypy` on packages and services.
- [ ] Run `pytest tests/` ensuring all tests pass.
- [ ] Commit all Phase 1 files and push to `origin/main`.
