# AI Continuity CI/CD Demo — Audit Report

**Scenario:** `ai-invalid`
**AI provider:** `mock`
**Timestamp UTC:** `2026-06-22T12:10:16+00:00`

## Decision

- Pipeline can continue: **Sí**
- Deployment allowed: **No**
- Manual review required: **Sí**
- Decision reason: `AI_RESPONSE_SCHEMA_VALIDATION_ERROR`

## AI status

- AI enabled: **Sí**
- AI available: **No**
- Provider: `mock`
- Model: `mock-reviewer-1`
- Confidence: `None`
- Risk: `None`
- Blocking: **No**
- Summary: La IA no produjo una respuesta utilizable.

## Fallback

- Fallback activated: **Sí**
- Reason: `AI_RESPONSE_SCHEMA_VALIDATION_ERROR`
- Manual review from fallback: **Sí**
- Summary: Fallback activado: no hay bloqueos deterministas, pero se requiere revisión humana por indisponibilidad o invalidez de la IA.

## Deterministic quality gates

- Unit tests: `passed`
- Static findings: `0`

## Interpretation

Este informe muestra que la IA puede participar en el pipeline, pero no es la única garantía del proceso.
Si la IA no está disponible o no cumple el contrato esperado, el pipeline activa un modo degradado con reglas deterministas, trazabilidad y revisión humana.
