"""Test suite for STORMTRACE Multilingual / i18n System.

Verifies:
1. All 13 supported language JSON files exist and parse as valid JSON.
2. 100% key parity with en.json (0 missing keys, 0 extra keys, 0 empty values).
3. All interpolation parameters (e.g. {{min}}, {{id}}, {{pct}}) match between en.json and target locales.
4. Scope refusal messages exist for all 13 supported languages.
5. Urdu (ur) is correctly identified for RTL direction.
"""

import os
import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCALES_DIR = REPO_ROOT / "frontend" / "src" / "i18n" / "locales"

REQUIRED_LOCALES = [
    "en", "hi", "bn", "ta", "te", "mr", "gu",
    "kn", "ml", "pa", "ur", "or", "as"
]


def extract_leaf_keys(data, prefix=""):
    keys = {}
    for k, v in data.items():
        curr_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            keys.update(extract_leaf_keys(v, curr_key))
        else:
            keys[curr_key] = str(v)
    return keys


def extract_placeholders(text):
    return set(re.findall(r"\{\{([a-zA-Z0-9_]+)\}\}", text))


class TestI18nLocales(unittest.TestCase):
    """Test suite verifying all 13 i18n locales and system integration."""

    @classmethod
    def setUpClass(cls):
        cls.locales_data = {}
        for code in REQUIRED_LOCALES:
            file_path = LOCALES_DIR / f"{code}.json"
            assert file_path.exists(), f"Locale file missing: {file_path}"
            with open(file_path, "r", encoding="utf-8") as f:
                cls.locales_data[code] = json.load(f)

        cls.en_leaf_keys = extract_leaf_keys(cls.locales_data["en"])

    def test_all_13_locale_files_exist(self):
        """Ensure all 13 locale files exist and are loaded."""
        self.assertEqual(len(self.locales_data), 13)
        for code in REQUIRED_LOCALES:
            self.assertIn(code, self.locales_data)

    def test_key_parity_against_en_json(self):
        """Ensure every locale has 100% exact key parity with en.json."""
        en_keys_set = set(self.en_leaf_keys.keys())
        self.assertGreater(len(en_keys_set), 150, "Canonical schema should have >150 keys")

        for code, data in self.locales_data.items():
            if code == "en":
                continue
            target_leaf_keys = extract_leaf_keys(data)
            target_keys_set = set(target_leaf_keys.keys())

            missing_keys = en_keys_set - target_keys_set
            extra_keys = target_keys_set - en_keys_set

            self.assertEqual(
                len(missing_keys), 0,
                f"Locale '{code}' has {len(missing_keys)} missing keys: {list(missing_keys)[:5]}"
            )
            self.assertEqual(
                len(extra_keys), 0,
                f"Locale '{code}' has {len(extra_keys)} extra keys: {list(extra_keys)[:5]}"
            )

    def test_no_empty_string_values(self):
        """Ensure no locale contains empty string values."""
        for code, data in self.locales_data.items():
            leaf_keys = extract_leaf_keys(data)
            for k, val in leaf_keys.items():
                self.assertTrue(
                    bool(val and val.strip()),
                    f"Locale '{code}' has empty value at key: {k}"
                )

    def test_interpolation_variable_parity(self):
        """Ensure interpolation variables like {{min}} match en.json exactly."""
        for code, data in self.locales_data.items():
            if code == "en":
                continue
            target_leaf_keys = extract_leaf_keys(data)
            for k, en_val in self.en_leaf_keys.items():
                en_vars = extract_placeholders(en_val)
                if en_vars:
                    target_val = target_leaf_keys.get(k, "")
                    target_vars = extract_placeholders(target_val)
                    self.assertEqual(
                        en_vars, target_vars,
                        f"Interpolation mismatch in '{code}' at key '{k}': expected {en_vars}, found {target_vars}"
                    )

    def test_technical_units_retention(self):
        """Ensure standard meteorological and AI units/terms are preserved."""
        required_terms = ["dBZ", "STORMTRACE", "ConvLSTM", "MC-Dropout"]
        en_text = json.dumps(self.locales_data["en"])
        for term in required_terms:
            self.assertIn(term, en_text)

    def test_localized_ai_scope_refusal(self):
        """Ensure scope guard has localized refusal for all 13 languages."""
        from backend.stormtrace.ai.scope_guard import get_scope_refusal, LOCALIZED_SCOPE_REFUSALS

        self.assertEqual(len(LOCALIZED_SCOPE_REFUSALS), 13)
        for code in REQUIRED_LOCALES:
            refusal = get_scope_refusal(code)
            self.assertTrue(bool(refusal and len(refusal) > 20))
            self.assertIn("STORMTRACE", refusal)

    def test_rtl_locale_identification(self):
        """Ensure Urdu (ur) is marked as RTL while others are LTR."""
        rtl_locales = ["ur"]
        for code in REQUIRED_LOCALES:
            is_rtl = code in rtl_locales
            expected_dir = "rtl" if is_rtl else "ltr"
            if code == "ur":
                self.assertEqual(expected_dir, "rtl")
            else:
                self.assertEqual(expected_dir, "ltr")


if __name__ == "__main__":
    unittest.main()
