# Arquitectura conceptual

```text
                    ┌───────────────────────────┐
                    │         CI/CD             │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │     Tests deterministas   │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │  Reglas estáticas básicas │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │      Revisión IA          │
                    │   contrato estructurado   │
                    └─────────────┬─────────────┘
                                  │
              ┌───────────────────┴────────────────────┐
              │                                        │
              ▼                                        ▼
┌──────────────────────────┐              ┌──────────────────────────┐
│ MockAiReviewClient       │              │ OllamaAiReviewClient     │
│ modo simulado            │              │ modo local real opcional │
└─────────────┬────────────┘              └─────────────┬────────────┘
              │                                        │
              └───────────────────┬────────────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │ Validación de contrato    │
                    └─────────────┬─────────────┘
                                  │
                  ┌───────────────┴────────────────┐
                  │                                │
                  ▼                                ▼
      ┌───────────────────────┐        ┌────────────────────────┐
      │ IA disponible y válida│        │ IA caída / inválida     │
      └───────────┬───────────┘        └────────────┬───────────┘
                  │                                 │
                  ▼                                 ▼
      ┌───────────────────────┐        ┌────────────────────────┐
      │ Evaluación de riesgo  │        │ Fallback determinista   │
      └───────────┬───────────┘        └────────────┬───────────┘
                  │                                 │
                  └──────────────┬──────────────────┘
                                 ▼
                  ┌──────────────────────────────┐
                  │ Informe auditable JSON/MD    │
                  └──────────────┬───────────────┘
                                 ▼
                  ┌──────────────────────────────┐
                  │ Deployment gate              │
                  │ permitir / bloquear / revisar│
                  └──────────────────────────────┘
```

## Decisión clave

El pipeline puede seguir vivo aunque la IA falle, pero el despliegue automático queda bloqueado si la política de continuidad así lo exige.

Esto permite diferenciar entre:

- caída total del proceso,
- degradación controlada,
- revisión humana,
- bloqueo de despliegue,
- trazabilidad posterior.

## Contrato antes que proveedor

La pieza central no es el proveedor de IA.

La pieza central es el contrato:

```python
class AiReviewClient(Protocol):
    def review(self, changed_files: list[str]) -> AiReviewResult:
        ...
```

Mientras una implementación respete ese contrato, el pipeline puede cambiar de proveedor sin rediseñar la política de continuidad.

```text
MockAiReviewClient
OllamaAiReviewClient
OpenAiReviewClient
AzureOpenAiReviewClient
DisabledAiReviewClient
```

## Por qué validar la respuesta

Una IA puede responder, pero eso no significa que la respuesta sea usable.

Por eso la demo valida:

- que la salida sea JSON,
- que contenga los campos esperados,
- que el riesgo sea `low`, `medium` o `high`,
- que la confianza cumpla el umbral mínimo,
- que exista un resumen,
- que haya recomendaciones.

Si algo falla, no se fuerza el uso de la respuesta.

Se activa fallback.

## Fallback no significa éxito automático

Cuando se activa fallback, el pipeline puede continuar para generar evidencias y no perder trazabilidad.

Pero eso no implica permitir despliegue automático.

La política por defecto es:

```json
{
  "deployment_allowed_when_fallback_active": false
}
```

Es decir:

> El proceso no se cae, pero el despliegue queda bloqueado hasta revisión humana.
