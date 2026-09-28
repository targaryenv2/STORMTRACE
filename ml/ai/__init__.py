"""ML AI Module forwarding to stormtrace.ai."""

try:
    from backend.stormtrace.ai import (
        AIProvider, LocalFallbackProvider, GeminiProvider, get_ai_provider, STORMTRACE_SYSTEM_PROMPT
    )
except ImportError:
    from stormtrace.ai import (
        AIProvider, LocalFallbackProvider, GeminiProvider, get_ai_provider, STORMTRACE_SYSTEM_PROMPT
    )

__all__ = [
    "AIProvider",
    "LocalFallbackProvider",
    "GeminiProvider",
    "get_ai_provider",
    "STORMTRACE_SYSTEM_PROMPT"
]
