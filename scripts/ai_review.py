"""Clientes de revisión asistida por IA para la demo.

La demo soporta dos modos:

- MockAiReviewClient: simulado, determinista y reproducible.
- OllamaAiReviewClient: integración local opcional contra Ollama.

La idea arquitectónica es que el pipeline dependa de un contrato estable
(AiReviewClient.review), no de un proveedor concreto.
"""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


class AiUnavailableError(RuntimeError):
    """La IA no está disponible o no debe usarse."""


class AiInvalidResponseError(RuntimeError):
    """La IA ha devuelto una respuesta que no cumple el contrato esperado."""


@dataclass(frozen=True)
class AiReviewResult:
    available: bool
    provider: str
    model: str
    confidence: float
    risk: str
    blocking: bool
    summary: str
    recommendations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "available": self.available,
            "provider": self.provider,
            "model": self.model,
            "confidence": self.confidence,
            "risk": self.risk,
            "blocking": self.blocking,
            "summary": self.summary,
            "recommendations": self.recommendations,
        }


class AiReviewClient(Protocol):
    def review(self, changed_files: list[str]) -> AiReviewResult:
        """Devuelve una revisión IA estructurada o lanza una excepción controlada."""


class MockAiReviewClient:
    """Cliente simulado con escenarios deterministas."""

    def __init__(self, scenario: str) -> None:
        self.scenario = scenario

    def review(self, changed_files: list[str]) -> AiReviewResult:
        if self.scenario == "ai-timeout":
            raise AiUnavailableError("AI_TIMEOUT")
        if self.scenario == "ai-disabled":
            raise AiUnavailableError("AI_DISABLED_BY_CONFIGURATION")
        if self.scenario == "ai-invalid":
            raise AiInvalidResponseError("AI_RESPONSE_SCHEMA_VALIDATION_ERROR")
        if self.scenario == "high-risk":
            return AiReviewResult(
                available=True,
                provider="mock-provider",
                model="mock-reviewer-1",
                confidence=0.91,
                risk="high",
                blocking=True,
                summary="La IA detecta un cambio potencialmente crítico y recomienda revisión manual antes de desplegar.",
                recommendations=[
                    "Solicitar aprobación de una persona responsable.",
                    "Revisar impacto sobre datos, seguridad y operación.",
                    "No permitir despliegue automático en este escenario.",
                ],
            )

        return AiReviewResult(
            available=True,
            provider="mock-provider",
            model="mock-reviewer-1",
            confidence=0.84,
            risk="medium",
            blocking=False,
            summary="La IA no detecta bloqueos, pero recomienda mantener la revisión determinista y trazabilidad.",
            recommendations=[
                "Conservar informe de auditoría como artefacto del pipeline.",
                "Mantener reglas deterministas aunque la IA esté disponible.",
                "No usar la IA como única condición de despliegue.",
            ],
        )


