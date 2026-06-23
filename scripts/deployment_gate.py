#!/usr/bin/env python3
"""Gate conceptual de despliegue.

Lee reports/audit-report.json y decide si el despliegue automático estaría
permitido. En una plataforma real, este paso podría traducirse en:

- bloquear despliegue,
- pedir aprobación manual,
- crear un ticket,
- publicar un comentario en la pull request,
- o enviar el resultado a un sistema de auditoría.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate deployment gate")
    parser.add_argument("--audit-report", default="reports/audit-report.json", type=Path)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Devuelve código 1 si el despliegue automático no está permitido.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = json.loads(args.audit_report.read_text(encoding="utf-8"))
    decision = payload["decision"]

    print("Deployment gate")
    print(f"Deployment allowed: {decision['deployment_allowed']}")
    print(f"Manual review required: {decision['manual_review_required']}")
    print(f"Reason: {decision['reason']}")

    if args.strict and not decision["deployment_allowed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
