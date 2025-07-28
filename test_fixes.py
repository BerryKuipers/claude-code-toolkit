#!/usr/bin/env python3
"""Quick test to verify our fixes work."""

import os
os.environ["BITVAVO_API_KEY"] = "test_key_12345"
os.environ["BITVAVO_API_SECRET"] = "test_secret_12345"

from backend.app.main import app
from fastapi.testclient import TestClient

def test_fixes():
    print("🧪 Testing code quality fixes...")
    client = TestClient(app)
    
    # Test basic endpoints
    print("✅ Testing root endpoint...")
    response = client.get("/")
    print(f"Root: {response.status_code}")
    
    print("✅ Testing health endpoint...")
    response = client.get("/health")
    print(f"Health: {response.status_code}")
    
    # Test portfolio endpoint that was failing
    print("✅ Testing portfolio holdings endpoint...")
    response = client.get("/api/v1/portfolio/holdings")
    print(f"Holdings: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
    else:
        print("✅ Portfolio holdings endpoint working!")
    
    print("✅ Code quality fixes test completed!")

if __name__ == "__main__":
    test_fixes()
