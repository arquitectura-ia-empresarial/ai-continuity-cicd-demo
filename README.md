# AI Continuity CI/CD Demo

Ejemplo conceptual, ejecutable y auditable para acompañar el artículo **"¿Qué pasa si la IA se apaga?"**.

La idea del repositorio es sencilla:

> La IA puede aportar valor dentro de un pipeline CI/CD, pero el pipeline no debería depender ciegamente de ella.

Este ejemplo muestra un pipeline donde una revisión asistida por IA puede estar disponible, fallar, devolver una respuesta inválida o detectar un riesgo alto. En todos los casos, el sistema genera un informe trazable y toma una decisión explícita sobre continuidad, fallback, revisión humana y despliegue.

El repositorio tiene dos modos de ejecución:

1. **Modo simulado (`mock`)**: reproducible, sin claves, sin Docker y sin servicios externos.
2. **Modo local real (`ollama`)**: opcional, usando Ollama y un modelo local como Qwen mediante Docker Compose.

---

## Quick Start

Si solo quieres ver la idea funcionando sin instalar nada más que Python:

```bash
git clone https://github.com/<tu-usuario>/ai-continuity-cicd-demo.git
cd ai-continuity-cicd-demo

python -m unittest discover -s tests
python scripts/run_ci_demo.py --scenario ai-timeout --reports-dir reports/quickstart
```

Resultado esperado:

```text
AI Continuity CI/CD Demo
Scenario: ai-timeout
AI provider: mock
AI model: mock-reviewer-1
AI available: False
Fallback activated: True
Manual review required: True
Deployment allowed: False
Decision reason: AI_TIMEOUT
Reports written to: reports/quickstart
```

La IA ha fallado, pero el proceso no se ha caído. Ha generado evidencias, ha activado fallback y ha bloqueado el despliegue automático hasta revisión humana.

---

## Qué modo usar

| Modo | Cuándo usarlo | Requisitos | Qué demuestra |
|---|---|---|---|
| `mock` | Para entender el ejemplo, probar todos los escenarios y ejecutarlo en CI sin dependencias externas | Python 3.10+ | Continuidad, fallback, contrato, auditoría y deployment gate de forma reproducible |
| `ollama` | Para probar una IA local real manteniendo la misma arquitectura | Docker, Docker Compose, memoria suficiente y descarga inicial del modelo | Que incluso con una IA real el pipeline sigue validando contrato y degradando de forma controlada |

Recomendación:

- Usa **`mock`** para documentación, demos, pruebas automáticas y GitHub Actions.
- Usa **`ollama`** si quieres experimentar con un modelo local real.
- Prueba **`ollama` sin Ollama levantado** para comprobar que el fallo de la IA activa fallback.

---

## Probar todos los escenarios en modo simulado

El modo simulado es el modo base del repositorio. No requiere claves, Docker ni servicios externos.

```bash
python scripts/run_ci_demo.py --scenario ai-ok --reports-dir reports/ai-ok
python scripts/run_ci_demo.py --scenario ai-timeout --reports-dir reports/ai-timeout
python scripts/run_ci_demo.py --scenario ai-invalid --reports-dir reports/ai-invalid
python scripts/run_ci_demo.py --scenario ai-disabled --reports-dir reports/ai-disabled
python scripts/run_ci_demo.py --scenario high-risk --reports-dir reports/high-risk
```

### Tabla rápida de escenarios

| Escenario | Qué simula | IA disponible | Fallback | Revisión humana | Despliegue automático |
|---|---|---:|---:|---:|---:|
| `ai-ok` | La IA responde correctamente | Sí | No | No | Permitido |
| `ai-timeout` | La IA no responde | No | Sí | Sí | Bloqueado |
| `ai-invalid` | La IA devuelve una respuesta inválida | No utilizable | Sí | Sí | Bloqueado |
| `ai-disabled` | La IA está desactivada por configuración | No | Sí | Sí | Bloqueado |
| `high-risk` | La IA detecta riesgo alto | Sí | No | Sí | Bloqueado |

---

## Probar con Ollama mediante Docker Compose

