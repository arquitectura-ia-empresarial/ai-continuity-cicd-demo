"""Generación de informes de auditoría para la demo."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_json_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _format_bool(value: bool) -> str:
    return "Sí" if value else "No"


def write_markdown_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    decision = payload["decision"]
    ai = payload["ai"]
    fallback = payload["fallback"]
    quality = payload["quality"]

    lines = [
        "# AI Continuity CI/CD Demo — Audit Report",
        "",
        f"**Scenario:** `{payload['scenario']}`",
        f"**AI provider:** `{payload.get('ai_provider', 'mock')}`",
        f"**Timestamp UTC:** `{payload['timestamp_utc']}`",
        "",
        "## Decision",
        "",
        f"- Pipeline can continue: **{_format_bool(decision['pipeline_can_continue'])}**",
        f"- Deployment allowed: **{_format_bool(decision['deployment_allowed'])}**",
        f"- Manual review required: **{_format_bool(decision['manual_review_required'])}**",
        f"- Decision reason: `{decision['reason']}`",
        "",
        "## AI status",
        "",
        f"- AI enabled: **{_format_bool(ai['enabled'])}**",
        f"- AI available: **{_format_bool(ai['available'])}**",
        f"- Provider: `{ai.get('provider', 'n/a')}`",
        f"- Model: `{ai.get('model', 'n/a')}`",
        f"- Confidence: `{ai.get('confidence', 'n/a')}`",
        f"- Risk: `{ai.get('risk', 'n/a')}`",
        f"- Blocking: **{_format_bool(ai.get('blocking', False))}**",
        f"- Summary: {ai.get('summary', 'n/a')}",
        "",
        "## Fallback",
        "",
        f"- Fallback activated: **{_format_bool(fallback['activated'])}**",
        f"- Reason: `{fallback['reason']}`",
        f"- Manual review from fallback: **{_format_bool(fallback['manual_review_required'])}**",
        f"- Summary: {fallback['summary']}",
        "",
        "## Deterministic quality gates",
        "",
        f"- Unit tests: `{quality['unit_tests']}`",
        f"- Static findings: `{len(quality['static_findings'])}`",
        "",
    ]

    if quality["static_findings"]:
        lines.extend([
            "### Static findings",
            "",
            "| Severity | File | Line | Pattern | Message |",
            "|---|---|---:|---|---|",
        ])
        for finding in quality["static_findings"]:
            lines.append(
                f"| {finding['severity']} | `{finding['file']}` | {finding['line']} | `{finding['pattern']}` | {finding['message']} |"
            )
        lines.append("")

    lines.extend([
        "## Interpretation",
        "",
        "Este informe muestra que la IA puede participar en el pipeline, pero no es la única garantía del proceso.",
        "Si la IA no está disponible o no cumple el contrato esperado, el pipeline activa un modo degradado con reglas deterministas, trazabilidad y revisión humana.",
        "",
    ])

    path.write_text("\n".join(lines), encoding="utf-8")
