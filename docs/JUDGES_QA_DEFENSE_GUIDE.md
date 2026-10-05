# SaathiAI — Judges' Q&A Defense Guide (SIH 2026)

This cheat sheet equips the team with crisp, authoritative answers to the hardest questions judges typically ask during hackathon evaluations.

---

### Q1: "Is this model diagnosing mental trauma or clinical PTSD?"
**Answer:**
> "No, absolutely not. SaathiAI is **strictly a real-time triage prioritization tool**, not a diagnostic medical device. It measures situational vocal arousal, speech disruptions, and explicit distress markers to help human emergency operators prioritize who needs immediate attention first in a flooded queue."

---

### Q2: "How do you comply with privacy regulations and India's Digital Personal Data Protection (DPDP) Act 2023?"
**Answer:**
> "We implement privacy-by-design:
> 1. **Explicit Consent Layer:** Callers are presented with granular consent options (`allowed_voice`, `allowed_text`) before processing.
> 2. **Ephemeral & Encrypted Storage:** Audio is stored in encrypted MinIO object buckets with configurable retention policies and instant purge mechanisms.
> 3. **Role-Based Access Control (RBAC):** Only authorized responders and supervisors can view case details.
> 4. **Immutable Audit Trail:** All access, priority modifications, and exports are permanently recorded in the `audit_logs` table."

---

### Q3: "What happens if a caller is in low-bandwidth 2G/3G conditions or in a noisy vehicle?"
**Answer:**
> "Our **Module M04 (Audio Quality Analyzer)** continuously computes Signal-to-Noise Ratio (SNR), clipping ratio, and spectral flatness. If quality drops below our threshold (`quality_score < 0.15`), the voice model **abstains** rather than hallucinating high distress. The SVI Fusion Engine (M21) gracefully shifts weight to transcript and self-report inputs, marking the assessment status as `PARTIAL`."

---

### Q4: "How do you handle Indian languages, mixed dialects, and Hinglish?"
**Answer:**
> "Our text pipeline (M10-M12) utilizes Indic-normalized tokenizers and bilingual regular expression matrices supporting Hindi (Devanagari), English, and phonetic Romanized Hindi (Hinglish). We evaluate semantic intent across 8 distress dimensions (threat, fear, urgency, help requests) rather than relying on strict dictionary grammar."

---

### Q5: "What if the AI makes a false negative and misses a critical suicide or domestic violence threat?"
**Answer:**
> "We solved this with our **Zero Silent Suppression Safety Architecture (M13/M23)**. Deterministic safety rules execute prior to and independently of any machine learning model. If any crisis keyword or critical self-report answer is detected, a `CRITICAL` safety override is triggered unconditionally with `1.0` confidence, ensuring no statistical model can silently suppress life-threatening emergencies."

---

### Q6: "What is your real-time latency budget?"
**Answer:**
> "Our real-time streaming pipeline operates on 3-second audio chunk buffers with an end-to-end processing latency of **< 350ms** on standard CPU/GPU nodes, pushing provisional SVI updates over WebSockets every 5 seconds to the responder dashboard."

---

### Q7: "How is human oversight maintained?"
**Answer:**
> "SaathiAI adheres to the **Human-in-the-Loop (HITL)** mandate (Module M26). The AI provides recommendations and explainable evidence chips, but the final routing action and priority confirmation require the human responder's manual review and sign-off."
