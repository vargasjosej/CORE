#!/usr/bin/env python3
"""
Benchmark Edge Vision Models (<2GB) for URP Extraction

Tests ultra-lightweight vision models suitable for edge deployment:
- moondream:latest (1.7GB, 1B params)
- Future: llava variants, tiny models

Dataset: LISA traffic lights (real images)
Metrics: Latency, accuracy, memory footprint
"""
import json
import time
import base64
from pathlib import Path
from typing import Dict, List
import requests
from anthropic import Anthropic
import os

# LISA dataset path
LISA_PATH = Path.home() / "Proyectos" / "PRU" / "data" / "lisa"

def encode_image(image_path: str) -> str:
    """Encode image to base64 for API calls."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def extract_traffic_states_ollama(image_path: str, model: str) -> Dict:
    """
    Extract traffic light states using Ollama vision model.

    Args:
        image_path: Path to image
        model: Ollama model name (e.g., "moondream:latest")

    Returns:
        Dict with detected states
    """
    import ollama

    prompt = """Analyze this traffic light image. List ONLY the traffic lights visible.

For EACH traffic light, specify:
1. Color (red/yellow/green)
2. Position (left/center/right/top/bottom)

Format as JSON:
{
  "traffic_lights": [
    {"color": "red", "position": "top-left"},
    {"color": "green", "position": "center"}
  ]
}"""

    start = time.time()
    try:
        response = ollama.chat(
            model=model,
            messages=[{
                'role': 'user',
                'content': prompt,
                'images': [image_path]
            }]
        )
        latency = (time.time() - start) * 1000  # ms

        # Parse response
        content = response['message']['content']

        # Try to extract JSON
        if '```json' in content:
            json_str = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            json_str = content.split('```')[1].split('```')[0].strip()
        else:
            json_str = content.strip()

        try:
            data = json.loads(json_str)
            # Handle both array and object formats
            if isinstance(data, list):
                traffic_lights = data
            elif isinstance(data, dict):
                traffic_lights = data.get('traffic_lights', [])
            else:
                traffic_lights = []
        except json.JSONDecodeError:
            print(f"[WARN] JSON parse failed, raw: {content[:200]}")
            traffic_lights = []

        return {
            "model": model,
            "traffic_lights": traffic_lights,
            "count": len(traffic_lights),
            "latency_ms": latency,
            "raw_response": content[:500],
            "success": len(traffic_lights) > 0
        }

    except Exception as e:
        return {
            "model": model,
            "error": str(e),
            "latency_ms": (time.time() - start) * 1000,
            "success": False
        }

def extract_traffic_states_claude(image_path: str, client: Anthropic) -> Dict:
    """Extract using Claude 4.5 Sonnet (baseline)."""

    prompt = """Analyze this traffic light image. List ONLY the traffic lights visible.

For EACH traffic light, specify:
1. Color (red/yellow/green)
2. Position (left/center/right/top/bottom)