El modo Ollama permite conectar una IA local real sin usar claves de API ni servicios cloud.

### 1. Copiar configuración

```bash
cp .env.example .env
```

Modelo por defecto:

```text
qwen2.5:1.5b
```

Puedes cambiarlo en `.env`:

```text
OLLAMA_MODEL=qwen2.5:0.5b
OLLAMA_MODEL=qwen2.5:1.5b
OLLAMA_MODEL=qwen2.5:7b
```

### 2. Levantar Ollama

```bash
docker compose up -d ollama
```

### 3. Descargar el modelo configurado

```bash
docker compose run --rm pull-model
```

La primera descarga puede tardar según el modelo y la conexión.

### 4. Ejecutar la demo con Ollama dentro de Docker

```bash
docker compose run --rm demo-ollama
```

Los informes se generan en:

```text
reports/ollama/
 ├── audit-report.json
 └── audit-report.md
```

---

## Ejecutar Python local contra Ollama en Docker

También puedes levantar solo Ollama con Docker y ejecutar el script desde tu máquina:

```bash
docker compose up -d ollama
docker compose run --rm pull-model

python scripts/run_ci_demo.py \
  --ai-provider ollama \
  --ollama-base-url http://localhost:11434 \
  --ollama-model qwen2.5:1.5b \
  --reports-dir reports/ollama-local
```

En este modo el escenario indicado por `--scenario` no fuerza respuestas simuladas. La revisión la realiza el modelo local a través de Ollama.

---

## Probar un fallo real de IA con Ollama

Esta prueba es importante porque conecta directamente con el artículo.

Ejecuta el cliente Ollama sin tener Ollama levantado:

```bash
docker compose down

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

Esto demuestra el punto central:

> El fallo de la IA no debe tumbar el proceso. Debe activar una degradación controlada.

---

## Comandos útiles

| Objetivo | Comando |
|---|---|
| Ejecutar tests | `python -m unittest discover -s tests` |
| Ejecutar escenario normal simulado | `python scripts/run_ci_demo.py --scenario ai-ok --reports-dir reports/ai-ok` |
| Simular caída de IA | `python scripts/run_ci_demo.py --scenario ai-timeout --reports-dir reports/ai-timeout` |
| Simular respuesta inválida | `python scripts/run_ci_demo.py --scenario ai-invalid --reports-dir reports/ai-invalid` |
| Simular IA desactivada | `python scripts/run_ci_demo.py --scenario ai-disabled --reports-dir reports/ai-disabled` |
| Simular riesgo alto | `python scripts/run_ci_demo.py --scenario high-risk --reports-dir reports/high-risk` |
| Levantar Ollama | `docker compose up -d ollama` |
| Descargar modelo Ollama | `docker compose run --rm pull-model` |
| Ejecutar demo con Ollama en Docker | `docker compose run --rm demo-ollama` |
| Apagar Ollama | `docker compose down` |

---

## Qué demuestra este repositorio

Este repositorio no pretende ser un framework de CI/CD ni una solución cerrada de revisión de código con IA.

Pretende demostrar un principio arquitectónico:

> Una integración empresarial de IA debe poder degradarse de forma controlada.

El ejemplo cubre:

- ejecución de tests deterministas,
- revisión simulada por IA,
- revisión opcional con IA local mediante Ollama,
- validación del contrato de respuesta de la IA,
- fallback determinista si la IA no está disponible,
- activación de revisión humana,
- bloqueo del despliegue automático cuando procede,
- generación de informes de auditoría en JSON y Markdown,
- workflow de GitHub Actions,
- Jenkinsfile equivalente,
- Docker Compose para ejecutar Ollama localmente.

---

## Flujo conceptual

```text
checkout
  ↓
unit tests
  ↓
static deterministic review
  ↓
AI assisted review
  ↓
AI response contract validation
  ↓
fallback if AI is unavailable or invalid
  ↓
audit report
  ↓
