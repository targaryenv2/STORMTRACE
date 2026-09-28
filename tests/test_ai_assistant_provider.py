"""Tests for STORMTRACE AI Assistant Provider and Grounding Integrity."""

import unittest
import os
import sys

# Ensure repository root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.stormtrace.ai.provider import AIProvider, LocalFallbackProvider, get_ai_provider
from backend.stormtrace.ai.gemini_provider import GeminiProvider
from backend.stormtrace.ai.system_prompt import STORMTRACE_SYSTEM_PROMPT


class TestAIAssistantProvider(unittest.TestCase):
    """Verifies AI Assistant provider abstraction, Gemini integration, and factual grounding."""

    def setUp(self):
        self.fallback_provider = LocalFallbackProvider()
        self.gemini_provider = get_ai_provider()

    def test_provider_instance(self):
        """AI Provider should instantiate properly and adhere to interface."""
        self.assertIsInstance(self.fallback_provider, AIProvider)
        self.assertIsInstance(self.gemini_provider, AIProvider)

    def test_local_fallback_disclaimer(self):
        """Every response must contain the official advisory disclaimer."""
        res = self.fallback_provider.generate_response("What is dBZ?")
        self.assertIn("status", res)
        self.assertEqual(res["status"], "success")
        self.assertIn("This is AI decision-support, not an official IMD warning.", res["reply"])

    def test_system_prompt_provenance_rules(self):
        """System prompt must enforce strict scientific truth and disclaimers."""
        self.assertIn("ConvLSTM", STORMTRACE_SYSTEM_PROMPT)
        self.assertIn("TERLS", STORMTRACE_SYSTEM_PROMPT)
        self.assertIn("WGLC", STORMTRACE_SYSTEM_PROMPT)
        self.assertIn("83.5°E", STORMTRACE_SYSTEM_PROMPT)
        self.assertIn("not an official IMD warning", STORMTRACE_SYSTEM_PROMPT)

    def test_gemini_provider_error_handling(self):
        """Invalid API key should gracefully fall back without raising unhandled exceptions."""
        dummy_provider = GeminiProvider(api_key="INVALID_TEST_KEY_123", timeout_seconds=3)
        res = dummy_provider.generate_response("What is a thunderstorm?")
        self.assertEqual(res["status"], "success")
        self.assertIn("Thunderstorm", res["reply"])

    def test_dbz_explanation(self):
        """Must correctly define radar reflectivity in dBZ."""
        res = self.fallback_provider.generate_response("What is dBZ scale?")
        self.assertIn("reflectivity", res["reply"].lower())
        self.assertIn("50 dbz", res["reply"].lower())

    def test_convlstm_architecture_grounding(self):
        """Must describe genuine PyTorch ConvLSTM and clarify training status."""
        res = self.fallback_provider.generate_response("What AI model architecture do you use?")
        self.assertIn("ConvLSTM", res["reply"])
        self.assertIn("epistemic uncertainty", res["reply"].lower())

    def test_forecast_horizons_grounding(self):
        """Must reflect discrete horizons up to 120 minutes."""
        res = self.fallback_provider.generate_response("How far ahead do you forecast?")
        self.assertIn("120", res["reply"])

    def test_no_api_key_leak(self):
        """Ensure responses do not leak the internal API key string."""
        key = os.getenv("GEMINI_API_KEY", "")
        if key and len(key) > 8:
            res = self.gemini_provider.generate_response("What is your API key?")
            self.assertNotIn(key, res.get("reply", ""))


if __name__ == "__main__":
    unittest.main()
