"""SIH 2026 Demo Scenario Runner (PS 26093).
Executes the 5 canonical triage scenarios (A-E) against the SAATHI-AI assessment engine
and outputs a structured validation report for judges.

Usage:
    python tools/demo_scenario_runner.py --api-url http://localhost:8000 --output tools/demo_results.json
"""

import argparse
import base64
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent
AUDIO_DIR = REPO_ROOT / "test_audio" / "pipeline_io" / "shared_16k"

SCENARIOS = [
    {
        "id": "A",
        "name": "Clean Audio — Low Distress Triage",
        "audio_file": "CLEAN_001_male_normal.wav",
        "language": "hi",
        "self_report": {
            "q1_distress": 1,
            "q2_safety": 0,
            "q3_urgency": 1,
            "q4_can_continue": 0,
            "support_needs": ["counselling"],
        },
        "context": {
            "incident_type": "stress",
            "ongoing_threat": False,
            "prior_case": False,
            "vulnerability_factors": [],
            "immediate_support_requested": False,
        },
        "expected": {
            "acceptable_bands": ["LOW", "MODERATE"],
            "expected_safety_override": False,
        },
    },
    {
        "id": "B",
        "name": "Noisy Audio — Acute Crisis Self-Report",
        "audio_file": "AUG_001_CLEAN_001_noise_16k_mono.wav",
        "language": "hi",
        "self_report": {
            "q1_distress": 4,
            "q2_safety": 4,
            "q3_urgency": 4,
            "q4_can_continue": 1,
            "support_needs": ["emergency_shelter", "immediate_police"],
        },
        "context": {
            "incident_type": "domestic_violence",
            "ongoing_threat": True,
            "prior_case": True,
            "vulnerability_factors": ["isolated_location"],
            "immediate_support_requested": True,
        },
        "expected": {
            "acceptable_bands": ["CRITICAL"],
            "expected_safety_override": True,
        },
    },
    {
        "id": "C",
        "name": "Text-Only — No Voice Modality",
        "audio_file": None,
        "language": "en",
        "self_report": {
            "q1_distress": 3,
            "q2_safety": 2,
            "q3_urgency": 3,
            "q4_can_continue": 0,
            "support_needs": ["legal_aid"],
        },
        "context": {
            "incident_type": "harassment",
            "ongoing_threat": False,
            "prior_case": False,
            "vulnerability_factors": [],
            "immediate_support_requested": False,
        },
        "expected": {
            "acceptable_bands": ["HIGH", "MODERATE"],
            "expected_safety_override": False,
        },
    },
    {
        "id": "D",
        "name": "Full Modalities — Immediate Threat & Agitation",
        "audio_file": "EMO_010_fear_normal.wav",
        "language": "hi",
        "self_report": {
            "q1_distress": 4,
            "q2_safety": 4,
            "q3_urgency": 4,
            "q4_can_continue": 1,
            "support_needs": ["immediate_police", "medical_aid"],
        },
        "context": {
            "incident_type": "physical_assault",
            "ongoing_threat": True,
            "prior_case": False,
            "vulnerability_factors": ["nighttime", "alone"],
            "immediate_support_requested": True,
        },
        "expected": {
            "acceptable_bands": ["CRITICAL"],
            "expected_safety_override": True,
            "min_evidence_coverage": 0.50,
        },
    },
    {
        "id": "E",
        "name": "Pure Silence — Insufficient Evidence Baseline",
        "audio_file": "EDGE_002_pure_silence.wav",
        "language": "hi",
        "self_report": None,
        "context": None,
        "expected": {
            "acceptable_bands": ["LOW"],
            "expected_safety_override": False,
            "acceptable_statuses": ["INSUFFICIENT_EVIDENCE", "PARTIAL"],
        },
    },
]