deployment gate
```

La IA participa en el proceso, pero no es el único mecanismo de control.

---

## Requisitos

### Modo simulado

- Python 3.10 o superior.
- No requiere claves de API.
- No llama a servicios externos.
- No necesita Docker.
- No necesita instalar dependencias externas.

### Modo Ollama

- Docker y Docker Compose.
- Memoria suficiente para cargar el modelo elegido.
- Conexión a Internet la primera vez para descargar el modelo.
- No requiere claves de API.

---

## Contrato de respuesta de la IA

Tanto el modo simulado como el modo Ollama usan el mismo contrato conceptual.

La IA debe devolver un objeto JSON con esta forma:

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

Campos:

| Campo | Descripción |
|---|---|
| `confidence` | Confianza declarada por la IA, entre 0 y 1 |
| `risk` | `low`, `medium` o `high` |
| `blocking` | Indica si la IA considera que el cambio debe bloquear despliegue automático |
| `summary` | Resumen breve de la revisión |
| `recommendations` | Recomendaciones operativas |

Si el modelo no cumple el contrato, la respuesta se descarta y se activa fallback.

---

## Informes generados

Cada ejecución genera:

```text
reports/<escenario-o-modo>/
 ├── audit-report.json
 └── audit-report.md
```

El informe JSON contiene una estructura como esta:

```json
{
  "scenario": "ai-timeout",
  "ai_provider": "mock",
  "ai": {
    "enabled": true,
    "available": false,
    "provider": "mock",
    "model": "mock-reviewer-1",
    "error": "AI_TIMEOUT"
  },
  "fallback": {
    "activated": true,
    "reason": "AI_TIMEOUT",
    "manual_review_required": true
  },
  "decision": {
    "pipeline_can_continue": true,
    "deployment_allowed": false,
    "manual_review_required": true,
    "reason": "AI_TIMEOUT"
  }
}
```

El informe Markdown está pensado para ser leído por una persona, adjuntado como artefacto del pipeline o publicado como comentario en una pull request.

---

## Ejemplos pre-generados

El repositorio incluye informes de ejemplo en:

```text
reports/examples/
 ├── ai-ok/
 ├── ai-timeout/
 ├── ai-invalid/
 ├── ai-disabled/
 ├── high-risk/
 └── ollama-unavailable/
```

Estos ficheros permiten entender el resultado sin ejecutar nada.

---

## Política de continuidad

La política se define en:

```text
config/continuity_policy.json
```

Ejemplo:

```json
{
  "minimum_ai_confidence": 0.70,
  "manual_review_required_when_ai_unavailable": true,
  "manual_review_required_when_ai_invalid": true,
  "deployment_allowed_when_fallback_active": false,
  "deployment_allowed_when_ai_risk_is_high": false
}
```

Esto permite expresar una decisión importante:

> El pipeline puede continuar si la IA falla, pero el despliegue automático no queda permitido sin revisión humana.

---

## GitHub Actions

El repositorio incluye un workflow en:

```text
.github/workflows/ai-continuity-demo.yml
```

Puedes ejecutarlo manualmente desde la pestaña **Actions** y elegir:

- escenario,
- proveedor de IA,
- modelo Ollama.

En GitHub Actions se recomienda usar `mock` como proveedor, porque es reproducible y no necesita servicios locales.

Si eliges `ollama` en GitHub Actions sin levantar un servicio Ollama dentro del runner, la demo debería activar fallback. Eso también es una prueba útil: el pipeline sigue vivo aunque la IA no esté disponible.

El workflow:

1. hace checkout,
2. prepara Python,
3. ejecuta tests,
4. ejecuta la demo de continuidad,
5. evalúa el deployment gate,
6. publica los informes como artefactos.

---

## Jenkins

También se incluye un `Jenkinsfile` conceptual para entornos donde el CI/CD no está basado en GitHub Actions.

Parámetros disponibles:

```text
AI_DEMO_SCENARIO
AI_PROVIDER
OLLAMA_BASE_URL
OLLAMA_MODEL
```

Valores habituales:

```text
AI_DEMO_SCENARIO = ai-ok | ai-timeout | ai-invalid | ai-disabled | high-risk
AI_PROVIDER      = mock | ollama
OLLAMA_BASE_URL  = http://localhost:11434
OLLAMA_MODEL     = qwen2.5:1.5b
```

El pipeline Jenkins ejecuta las mismas fases:

```text
Checkout
Unit tests
AI continuity review
Deployment gate
Archive artifacts
```

---

## Por qué conservar el modo simulado

Aunque el repositorio permite usar Ollama, el modo simulado sigue siendo importante.

La IA simulada permite que el ejemplo sea:

- reproducible,
- barato,
- ejecutable sin claves,
- independiente de hardware,
- independiente de proveedores,
- útil para explicar arquitectura, no consumo de APIs.

El modo Ollama añade realismo, pero también introduce incertidumbre: latencia, descarga de modelos, memoria disponible y variabilidad en la respuesta del modelo.

Por eso el diseño mantiene ambas opciones.

---

## Aislamiento del proveedor de IA

La interfaz está aislada en:

```text
scripts/ai_review.py
```

La clase relevante es:

```python
class AiReviewClient(Protocol):
    def review(self, changed_files: list[str]) -> AiReviewResult:
        ...
