#!/usr/bin/env python3
"""Test script to check environment variable loading."""

import os


# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file."""
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    print(f"Looking for .env file at: {env_file}")

    if os.path.exists(env_file):
        print("✅ .env file found!")
        with open(env_file, "r") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    os.environ[key] = value
                    print(f"Line {line_num}: Set {key} = {value[:10]}...")
    else:
        print("❌ .env file not found!")


# Load environment variables
load_env_file()

# Check if the API keys are loaded
api_key = os.getenv("BITVAVO_API_KEY")
api_secret = os.getenv("BITVAVO_API_SECRET")

print(f"\nBITVAVO_API_KEY: {'✅ Found' if api_key else '❌ Not found'}")
print(f"BITVAVO_API_SECRET: {'✅ Found' if api_secret else '❌ Not found'}")

if api_key:
    print(f"API Key starts with: {api_key[:10]}...")
if api_secret:
    print(f"API Secret starts with: {api_secret[:10]}...")
