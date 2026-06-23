"""Revisión determinista de fallback.

Esta revisión no pretende sustituir una revisión humana ni una herramienta real
SAST/QA. Su objetivo es mostrar que, si la IA falla, el pipeline puede activar
un modo degradado con reglas explícitas, trazabilidad y revisión manual.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class StaticFinding:
    severity: str
    file: str
    line: int
    pattern: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "file": self.file,
            "line": self.line,
            "pattern": self.pattern,
            "message": self.message,
        }


@dataclass(frozen=True)
class FallbackReviewResult:
    activated: bool
    reason: str
    findings: list[StaticFinding]
    summary: str
    manual_review_required: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "activated": self.activated,
            "reason": self.reason,
            "findings": [finding.to_dict() for finding in self.findings],
            "summary": self.summary,
            "manual_review_required": self.manual_review_required,
        }


def scan_files(
    root: Path,
    changed_files: list[str],
    blocking_patterns: list[str],
    warning_patterns: list[str],
) -> list[StaticFinding]:
    findings: list[StaticFinding] = []
    for relative in changed_files:
        path = root / relative
        if not path.exists() or not path.is_file():
            continue
        if path.suffix not in {".py", ".yml", ".yaml", ".json", ".md"}:
            continue

        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for pattern in blocking_patterns:
                if pattern in line:
                    findings.append(
                        StaticFinding(
                            severity="BLOCKER",
                            file=relative,
                            line=line_number,
                            pattern=pattern,
                            message="Patrón determinista bloqueante detectado.",
                        )
                    )
            for pattern in warning_patterns:
                if pattern in line:
                    findings.append(
                        StaticFinding(
                            severity="WARNING",
                            file=relative,
                            line=line_number,
                            pattern=pattern,
                            message="Patrón de aviso detectado; requiere revisión si el contexto lo justifica.",
                        )
                    )
    return findings


def run_fallback_review(
    *,
    root: Path,
    changed_files: list[str],
    blocking_patterns: list[str],
    warning_patterns: list[str],
    reason: str,
    manual_review_required: bool,
) -> FallbackReviewResult:
    findings = scan_files(root, changed_files, blocking_patterns, warning_patterns)
    blockers = [finding for finding in findings if finding.severity == "BLOCKER"]

    if blockers:
        summary = "Fallback activado: se han detectado hallazgos bloqueantes mediante reglas deterministas."
    else:
        summary = "Fallback activado: no hay bloqueos deterministas, pero se requiere revisión humana por indisponibilidad o invalidez de la IA."

    return FallbackReviewResult(
        activated=True,
        reason=reason,
        findings=findings,
        summary=summary,
        manual_review_required=manual_review_required,
    )