```

Implementaciones incluidas:

```text
MockAiReviewClient
OllamaAiReviewClient
```

Implementaciones posibles:

```text
OpenAiReviewClient
AzureOpenAiReviewClient
AnthropicReviewClient
LocalLlamaCppReviewClient
DisabledAiReviewClient
```

La arquitectura importante es esta:

> El pipeline depende del contrato, no de un proveedor concreto.

---

## Qué NO hace este repositorio

Este repositorio no hace despliegues reales.

No ejecuta análisis de seguridad real.

No sustituye una estrategia de CI/CD empresarial.

No demuestra que una IA sea fiable para aprobar código.

No propone que la IA decida despliegues de forma autónoma.

El objetivo es más concreto:

> Mostrar cómo tratar la IA como una dependencia operativa que puede fallar.

---

## Lectura arquitectónica

Este ejemplo separa varias responsabilidades:

| Pieza | Responsabilidad |
|---|---|
| `tests/` | Validación determinista clásica |
| `scripts/ai_review.py` | Contrato de revisión asistida por IA y clientes `mock`/`ollama` |
| `scripts/fallback_review.py` | Reglas de fallback cuando la IA no está disponible |
| `scripts/run_ci_demo.py` | Orquestación del flujo |
| `scripts/reporting.py` | Evidencias y trazabilidad |
| `scripts/deployment_gate.py` | Decisión explícita sobre despliegue automático |
| `config/continuity_policy.json` | Política configurable de continuidad |
| `docker-compose.yml` | Ejecución opcional de Ollama local |

La decisión final no depende únicamente de lo que diga la IA.

Depende de:

- tests,
- reglas deterministas,
- disponibilidad de IA,
- validez de la respuesta,
- nivel de riesgo,
- política de continuidad,
- necesidad de revisión humana.

---

## Documentación adicional

```text
docs/
 ├── architecture.md
 ├── ollama.md
```

---

## Relación con el artículo

Este repositorio ilustra técnicamente la tesis del artículo:

> La IA empresarial no va de magia. Va de sistemas.

Y los sistemas serios no solo se diseñan para funcionar.

También se diseñan para fallar bien.

---

## Posibles ampliaciones

Ideas para evolucionar el ejemplo:

- añadir comentarios automáticos en pull requests,
- generar tickets si se activa fallback,
- integrar una herramienta SAST real,
- enviar informes a un sistema de auditoría,
- usar aprobación manual en entornos protegidos,
- añadir métricas de disponibilidad de IA,
- probar varios proveedores de IA detrás del mismo contrato,
- añadir pruebas de caos simulando timeouts y respuestas inválidas,
- añadir una variante con Kubernetes y health checks,
- añadir publicación de métricas en Prometheus/Grafana.

---

## Referencias técnicas

- Ollama Docker: https://docs.ollama.com/docker
- Ollama API: https://github.com/ollama/ollama/blob/main/docs/api.md
- Modelo Qwen2.5 en Ollama: https://ollama.com/library/qwen2.5
- GitHub Actions: https://docs.github.com/actions
- Docker Compose: https://docs.docker.com/compose/

---

## Licencia

MIT.
