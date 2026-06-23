"""Pequeña aplicación de ejemplo para tener algo que probar en CI.

La lógica de negocio es deliberadamente simple: el repositorio no pretende
mostrar una aplicación compleja, sino una forma de integrar IA en un pipeline
sin convertirla en un punto único de fallo.
"""

from __future__ import annotations


def add(a: int, b: int) -> int:
    """Suma dos enteros."""
    return a + b


def divide(a: float, b: float) -> float:
    """Divide dos números.

    Raises:
        ValueError: si el divisor es cero.
    """
    if b == 0:
        raise ValueError("division by zero is not allowed")
    return a / b


def calculate_discount(price: float, percentage: float) -> float:
    """Calcula el precio final tras aplicar un descuento porcentual."""
    if price < 0:
        raise ValueError("price cannot be negative")
    if percentage < 0 or percentage > 100:
        raise ValueError("percentage must be between 0 and 100")
    return round(price * (1 - percentage / 100), 2)
