import unittest
from pathlib import Path

from scripts.ai_review import (
    AiInvalidResponseError,
    MockAiReviewClient,
    OllamaAiReviewClient,
)


class MockAiReviewClientTest(unittest.TestCase):
    def test_mock_ai_ok_returns_structured_result(self):
        result = MockAiReviewClient("ai-ok").review(["src/demo_app/calculator.py"])

        self.assertTrue(result.available)
        self.assertEqual(result.provider, "mock-provider")
        self.assertIn(result.risk, {"low", "medium", "high"})
        self.assertGreaterEqual(result.confidence, 0)
        self.assertLessEqual(result.confidence, 1)
        self.assertGreater(len(result.recommendations), 0)


class OllamaAiReviewClientParsingTest(unittest.TestCase):
    def test_ollama_result_contract_is_mapped(self):
        client = OllamaAiReviewClient(root=Path.cwd())
        result = client._to_review_result(
            {
                "confidence": 0.8,
                "risk": "medium",
                "blocking": False,
                "summary": "Cambio sin bloqueo evidente.",
                "recommendations": ["Conservar trazabilidad."],
            }
        )

        self.assertTrue(result.available)
        self.assertEqual(result.provider, "ollama")
        self.assertEqual(result.model, "qwen2.5:1.5b")
        self.assertEqual(result.risk, "medium")
        self.assertFalse(result.blocking)

    def test_ollama_invalid_risk_is_rejected(self):
        client = OllamaAiReviewClient(root=Path.cwd())

        with self.assertRaises(AiInvalidResponseError):
            client._to_review_result(
                {
                    "confidence": 0.8,
                    "risk": "critical",
                    "blocking": True,
                    "summary": "Riesgo no válido.",
                    "recommendations": ["Revisar."],
                }
            )


if __name__ == "__main__":
    unittest.main()
