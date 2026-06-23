from __future__ import annotations

import unittest

from src.demo_app.calculator import add, calculate_discount, divide


class CalculatorTests(unittest.TestCase):
    def test_add(self) -> None:
        self.assertEqual(add(2, 3), 5)

    def test_divide(self) -> None:
        self.assertEqual(divide(10, 2), 5)

    def test_divide_by_zero_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            divide(10, 0)

    def test_discount(self) -> None:
        self.assertEqual(calculate_discount(100, 15), 85.0)

    def test_invalid_discount_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            calculate_discount(100, 150)


if __name__ == "__main__":
    unittest.main()