Format as JSON:
{
  "traffic_lights": [
    {"color": "red", "position": "top-left"},
    {"color": "green", "position": "center"}
  ]
}"""

    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()

    start = time.time()
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_data
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }]
        )
        latency = (time.time() - start) * 1000

        content = response.content[0].text

        # Parse JSON
        if '```json' in content:
            json_str = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            json_str = content.split('```')[1].split('```')[0].strip()
        else:
            json_str = content.strip()

        data = json.loads(json_str)
        traffic_lights = data.get('traffic_lights', [])

        return {
            "model": "claude-sonnet-4",
            "traffic_lights": traffic_lights,
            "count": len(traffic_lights),
            "latency_ms": latency,
            "success": True
        }

    except Exception as e:
        return {
            "model": "claude-sonnet-4",
            "error": str(e),
            "latency_ms": (time.time() - start) * 1000,
            "success": False
        }

def run_benchmark(sample_size: int = 10):
    """
    Benchmark edge vision models vs Claude baseline.

    Args:
        sample_size: Number of LISA images to test
    """
    print("="*70)
    print("EDGE VISION MODELS BENCHMARK (<2GB)")
    print("="*70)
    print(f"Dataset: LISA Traffic Lights")
    print(f"Sample size: {sample_size} images")
    print(f"Models: moondream (1.7GB) vs Claude Sonnet 4 (baseline)")
    print("="*70)

    # Check LISA dataset
    if not LISA_PATH.exists():
        print(f"❌ LISA dataset not found at {LISA_PATH}")
        print("Run: python benchmark_industrial_kr.py --dataset lisa --download")
        return

    # Find test images (LISA has daySequence1/daySequence1/frames/*.jpg structure)
    image_dirs = [
        LISA_PATH / "daySequence1" / "daySequence1" / "frames",
        LISA_PATH / "daySequence2" / "daySequence2" / "frames",
        LISA_PATH / "nightSequence1" / "nightSequence1" / "frames"
    ]

    images = []
    for img_dir in image_dirs:
        if img_dir.exists():
            images.extend(sorted(img_dir.glob("*.jpg"))[:sample_size])
            if len(images) >= sample_size:
                break

    images = images[:sample_size]

    if not images:
        print(f"❌ No images found in LISA dataset")
        print(f"Tried: {[str(d) for d in image_dirs]}")
        return

    print(f"✓ Found {len(images)} images")
    print()

    # Initialize Claude client
    claude_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Results storage
    results = {
        "moondream": [],
        "claude": []
    }

    # Run benchmark
    for i, img in enumerate(images, 1):
        print(f"\n[{i}/{len(images)}] Processing: {img.name}")
        print("-" * 70)

        # Test 1: moondream
        print("  Testing moondream (1.7GB)...", end=" ", flush=True)
        moon_result = extract_traffic_states_ollama(str(img), "moondream:latest")
        results["moondream"].append(moon_result)

        if moon_result["success"]:
            print(f"✓ {moon_result['count']} lights, {moon_result['latency_ms']:.0f}ms")
        else:
            print(f"✗ Failed: {moon_result.get('error', 'No lights detected')}")

        # Test 2: Claude baseline
        print("  Testing Claude Sonnet 4...", end=" ", flush=True)
        claude_result = extract_traffic_states_claude(str(img), claude_client)
        results["claude"].append(claude_result)

        if claude_result["success"]:
            print(f"✓ {claude_result['count']} lights, {claude_result['latency_ms']:.0f}ms")
        else:
            print(f"✗ Failed")

        # Quick comparison
        if moon_result["success"] and claude_result["success"]:
            agreement = "✓" if moon_result["count"] == claude_result["count"] else "✗"
            print(f"  Agreement: {agreement} (moon: {moon_result['count']}, claude: {claude_result['count']})")

    # Calculate statistics
    print("\n" + "="*70)
    print("RESULTS SUMMARY")
    print("="*70)

    for model_name in ["moondream", "claude"]:
        model_results = results[model_name]
        successful = [r for r in model_results if r["success"]]

        if successful:
            avg_latency = sum(r["latency_ms"] for r in successful) / len(successful)
            avg_count = sum(r["count"] for r in successful) / len(successful)
            success_rate = len(successful) / len(model_results) * 100

            print(f"\n{model_name.upper()}:")
            print(f"  Success rate: {success_rate:.1f}% ({len(successful)}/{len(model_results)})")
            print(f"  Avg latency: {avg_latency:.0f}ms")
            print(f"  Avg lights detected: {avg_count:.1f}")
        else:
            print(f"\n{model_name.upper()}: ❌ All failed")

    # Speedup analysis
    moon_successful = [r for r in results["moondream"] if r["success"]]
    claude_successful = [r for r in results["claude"] if r["success"]]

    if moon_successful and claude_successful:
        moon_avg = sum(r["latency_ms"] for r in moon_successful) / len(moon_successful)
        claude_avg = sum(r["latency_ms"] for r in claude_successful) / len(claude_successful)
        speedup = claude_avg / moon_avg

        print("\n" + "-"*70)
        print(f"SPEEDUP: moondream is {speedup:.2f}x {'faster' if speedup > 1 else 'slower'} than Claude")
        print("-"*70)

    # Save detailed results
    output_file = "edge_vision_benchmark_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Detailed results saved to: {output_file}")

    # Edge deployment verdict
    print("\n" + "="*70)
    print("EDGE DEPLOYMENT VERDICT")
    print("="*70)

    if moon_successful:
        moon_avg_latency = sum(r["latency_ms"] for r in moon_successful) / len(moon_successful)

        if moon_avg_latency < 500:
            verdict = "✅ EXCELLENT for edge (real-time capable)"
        elif moon_avg_latency < 2000:
            verdict = "✅ GOOD for edge (near real-time)"
        elif moon_avg_latency < 5000:
            verdict = "⚠️ MARGINAL for edge (batch processing only)"
        else:
            verdict = "❌ TOO SLOW for edge"

        print(f"\nmoondream (1.7GB): {verdict}")
        print(f"  Latency: {moon_avg_latency:.0f}ms/image")
        print(f"  Model size: 1.7GB (fits Raspberry Pi 4, Jetson Nano)")
        print(f"  Deployment: ONNX, TensorRT, or Ollama")

    print("\n" + "="*70)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Benchmark edge vision models")
    parser.add_argument("--sample-size", type=int, default=10,
                       help="Number of images to test (default: 10)")

    args = parser.parse_args()

    # Check dependencies
    try:
        import ollama
    except ImportError:
        print("❌ ollama-python not installed")
        print("Install: pip install ollama")
        exit(1)

    run_benchmark(args.sample_size)
