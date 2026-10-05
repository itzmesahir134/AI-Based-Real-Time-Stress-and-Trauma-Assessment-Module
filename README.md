# SAATHI-AI

> **AI-Assisted First-Contact Stress & Trauma Assessment and Support-Routing System**  
> *Loopers — Smart India Hackathon 2026 (Problem Statement 26093)*

SAATHI-AI is an AI-assisted first-contact triage and support-routing layer designed to integrate with the NHAA 14566 helpline and allied channels. It transforms multimodal evidence (voice acoustics, linguistic text markers, structured self-reports, case context, and interaction dynamics) into an auditable **Support/Vulnerability/Immediate-urgency Indicator (SVI)** for trained human responders.

---

## Repository Structure

```text
saathi-ai/
├── apps/
│   ├── web/                    # Next.js responder dashboard + triage interface
│   └── realtime-agent/         # Live media / WebRTC interaction client
├── services/
│   ├── api/                    # FastAPI orchestration, session & case management
│   ├── inference/              # ML inference workers (Distress models, IndicBERT/XLM-R)
│   ├── audio-worker/           # Signal processing (VAD, faster-whisper ASR, openSMILE)
│   ├── scoring/                # SVI fusion engine, evidence quality & safety overrides
│   └── recommendations/        # Support routing & recommendation engine
├── packages/
│   ├── schemas/                # Shared Pydantic schemas and TypeScript contracts
│   ├── config/                 # Centralized configuration (SVI weights, risk bands)
│   └── utils/                  # Shared utilities (logging, validation, IDs)
├── models/
│   ├── voice/                  # Acoustic feature extraction & voice distress models
│   ├── text/                   # IndicBERT / XLM-R linguistic classifiers
│   ├── crisis/                 # Deterministic rules & ML crisis detectors
│   └── calibration/            # Platt scaling / isotonic regression calibration artifacts
├── infra/
│   ├── docker/                 # Service Dockerfiles
│   ├── compose/                # Local development Docker Compose configurations
│   ├── migrations/             # PostgreSQL database migrations (Alembic)
│   └── monitoring/             # Prometheus / Grafana observability configs
├── datasets/
│   ├── raw/                    # Raw input recordings (strictly gitignored)
│   ├── processed/              # Processed / normalized features
│   ├── manifests/              # Dataset manifests and metadata splits
│   ├── labels/                 # Multi-target distress & safety labels
│   └── evaluation/             # Held-out challenge and evaluation benchmarks
├── docs/
│   ├── architecture/           # System architecture and design diagrams
│   ├── api/                    # API specifications and contracts
│   └── model-cards/            # Model performance cards & bias/fairness reports
└── tests/
    ├── unit/                   # Unit tests (SVI math, normalization, safety rules)
    ├── integration/            # Multi-service integration tests
    ├── model/                  # Model inference and calibration validation
    └── e2e/                    # End-to-end caller-to-responder pipeline tests
```

---

## Core Technologies

- **Frontend:** Next.js (App Router), React, TypeScript, Tailwind CSS, shadcn/ui
- **Real-time Media:** LiveKit, WebRTC
- **Backend & APIs:** Python, FastAPI, Pydantic v2
- **Audio & Signal Processing:** Silero VAD, faster-whisper, librosa, openSMILE
- **NLP & Multilingual ML:** Hugging Face Transformers, IndicBERT, XLM-R, scikit-learn, PyTorch
- **Data & Storage:** PostgreSQL, Redis, MinIO (S3 compatible)
- **Generative AI:** Google Gemini (explanation drafting & conversational assistance)

---

## Quick Start & Live Demo

### One-Click Demo Launch (Windows PowerShell)
```powershell
./scripts/run_demo.ps1
```
This single command:
1. Trains ML model checkpoints and exports them to `models/`.
2. Seeds the database with 17 realistic emergency & helpline triage cases across all risk bands.
3. Launches the FastAPI backend (`http://localhost:8000`).
4. Launches the Next.js frontend (`http://localhost:3000/login`) and opens your browser.

### Demo Credentials (Role-Based Access Control)
| Role | Username | Password | Access Level |
|---|---|---|---|
| **Responder** | `responder` | `saathi-resp-2026` | Live Triage Queue, Case Details, Human Review Form |
| **Admin** | `admin` | `saathi-admin-2026` | Full Access + Model Registry + System Audit Log |
| **Auditor** | `auditor` | `saathi-audit-2026` | Read-only Cases & Immutable Audit Log Trail |

---

## Running Tests

```bash
# Run all 81 unit, integration, and E2E scenario tests
pytest tests/ -q
```

---

## Documentation & Presentation Assets
- **Pitch Deck & Demo Script:** [`docs/SIH_PITCH_DECK.md`](file:///c:/Projects/SaathiAI/docs/SIH_PITCH_DECK.md)
- **Judges' Q&A Defense Guide:** [`docs/JUDGES_QA_DEFENSE_GUIDE.md`](file:///c:/Projects/SaathiAI/docs/JUDGES_QA_DEFENSE_GUIDE.md)
- **Model Performance & Ethical Cards:** [`docs/model-cards/`](file:///c:/Projects/SaathiAI/docs/model-cards/)
- **Full Architectural Specification:** [`SAATHI_AI_IMPLEMENTATION_SPEC.md`](file:///c:/Projects/SaathiAI/SAATHI_AI_IMPLEMENTATION_SPEC.md)

