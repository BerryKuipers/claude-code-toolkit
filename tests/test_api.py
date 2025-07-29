#!/usr/bin/env python3
"""Test script to debug Bitvavo API connection."""

import os
import sys

from python_bitvavo_api.bitvavo import Bitvavo


# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file."""
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()


# Load environment variables
load_env_file()

# Get API credentials
api_key = os.getenv("BITVAVO_API_KEY")
api_secret = os.getenv("BITVAVO_API_SECRET")

print(f"API Key: {'Found' if api_key else 'Not found'}")
print(f"API Secret: {'Found' if api_secret else 'Not found'}")

if not api_key or not api_secret:
    print("❌ Missing API credentials")
    sys.exit(1)

try:
    print("\n🔄 Creating Bitvavo client...")
    client = Bitvavo({"APIKEY": api_key, "APISECRET": api_secret})
    print("✅ Client created successfully")

    print("\n🔄 Testing time endpoint...")
    time_response = client.time()
    print(f"Time response type: {type(time_response)}")
    print(f"Time response: {time_response}")

    if isinstance(time_response, dict) and "time" in time_response:
        print(f"✅ Time found in dict: {time_response['time']}")
    elif isinstance(time_response, list) and len(time_response) > 0:
        print(f"✅ Time response is list with {len(time_response)} items")
        if "time" in time_response[0]:
            print(f"✅ Time found in first item: {time_response[0]['time']}")
    else:
        print("❌ Unexpected time response format")

    print("\n🔄 Testing balance endpoint...")
    balance_response = client.balance({})
    print(f"Balance response type: {type(balance_response)}")
    print(
        f"Balance response length: {len(balance_response) if balance_response else 0}"
    )

    if balance_response:
        print("First few balance entries:")
        for i, balance in enumerate(balance_response[:3]):
            print(f"  {i+1}: {balance}")

    print("\n🔄 Testing ticker endpoint for BTC-EUR...")
    ticker_response = client.tickerPrice({"market": "BTC-EUR"})
    print(f"Ticker response type: {type(ticker_response)}")
    print(f"Ticker response: {ticker_response}")

    print("\n✅ All API tests completed successfully!")

except Exception as exc:
    print(f"❌ Error: {exc}")
    import traceback

    traceback.print_exc()
