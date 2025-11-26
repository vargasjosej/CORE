#!/usr/bin/env python3
"""
Test API connection to local server.
Verifies that Claude Sonnet 4 is accessible via local proxy.
"""
import os
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    """Test connection to local API server."""

    print("="*60)
    print("Testing API Connection to Local Server")
    print("="*60)

    # Get configuration
    api_key = os.getenv("ANTHROPIC_API_KEY")
    base_url = os.getenv("ANTHROPIC_BASE_URL")
    model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")

    print(f"\nConfiguration:")
    print(f"  API Key: {api_key[:10]}..." if api_key else "  API Key: NOT SET")
    print(f"  Base URL: {base_url}")
    print(f"  Model: {model}")

    # Initialize client
    try:
        if base_url:
            client = Anthropic(api_key=api_key, base_url=base_url)
        else:
            client = Anthropic(api_key=api_key)

        print("\n✅ Client initialized successfully")
    except Exception as e:
        print(f"\n❌ Failed to initialize client: {e}")
        return False

    # Test simple query
    print("\nTesting simple query...")
    try:
        response = client.messages.create(
            model=model,
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": "Say 'API connection successful' and nothing else."
            }]
        )

        print(f"\n✅ Query successful!")
        print(f"Response: {response.content[0].text}")
        print(f"Model used: {response.model}")
        print(f"Tokens: {response.usage.input_tokens} input, {response.usage.output_tokens} output")

        return True

    except Exception as e:
        print(f"\n❌ Query failed: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()

    print("\n" + "="*60)
    if success:
        print("✅ All tests passed! System ready for PRU extraction.")
    else:
        print("❌ Tests failed. Check configuration.")
    print("="*60)
