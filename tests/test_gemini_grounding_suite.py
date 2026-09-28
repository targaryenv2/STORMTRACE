#!/usr/bin/env python3
"""
STORMTRACE Live Gemini Grounding Verification Suite.
Tests the 4 specific meteorological and provenance questions against the live Gemini provider.
"""

import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.stormtrace.ai import get_ai_provider, GeminiProvider

def main():
    print("============================================================")
    print("STORMTRACE LIVE GEMINI GROUNDING VERIFICATION SUITE")
    print("============================================================")
    
    provider = get_ai_provider()
    print(f"Provider: {type(provider).__name__}")
    if hasattr(provider, 'model'):
        print(f"Model: {provider.model}")
        
    questions = [
        {
            "id": "Q1",
            "q": "Is the final East India model already trained?"
        },
        {
            "id": "Q2",
            "q": "Does STORMTRACE currently have live radar coverage?"
        },
        {
            "id": "Q3",
            "q": "What forecast horizons does STORMTRACE support?"
        },
        {
            "id": "Q4",
            "q": "What is the current status of the 2020+ East India training data?"
        }
    ]
    
    all_passed = True
    
    for item in questions:
        print(f"\n[{item['id']}] Question: {item['q']}")
        t0 = time.time()
        res = provider.generate_response(item['q'])
        dt = time.time() - t0
        
        reply = res.get('reply', '')
        provider_used = res.get('provider', 'unknown')
        status = res.get('status', 'unknown')
        
        print(f"Provider Used: {provider_used}")
        print(f"Response Status: {status} ({dt:.2f}s)")
        print(f"Response Content:\n{reply}\n")
        
        if status != "success" or not reply:
            all_passed = False
            print(f"FAILED: Empty or failed response for {item['id']}")
            
    print("============================================================")
    if all_passed:
        print("ALL GROUNDING QUESTIONS COMPLETED SUCCESSFULLY")
    else:
        print("SOME GROUNDING QUESTIONS FAILED")
    print("============================================================")

if __name__ == '__main__':
    main()
