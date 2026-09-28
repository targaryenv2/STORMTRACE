"""STORMTRACE AI Assistant Module."""

from .provider import AIProvider, LocalFallbackProvider, get_ai_provider
from .gemini_provider import GeminiProvider
from .system_prompt import STORMTRACE_SYSTEM_PROMPT
from .scope_guard import classify_project_scope, SCOPE_REFUSAL_MESSAGE

__all__ = [
    "AIProvider",
    "LocalFallbackProvider",
    "GeminiProvider",
    "get_ai_provider",
    "STORMTRACE_SYSTEM_PROMPT",
    "classify_project_scope",
    "SCOPE_REFUSAL_MESSAGE"
]
