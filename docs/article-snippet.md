# Texto sugerido para enlazar desde el artículo

He preparado un pequeño ejemplo conceptual en GitHub para acompañar este artículo: un pipeline CI/CD básico donde la IA puede participar en una revisión, pero no se convierte en un punto único de fallo.

El ejemplo permite simular varios escenarios: IA disponible, timeout, respuesta inválida, IA desactivada y riesgo alto. En cada caso se genera un informe auditable y el pipeline decide de forma explícita si puede continuar, si debe activar fallback, si requiere revisión humana y si el despliegue automático queda permitido.

La idea no es construir un framework ni proponer que la IA apruebe despliegues por sí sola. La idea es mostrar un principio arquitectónico: si la IA entra en un proceso empresarial, también hay que diseñar qué ocurre cuando falla.
