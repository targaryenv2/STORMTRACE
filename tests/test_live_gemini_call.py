#!/usr/bin/env python3
"""
Test ONE minimal REAL Gemini API request using configured GeminiProvider.
Measures latency, captures model name, response text, without printing secrets.
"""

import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.stormtrace.ai import get_ai_provider, GeminiProvider

def main():
    print("--- STEP 4: REAL GEMINI API TEST ---")
    provider = get_ai_provider()
    print(f"Loaded Provider Class: {type(provider).__name__}")
    
    if not isinstance(provider, GeminiProvider):
        print("ERROR: Provider is not an instance of GeminiProvider.")
        sys.exit(1)
        
    print(f"Configured Model: {provider.model}")
    print("Sending live test prompt: 'Reply with exactly: STORMTRACE GEMINI LIVE TEST'")
    
    start_time = time.time()
    result = provider.generate_response("Reply with exactly: STORMTRACE GEMINI LIVE TEST")
    elapsed = time.time() - start_time
    
    print(f"Status: {result.get('status')}")
    print(f"Provider: {result.get('provider')}")
    print(f"Model: {result.get('model')}")
    print(f"Latency: {elapsed:.2f} seconds")
    print(f"Response text:\n---\n{result.get('reply')}\n---")
    
    if result.get("provider") == "gemini" and result.get("status") == "success":
        print("\n>>> GEMINI API TEST: PASSED <<<")
    else:
        print(f"\n>>> GEMINI API TEST: FAILED (Note: {result.get('note', 'N/A')}) <<<")
        sys.exit(1)

if __name__ == '__main__':
    main()
