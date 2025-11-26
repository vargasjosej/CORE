#!/usr/bin/env python3
"""
Test improved prompts for moondream to reduce over-detection.

Current issue: Moondream detects 5 lights consistently vs Claude's 0-1
Goal: Make moondream more conservative/accurate
"""
import ollama
from pathlib import Path
import time

# Test image
LISA_PATH = Path.home() / "Proyectos" / "PRU" / "data" / "lisa"
test_image = LISA_PATH / "daySequence1" / "daySequence1" / "frames" / "daySequence1--00001.jpg"

# Prompts to test
prompts = {
    "original": """Analyze this traffic light image. List ONLY the traffic lights visible.

For EACH traffic light, specify:
1. Color (red/yellow/green)
2. Position (left/center/right/top/bottom)

Format as JSON:
{
  "traffic_lights": [
    {"color": "red", "position": "top-left"},
    {"color": "green", "position": "center"}
  ]
}""",

    "conservative": """You are analyzing a REAL traffic light camera image.

STRICT RULES:
- Only list traffic lights that are CLEARLY VISIBLE and IN FOCUS
- Ignore reflections, blurred lights, or distant signals
- If unsure, DO NOT include it
- Most images have 0-2 traffic lights, NOT 5+

List each traffic light as JSON array:
[
  {"color": "red", "position": "top-left"},
  {"color": "green", "position": "center"}
]

If NO clear traffic lights are visible, return: []""",

    "minimal": """List ONLY clearly visible traffic lights in this image.
Be conservative - when in doubt, omit.

JSON format: [{"color": "red", "position": "top"}]
If none: []""",

    "count_first": """Step 1: Count how many traffic lights you see CLEARLY (not reflections).
Step 2: For each one, specify color and position.

Return JSON array. Most images have 0-2 lights.
Example: [{"color": "red", "position": "center"}]"""
}

print("="*70)
print("MOONDREAM PROMPT OPTIMIZATION TEST")
print("="*70)
print(f"Test image: {test_image.name}")
print()

results = {}

for prompt_name, prompt_text in prompts.items():
    print(f"\n{'='*70}")
    print(f"Testing: {prompt_name.upper()}")
    print(f"{'='*70}")
    print(f"Prompt: {prompt_text[:100]}...")

    start = time.time()
    try:
        response = ollama.chat(
            model="moondream:latest",
            messages=[{
                'role': 'user',
                'content': prompt_text,
                'images': [str(test_image)]
            }]
        )
        latency = (time.time() - start) * 1000
        content = response['message']['content']

        print(f"\nLatency: {latency:.0f}ms")
        print(f"Response:\n{content}")

        # Try to count lights
        import json
        try:
            if '[' in content:
                json_str = content[content.index('['):content.rindex(']')+1]
                lights = json.loads(json_str)
                count = len(lights) if isinstance(lights, list) else 0
            else:
                count = "parse_failed"
        except:
            count = "parse_failed"

        print(f"\n→ Detected: {count} lights")

        results[prompt_name] = {
            "latency_ms": latency,
            "count": count,
            "response": content
        }

    except Exception as e:
        print(f"❌ Error: {e}")
        results[prompt_name] = {"error": str(e)}

# Summary
print("\n" + "="*70)
print("SUMMARY")
print("="*70)

for prompt_name, result in results.items():
    if "error" not in result:
        print(f"{prompt_name:15s}: {result['count']} lights, {result['latency_ms']:.0f}ms")
    else:
        print(f"{prompt_name:15s}: ERROR")

print("\n" + "="*70)
print("RECOMMENDATION")
print("="*70)

# Find best (closest to 0-2 lights)
best = None
best_score = float('inf')

for prompt_name, result in results.items():
    if "error" not in result and isinstance(result['count'], int):
        # Score: distance from expected range (0-2)
        if result['count'] <= 2:
            score = 0  # Perfect
        else:
            score = result['count'] - 2  # Penalty for over-detection

        if score < best_score:
            best_score = score
            best = prompt_name

if best:
    print(f"✅ BEST PROMPT: {best}")
    print(f"   Detected: {results[best]['count']} lights")
    print(f"   Latency: {results[best]['latency_ms']:.0f}ms")
else:
    print("❌ All prompts failed")

print("="*70)
