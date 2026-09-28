"""Google Gemini AI Provider implementation for STORMTRACE Assistant."""

import json
import re
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from .provider import AIProvider, LocalFallbackProvider
from .system_prompt import STORMTRACE_SYSTEM_PROMPT
from .scope_guard import classify_project_scope, SCOPE_REFUSAL_MESSAGE, get_scope_refusal


class GeminiProvider(AIProvider):
    """Integrates Google Gemini (default: gemini-3.5-flash) with project scope guard and safety rules."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3.5-flash",
        timeout_seconds: int = 30
    ):
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.fallback = LocalFallbackProvider()
        self.endpoint_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

    def _extract_actions_and_clean_text(self, raw_text: str) -> tuple[str, List[Dict[str, Any]]]:
        """Extracts JSON action directives from model response and returns clean text."""
        actions = []
        action_match = re.search(r"<!--ACTIONS:\s*(\[.*?\])\s*-->", raw_text, re.DOTALL)
        if action_match:
            try:
                actions = json.loads(action_match.group(1))
            except Exception:
                actions = []
            clean_text = raw_text[:action_match.start()].strip() + " " + raw_text[action_match.end():].strip()
            clean_text = clean_text.strip()
        else:
            clean_text = raw_text.strip()

        # Append standard disclaimer if not already present and not a scope refusal
        disclaimer = "This is AI decision-support, not an official IMD warning."
        if "i'm the stormtrace ai assistant" not in clean_text.lower() and disclaimer.lower() not in clean_text.lower():
            clean_text = f"{clean_text}\n\n{disclaimer}"

        return clean_text, actions

    def generate_response(
        self,
        message: str,
        history: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Sends request to Gemini API and formats response, guarded by project scope."""
        lang = "en"
        if context and isinstance(context, dict):
            lang = context.get("language") or "en"

        # 1. Deterministic Scope Guard Check
        category, is_project_related = classify_project_scope(message)
        if not is_project_related:
            return {
                "status": "success",
                "reply": get_scope_refusal(lang),
                "provider": "scope_guard",
                "model": "scope_guard_v1",
                "actions": [],
                "card": None
            }

        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return self.fallback.generate_response(message, history, context)

        # Build contents array
        contents = []
        if history:
            for item in history:
                role = "user" if item.get("sender") == "user" else "model"
                text = item.get("text", "")
                if text:
                    contents.append({
                        "role": role,
                        "parts": [{"text": text}]
                    })

        # Append current user message with context if available
        user_content = message
        if context and context.get("selected_cell"):
            cell = context["selected_cell"]
            user_content += (
                f"\n\n[Active App Context: Selected Cell {cell.get('cell_id')} in {cell.get('region')}, "
                f"Max dBZ: {cell.get('max_dbz')}, Severity: {cell.get('severity_score')}/100, "
                f"Heading: {cell.get('compass')}, Speed: {cell.get('speed_kmh')} km/h]"
            )

        contents.append({
            "role": "user",
            "parts": [{"text": user_content}]
        })

        payload = {
            "system_instruction": {
                "parts": [{"text": STORMTRACE_SYSTEM_PROMPT}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.95,
                "maxOutputTokens": 2048,
                "thinkingConfig": {
                    "thinkingBudget": 0
                }
            }
        }

        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.endpoint_url,
            data=req_data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                resp_json = json.loads(resp.read().decode("utf-8"))
                candidates = resp_json.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    raw_text = "".join(p.get("text", "") for p in parts)
                    clean_text, actions = self._extract_actions_and_clean_text(raw_text)
                    return {
                        "status": "success",
                        "reply": clean_text,
                        "provider": "gemini",
                        "model": self.model,
                        "actions": actions,
                        "card": None
                    }
                else:
                    return self.fallback.generate_response(message, history, context)

        except urllib.error.HTTPError as e:
            err_body = ""
            try:
                err_body = e.read().decode("utf-8")
            except Exception:
                pass
            sanitized_code = e.code
            print(f"[GEMINI_PROVIDER] HTTP Error {sanitized_code}: {err_body[:200]}")
            fallback_res = self.fallback.generate_response(message, history, context)
            fallback_res["note"] = f"Gemini API returned status {sanitized_code}; responded via grounded local fallback."
            return fallback_res

        except Exception as e:
            print(f"[GEMINI_PROVIDER] Connection error: {type(e).__name__}")
            fallback_res = self.fallback.generate_response(message, history, context)
            fallback_res["note"] = f"Gemini connection timeout/offline; responded via grounded local fallback."
            return fallback_res