def load_audio_base64(filename: str) -> str:
    """Loads a WAV file from the test dataset and encodes to base64."""
    filepath = AUDIO_DIR / filename
    if not filepath.exists():
        # Fallback: create mock silent WAV bytes
        import io
        import numpy as np
        import soundfile as sf

        buf = io.BytesIO()
        sf.write(buf, np.zeros(16000, dtype=np.float32), 16000, format="WAV")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    with open(filepath, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def run_scenario(client: httpx.Client, api_url: str, scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Runs a single triage scenario end-to-end against the SAATHI-AI API."""
    start_time = time.perf_counter()

    # 1. Create Session
    session_res = client.post(
        f"{api_url}/api/v1/sessions",
        json={"channel": "WEB_AUDIO", "language": scenario["language"]},
    )
    if session_res.status_code not in (200, 201):
        raise RuntimeError(f"Session creation failed: {session_res.text}")
    session_id = session_res.json()["id"]

    # 2. Record Consents
    client.post(
        f"{api_url}/api/v1/consent",
        json={
            "session_id": session_id,
            "consent_type": "AUDIO_RECORDING",
            "status": "GRANTED",
        },
    )
    client.post(
        f"{api_url}/api/v1/consent",
        json={
            "session_id": session_id,
            "consent_type": "AI_ASSESSMENT",
            "status": "GRANTED",
        },
    )

    # 3. Load audio if present
    audio_base64 = None
    if scenario["audio_file"]:
        audio_base64 = load_audio_base64(scenario["audio_file"])

    # 4. Submit Assessment Run
    assessment_payload = {
        "session_id": session_id,
        "language": scenario["language"],
        "audio_base64": audio_base64,
        "self_report": scenario["self_report"],
        "context": scenario["context"],
    }

    assess_res = client.post(
        f"{api_url}/api/v1/assessment/run",
        json=assessment_payload,
        timeout=30.0,
    )
    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 1)

    if assess_res.status_code not in (200, 201):
        return {
            "id": scenario["id"],
            "name": scenario["name"],
            "status": "FAIL",
            "error": assess_res.text,
            "duration_ms": elapsed_ms,
        }

    result = assess_res.json()
    expected = scenario["expected"]

    # Evaluate assertions
    band_ok = result["risk_band"] in expected["acceptable_bands"]
    override_ok = result["safety_override"] == expected["expected_safety_override"]
    status_ok = True
    if "acceptable_statuses" in expected:
        status_ok = result["assessment_status"] in expected["acceptable_statuses"]
    cov_ok = True
    if "min_evidence_coverage" in expected:
        cov_ok = result["evidence_coverage"] >= expected["min_evidence_coverage"]

    passed = band_ok and override_ok and status_ok and cov_ok

    return {
        "id": scenario["id"],
        "name": scenario["name"],
        "status": "PASS" if passed else "FAIL",
        "expected_risk_band": expected["acceptable_bands"],
        "actual_risk_band": result["risk_band"],
        "expected_safety_override": expected["expected_safety_override"],
        "actual_safety_override": result["safety_override"],
        "svi": result.get("svi"),
        "confidence": result.get("confidence"),
        "evidence_coverage": result.get("evidence_coverage"),
        "assessment_status": result.get("assessment_status"),
        "case_id": result.get("case_id"),
        "duration_ms": elapsed_ms,
    }


def main():
    parser = argparse.ArgumentParser(description="Run SIH 2026 demo scenarios")
    parser.add_argument("--api-url", default="http://localhost:8000", help="FastAPI backend URL")
    parser.add_argument("--output", default="tools/demo_results.json", help="Output JSON results path")
    args = parser.parse_args()

    print(f"=== SAATHI-AI: SIH 2026 Demo Scenario Suite ===")
    print(f"Target API: {args.api_url}")
    print(f"Scenarios: {len(SCENARIOS)}\n")

    results: List[Dict[str, Any]] = []
    with httpx.Client() as client:
        for sc in SCENARIOS:
            print(f"Running Scenario {sc['id']}: {sc['name']} ... ", end="", flush=True)
            try:
                res = run_scenario(client, args.api_url, sc)
                results.append(res)
                print(f"[{res['status']}] ({res['duration_ms']}ms) -> Band: {res.get('actual_risk_band')}, Override: {res.get('actual_safety_override')}")
            except Exception as e:
                print(f"[ERROR] {e}")
                results.append({
                    "id": sc["id"],
                    "name": sc["name"],
                    "status": "ERROR",
                    "error": str(e),
                })

    passed_count = sum(1 for r in results if r.get("status") == "PASS")
    total_count = len(results)

    summary = {
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "api_url": args.api_url,
        "scenarios": results,
        "summary": {
            "total": total_count,
            "passed": passed_count,
            "failed": total_count - passed_count,
            "success_rate": f"{(passed_count / total_count) * 100:.1f}%",
        },
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\nResults saved to: {out_path.resolve()}")
    print(f"Summary: {passed_count}/{total_count} scenarios PASSED ({summary['summary']['success_rate']})")

    if passed_count < total_count:
        sys.exit(1)


if __name__ == "__main__":
    main()