class OllamaAiReviewClient:
    """Cliente opcional para revisar cambios usando un modelo local servido por Ollama.

    Esta implementación no es necesaria para ejecutar la demo. Existe para quien
    quiera probar el mismo contrato con una IA local real, por ejemplo Qwen.
    """

    REVIEW_SCHEMA: dict[str, Any] = {
        "type": "object",
        "properties": {
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "risk": {"type": "string", "enum": ["low", "medium", "high"]},
            "blocking": {"type": "boolean"},
            "summary": {"type": "string"},
            "recommendations": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "maxItems": 5,
            },
        },
        "required": ["confidence", "risk", "blocking", "summary", "recommendations"],
    }

    def __init__(
        self,
        *,
        root: Path,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5:1.5b",
        timeout_seconds: int = 60,
        max_chars_per_file: int = 6000,
    ) -> None:
        self.root = root
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_chars_per_file = max_chars_per_file

    def review(self, changed_files: list[str]) -> AiReviewResult:
        prompt = self._build_prompt(changed_files)
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": self.REVIEW_SCHEMA,
            "options": {
                "temperature": 0.1,
                "num_ctx": 8192,
            },
        }

        try:
            response = self._post_json("/api/generate", payload)
        except (TimeoutError, socket.timeout) as exc:
            raise AiUnavailableError("OLLAMA_TIMEOUT") from exc
        except urllib.error.URLError as exc:
            raise AiUnavailableError(f"OLLAMA_UNAVAILABLE: {exc.reason}") from exc
        except urllib.error.HTTPError as exc:
            raise AiUnavailableError(f"OLLAMA_HTTP_ERROR: {exc.code}") from exc

        raw_model_response = response.get("response")
        if not isinstance(raw_model_response, str) or not raw_model_response.strip():
            raise AiInvalidResponseError("OLLAMA_EMPTY_RESPONSE")

        parsed = self._parse_model_json(raw_model_response)
        return self._to_review_result(parsed)

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            url=f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310 - demo local URL
            body = response.read().decode("utf-8")
        return json.loads(body)

    def _build_prompt(self, changed_files: list[str]) -> str:
        files_payload = []
        for relative in changed_files:
            path = self.root / relative
            if not path.exists() or not path.is_file():
                continue
            content = path.read_text(encoding="utf-8", errors="replace")
            files_payload.append(
                {
                    "file": relative,
                    "content_excerpt": content[: self.max_chars_per_file],
                    "truncated": len(content) > self.max_chars_per_file,
                }
            )

        return (
            "Actúa como revisor técnico de un pipeline CI/CD. "
            "Tu tarea NO es aprobar despliegues de forma autónoma. "
            "Debes analizar los ficheros modificados y devolver exclusivamente JSON válido.\n\n"
            "Contrato obligatorio de respuesta:\n"
            "{\n"
            '  "confidence": número entre 0 y 1,\n'
            '  "risk": "low" | "medium" | "high",\n'
            '  "blocking": boolean,\n'
            '  "summary": texto breve en español,\n'
            '  "recommendations": lista de 1 a 5 recomendaciones en español\n'
            "}\n\n"
            "Criterios:\n"
            "- Marca risk=high y blocking=true si ves cambios peligrosos, inseguros o no auditables.\n"
            "- Marca risk=medium si no hay bloqueo claro pero conviene revisión.\n"
            "- Marca risk=low solo si el cambio parece claramente seguro y menor.\n"
            "- No inventes hechos externos. Basa la revisión solo en los fragmentos proporcionados.\n"
            "- Devuelve solo JSON. Sin Markdown. Sin texto adicional.\n\n"
            f"Ficheros modificados:\n{json.dumps(files_payload, ensure_ascii=False, indent=2)}"
        )

    def _parse_model_json(self, raw: str) -> dict[str, Any]:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AiInvalidResponseError("OLLAMA_RESPONSE_NOT_JSON") from exc
        if not isinstance(parsed, dict):
            raise AiInvalidResponseError("OLLAMA_RESPONSE_NOT_OBJECT")
        return parsed

    def _to_review_result(self, parsed: dict[str, Any]) -> AiReviewResult:
        try:
            confidence = float(parsed["confidence"])
            risk = str(parsed["risk"])
            blocking = bool(parsed["blocking"])
            summary = str(parsed["summary"]).strip()
            recommendations_raw = parsed["recommendations"]
        except (KeyError, TypeError, ValueError) as exc:
            raise AiInvalidResponseError("OLLAMA_RESPONSE_SCHEMA_VALIDATION_ERROR") from exc

        if not 0 <= confidence <= 1:
            raise AiInvalidResponseError("OLLAMA_RESPONSE_CONFIDENCE_OUT_OF_RANGE")
        if risk not in {"low", "medium", "high"}:
            raise AiInvalidResponseError("OLLAMA_RESPONSE_UNKNOWN_RISK")
        if not summary:
            raise AiInvalidResponseError("OLLAMA_RESPONSE_EMPTY_SUMMARY")
        if not isinstance(recommendations_raw, list) or not recommendations_raw:
            raise AiInvalidResponseError("OLLAMA_RESPONSE_EMPTY_RECOMMENDATIONS")

        recommendations = [str(item).strip() for item in recommendations_raw if str(item).strip()]
        if not recommendations:
            raise AiInvalidResponseError("OLLAMA_RESPONSE_EMPTY_RECOMMENDATIONS")

        return AiReviewResult(
            available=True,
            provider="ollama",
            model=self.model,
            confidence=confidence,
            risk=risk,
            blocking=blocking,
            summary=summary,
            recommendations=recommendations[:5],
        )
