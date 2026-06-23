# Modo opcional con Ollama

El repositorio funciona por defecto con un cliente de IA simulado. Ese modo es el recomendado para entender la arquitectura porque es reproducible, rápido y no requiere servicios externos.

Además, se incluye una integración opcional con Ollama para probar el mismo contrato contra un modelo local real.

## Qué añade este modo

El flujo sigue siendo el mismo:

```text
unit tests
  ↓
static deterministic review
  ↓
AI assisted review
  ↓
contract validation
  ↓
fallback if unavailable or invalid
  ↓
audit report
  ↓
deployment gate
```

La diferencia es que la revisión IA ya no sale de `MockAiReviewClient`, sino de `OllamaAiReviewClient`, que llama a un servidor Ollama mediante HTTP.

## Requisitos

- Docker y Docker Compose.
- Memoria suficiente para cargar el modelo elegido.
- Red disponible para descargar el modelo la primera vez.

No se necesita ninguna clave de API.

## Modelo recomendado

Por defecto se usa:

```text
qwen2.5:1.5b
```

Es una opción razonable para una demo local porque no es tan pesada como un 7B, pero suele respetar mejor instrucciones estructuradas que modelos más pequeños.

Alternativas:

```text
qwen2.5:0.5b   # más ligero, menor calidad
qwen2.5:7b     # más calidad, más consumo
```

## Arranque con Docker Compose

Desde la raíz del repositorio:

```bash
cp .env.example .env
```

Levanta Ollama:

```bash
docker compose up -d ollama
```

Descarga el modelo configurado en `.env`:

```bash
docker compose run --rm pull-model
```

Ejecuta la demo dentro de Docker:

```bash
docker compose run --rm demo-ollama
```

Los informes se generan en:

```text
reports/ollama/
 ├── audit-report.json
 └── audit-report.md
```

## Ejecución local contra Ollama en Docker

También puedes levantar solo Ollama con Docker y ejecutar Python desde tu máquina:

```bash
docker compose up -d ollama
docker compose run --rm pull-model
python scripts/run_ci_demo.py \
  --ai-provider ollama \
  --ollama-base-url http://localhost:11434 \
  --ollama-model qwen2.5:1.5b \
  --reports-dir reports/ollama-local
```

## Probar el fallback real

Si ejecutas el cliente Ollama sin levantar Ollama, la demo no debería romperse de forma descontrolada. Debe activar fallback:

```bash
python scripts/run_ci_demo.py \
  --ai-provider ollama \
  --ollama-base-url http://localhost:11434 \
  --ollama-model qwen2.5:1.5b \
  --reports-dir reports/ollama-down
```

Resultado esperado:

```text
AI provider: ollama
AI available: False
Fallback activated: True
Manual review required: True
Deployment allowed: False
```

Esta es precisamente la idea del artículo: el fallo de la IA no debe tumbar el proceso; debe activar una degradación controlada.

## Contrato de respuesta

El modelo debe devolver un JSON con esta forma:

```json
{
  "confidence": 0.82,
  "risk": "medium",
  "blocking": false,
  "summary": "No se detectan bloqueos evidentes, pero conviene revisión manual.",
  "recommendations": [
    "Mantener tests deterministas.",
    "Conservar el informe de auditoría."
  ]
}
```

Si el modelo no cumple este contrato, la respuesta se descarta y se activa fallback.

## Por qué no se sustituye el modo simulado

El modo Ollama es útil para hacer la demo más realista, pero no sustituye al modo simulado.

El modo simulado sigue siendo importante porque:

- es determinista,
- sirve para CI/CD público,
- no depende de hardware,
- no requiere descargar modelos,
- permite enseñar claramente los escenarios de fallo.

El modo Ollama demuestra otra cosa:

> La arquitectura puede conectar una IA real sin cambiar la política de continuidad ni el deployment gate.
