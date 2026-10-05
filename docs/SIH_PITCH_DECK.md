# SaathiAI — SIH 2026 Pitch Deck & Live Demonstration Guide

## Slide 1: Title & Vision
- **Project:** SaathiAI (साथी AI)
- **Tagline:** Real-Time AI Multi-Modal Stress, Distress & Vulnerability Assessment for Helplines & Emergency Response
- **Problem Statement:** Emergency helplines (112, 1090, 1098, mental health hotlines) face call overload, high triage latency (up to 15-20 min hold times), and subjective assessment errors. Responders lack objective multi-modal intelligence during peak surges.

---

## Slide 2: The Solution — Multi-Modal Triage Intelligence
SaathiAI computes a real-time **Stress & Vulnerability Index (SVI, 0–100)** across 5 calibrated dimensions:
1. **Acoustic & Prosodic Features (M08/M09):** Pitch jitter, tremors, voice breaks, speech rate anomalies.
2. **Multilingual NLP & Distress Mining (M10-M12):** Indic-aware threat, helplessness, and fear extraction (English, Hindi, Hinglish).
3. **Self-Report Gating (M14/M15):** Caller situational ratings with instant safety triggers.
4. **Context & Vulnerability Parsing (M16/M17):** Ongoing threat, isolated location, prior history, vulnerability flags.
5. **Zero-Miss Crisis Override (M13/M23):** Immediate critical escalation if life-threatening triggers occur.

---

## Slide 3: End-to-End System Architecture
```
Caller Mic (WebRTC/LiveKit)  ──┐
Caller Self-Report Form       ──┼─► FastAPI Orchestrator (26 Modules) ─► SVI Fusion Engine
Phone Audio Upload (WAV/PCM)  ──┘          │
                                            ├─► WebSocket Real-Time Stream (5s push)
                                            ├─► PostgreSQL / MinIO / Redis Cache
                                            └─► Next.js Responder Dashboard (JWT/RBAC)
```

---

## Slide 4: Live Demonstration Script (5-Minute Walkthrough)

### Step 1: Login & Access Control (`/login`)
- Show glassmorphism authentication with Role-Based Access Control (`RESPONDER`, `ADMIN`, `SUPERVISOR`, `AUDITOR`).
- Click "Login as Responder" -> Redirects to real-time Triage Queue.

### Step 2: Caller Intake (`/caller`)
- Switch to caller tab: Simulate a high-distress Hindi/Hinglish emergency call ("Bachao! Mere ghar par attack ho raha hai, please send police immediately!").
- Submit optional self-report ratings.

### Step 3: Responder Dashboard & Live SVI Gauge (`/cases/{id}`)
- Show the triage queue prioritizing the case with a red `CRITICAL (Safety Override)` badge.
- Open case detail: Highlight the interactive SVI gauge (e.g. 96/100), modality contribution breakdown, evidence chips, and AI explanation.

### Step 4: Human-in-the-Loop Review (`/cases/{id}/review`)
- Demonstrate the responder verifying the recommendation ("Dispatch emergency police unit + mental health counselor") and committing the review.
- Show instant audit trail logging.

### Step 5: System Analytics & Observability (`/analytics`, `/metrics`)
- Showcase the real-time analytics dashboard with SVI distribution charts, safety override rates, and Prometheus observability metrics.

---

## Slide 5: Key USPs & Hackathon Differentiators
1. **Explainable AI (XAI):** Not a black box — gives clear prosodic and linguistic evidence tags for every decision.
2. **Zero Silent Suppression:** Hard safety rules run first to guarantee life-saving alerts never get blocked by model uncertainty.
3. **Multilingual for Bharat:** Native support for Hindi, Hinglish, and English accents.
4. **Resilient Architecture:** Works on high-speed WebRTC as well as degraded low-bandwidth 2G/3G audio with quality abstention.
