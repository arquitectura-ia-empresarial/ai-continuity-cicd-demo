#!/usr/bin/env python3
"""Orquestador conceptual de un pipeline CI/CD con continuidad ante fallo de IA."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Permite ejecutar el script directamente desde la raíz del repositorio.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.ai_review import (  # noqa: E402
    AiInvalidResponseError,
    AiReviewClient,
    AiReviewResult,
    AiUnavailableError,
    MockAiReviewClient,
    OllamaAiReviewClient,
)
from scripts.fallback_review import FallbackReviewResult, run_fallback_review, scan_files  # noqa: E402
from scripts.reporting import write_json_report, write_markdown_report  # noqa: E402

SCENARIOS = ["ai-ok", "ai-timeout", "ai-invalid", "ai-disabled", "high-risk"]
AI_PROVIDERS = ["mock", "ollama"]
DEFAULT_CHANGED_FILES = [
    "src/demo_app/calculator.py",
    "tests/test_calculator.py",
    "scripts/run_ci_demo.py",
]


def load_policy(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_unit_tests() -> str:
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return "passed"
    print(result.stdout)
    print(result.stderr, file=sys.stderr)
    return "failed"


def validate_ai_result(result: AiReviewResult, minimum_confidence: float) -> None:
    valid_risks = {"low", "medium", "high"}
    if result.risk not in valid_risks:
        raise AiInvalidResponseError("AI_RESPONSE_UNKNOWN_RISK")
    if result.confidence < minimum_confidence:
        raise AiInvalidResponseError("AI_RESPONSE_CONFIDENCE_BELOW_THRESHOLD")
    if not result.summary.strip():
        raise AiInvalidResponseError("AI_RESPONSE_EMPTY_SUMMARY")


def empty_fallback() -> FallbackReviewResult:
    return FallbackReviewResult(
        activated=False,
        reason="NOT_NEEDED",
        findings=[],
        summary="La IA estaba disponible y cumplió el contrato esperado.",
        manual_review_required=False,
    )


def build_ai_client(
    *,
    ai_provider: str,
    scenario: str,
    ollama_base_url: str,
    ollama_model: str,
    ai_timeout_seconds: int,
) -> AiReviewClient:
    if ai_provider == "ollama":
        return OllamaAiReviewClient(
            root=ROOT,
            base_url=ollama_base_url,
            model=ollama_model,
            timeout_seconds=ai_timeout_seconds,
        )
    return MockAiReviewClient(scenario=scenario)


def build_decision(
    *,
    policy: dict[str, Any],
    unit_tests: str,
    ai_result: AiReviewResult | None,
    fallback_result: FallbackReviewResult,
    deterministic_findings: list[dict[str, Any]],
) -> dict[str, Any]:
    blockers = [finding for finding in deterministic_findings if finding["severity"] == "BLOCKER"]

    if unit_tests != "passed":
        return {
            "pipeline_can_continue": False,
            "deployment_allowed": False,
            "manual_review_required": True,
            "reason": "UNIT_TESTS_FAILED",
        }

    if blockers:
        return {
            "pipeline_can_continue": False,
            "deployment_allowed": False,
            "manual_review_required": True,
            "reason": "DETERMINISTIC_BLOCKERS_FOUND",
        }

    if fallback_result.activated:
        return {
            "pipeline_can_continue": True,
            "deployment_allowed": bool(policy["deployment_allowed_when_fallback_active"]),
            "manual_review_required": True,
            "reason": fallback_result.reason,
        }

    if ai_result and ai_result.blocking:
        return {
            "pipeline_can_continue": True,
            "deployment_allowed": bool(policy["deployment_allowed_when_ai_risk_is_high"]),
            "manual_review_required": True,
            "reason": "AI_BLOCKING_REVIEW",
        }

    return {
        "pipeline_can_continue": True,
        "deployment_allowed": True,
        "manual_review_required": False,
        "reason": "ALL_GATES_PASSED",
    }


def run_pipeline(
    *,
    scenario: str,
    ai_provider: str,
    ollama_base_url: str,
    ollama_model: str,
    ai_timeout_seconds: int,
    reports_dir: Path,
) -> dict[str, Any]:
    policy = load_policy(ROOT / "config" / "continuity_policy.json")
    changed_files = DEFAULT_CHANGED_FILES

    unit_tests = run_unit_tests()
    deterministic_findings = [
        finding.to_dict()
        for finding in scan_files(
            ROOT,
            changed_files,
            policy["blocking_static_patterns"],
            policy["warning_static_patterns"],
        )
    ]

    ai_result: AiReviewResult | None = None
    ai_error: str | None = None
    fallback_result = empty_fallback()

    try:
        client = build_ai_client(
            ai_provider=ai_provider,
            scenario=scenario,
            ollama_base_url=ollama_base_url,
            ollama_model=ollama_model,
            ai_timeout_seconds=ai_timeout_seconds,
        )
        ai_result = client.review(changed_files)
        validate_ai_result(ai_result, policy["minimum_ai_confidence"])
    except AiUnavailableError as exc:
        ai_error = str(exc)
        fallback_result = run_fallback_review(
            root=ROOT,
            changed_files=changed_files,
            blocking_patterns=policy["blocking_static_patterns"],
            warning_patterns=policy["warning_static_patterns"],
            reason=ai_error,
            manual_review_required=bool(policy["manual_review_required_when_ai_unavailable"]),
        )
    except AiInvalidResponseError as exc:
        ai_error = str(exc)
        fallback_result = run_fallback_review(
            root=ROOT,
            changed_files=changed_files,
            blocking_patterns=policy["blocking_static_patterns"],
            warning_patterns=policy["warning_static_patterns"],
            reason=ai_error,
            manual_review_required=bool(policy["manual_review_required_when_ai_invalid"]),
        )

    fallback_findings = [finding.to_dict() for finding in fallback_result.findings]
    merged_findings = deterministic_findings if not fallback_findings else fallback_findings

    decision = build_decision(
        policy=policy,
        unit_tests=unit_tests,
        ai_result=ai_result,
        fallback_result=fallback_result,
        deterministic_findings=merged_findings,
    )

    ai_payload: dict[str, Any]
    if ai_result:
        ai_payload = ai_result.to_dict()
        ai_payload["enabled"] = scenario != "ai-disabled" or ai_provider == "ollama"
        ai_payload["error"] = None
    else:
        ai_payload = {
            "enabled": scenario != "ai-disabled" or ai_provider == "ollama",
            "available": False,
            "provider": ai_provider,
            "model": ollama_model if ai_provider == "ollama" else "mock-reviewer-1",
            "confidence": None,
            "risk": None,
            "blocking": False,
            "summary": "La IA no produjo una respuesta utilizable.",
            "recommendations": [],
            "error": ai_error,
        }

    payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scenario": scenario,
        "ai_provider": ai_provider,
        "changed_files": changed_files,
        "ai": ai_payload,
        "fallback": fallback_result.to_dict(),
        "quality": {
            "unit_tests": unit_tests,
            "static_findings": merged_findings,
        },
        "decision": decision,
    }

    reports_dir.mkdir(parents=True, exist_ok=True)
    write_json_report(reports_dir / "audit-report.json", payload)
    write_markdown_report(reports_dir / "audit-report.md", payload)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run AI continuity CI/CD demo")
    parser.add_argument("--scenario", choices=SCENARIOS, default=os.getenv("AI_DEMO_SCENARIO", "ai-ok"))
    parser.add_argument("--ai-provider", choices=AI_PROVIDERS, default=os.getenv("AI_PROVIDER", "mock"))
    parser.add_argument("--ollama-base-url", default=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    parser.add_argument("--ollama-model", default=os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b"))
    parser.add_argument(
        "--ai-timeout-seconds",
        default=int(os.getenv("AI_TIMEOUT_SECONDS", "60")),
        type=int,
    )
    parser.add_argument("--reports-dir", default="reports", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = run_pipeline(
        scenario=args.scenario,
        ai_provider=args.ai_provider,
        ollama_base_url=args.ollama_base_url,
        ollama_model=args.ollama_model,
        ai_timeout_seconds=args.ai_timeout_seconds,
        reports_dir=args.reports_dir,
    )
    decision = payload["decision"]

    print("AI Continuity CI/CD Demo")
    print(f"Scenario: {payload['scenario']}")
    print(f"AI provider: {payload['ai_provider']}")
    print(f"AI model: {payload['ai']['model']}")
    print(f"AI available: {payload['ai']['available']}")
    print(f"Fallback activated: {payload['fallback']['activated']}")
    print(f"Manual review required: {decision['manual_review_required']}")
    print(f"Deployment allowed: {decision['deployment_allowed']}")
    print(f"Decision reason: {decision['reason']}")
    print(f"Reports written to: {args.reports_dir}")

    # El pipeline solo falla aquí si los gates deterministas fallan.
    # La indisponibilidad de IA no rompe el proceso: activa fallback.
    return 0 if decision["pipeline_can_continue"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
