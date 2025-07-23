#!/usr/bin/env python3
"""Verify dashboard data against actual Bitvavo account balances."""

import os
import sys
from decimal import Decimal
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

if not api_key or not api_secret:
    print("❌ Missing API credentials")
    sys.exit(1)

try:
    print("🔍 Checking your ACTUAL Bitvavo account balances...\n")

    client = Bitvavo({"APIKEY": api_key, "APISECRET": api_secret})

    # Get actual account balances
    balances = client.balance({})

    print("📊 ACTUAL ACCOUNT BALANCES:")
    print("=" * 50)

    significant_balances = []
    for balance in balances:
        symbol = balance["symbol"]
        available = float(balance["available"])
        in_order = float(balance["inOrder"])
        total = available + in_order

        if total > 0.001:  # Only show significant balances
            significant_balances.append(
                {
                    "symbol": symbol,
                    "available": available,
                    "in_order": in_order,
                    "total": total,
                }
            )

    # Sort by total balance descending
    significant_balances.sort(key=lambda x: x["total"], reverse=True)

    for balance in significant_balances:
        print(
            f"{balance['symbol']:>8}: {balance['total']:>15.8f} (Available: {balance['available']:>12.8f}, In Orders: {balance['in_order']:>12.8f})"
        )

    print("\n" + "=" * 50)
    print(f"Total assets with balance > 0.001: {len(significant_balances)}")

    # Check specific assets mentioned
    print("\n🔍 SPECIFIC ASSET CHECKS:")
    print("-" * 30)

    btc_balance = next((b for b in balances if b["symbol"] == "BTC"), None)
    if btc_balance:
        btc_total = float(btc_balance["available"]) + float(btc_balance["inOrder"])
        print(f"BTC: {btc_total:.8f} (Dashboard shows: 0.00000000)")
        if btc_total > 0:
            print("⚠️  MISMATCH: You have BTC in your account but dashboard shows 0!")
        else:
            print("✅ MATCH: No BTC in account, dashboard correctly shows 0")

    sol_balance = next((b for b in balances if b["symbol"] == "SOL"), None)
    if sol_balance:
        sol_total = float(sol_balance["available"]) + float(sol_balance["inOrder"])
        print(f"SOL: {sol_total:.8f} (Dashboard shows: 14.84076157)")
        if abs(sol_total - 14.84076157) > 0.001:
            print("⚠️  POTENTIAL MISMATCH: SOL amounts differ!")
        else:
            print("✅ MATCH: SOL amounts are very close")

    print("\n💡 EXPLANATION:")
    print("- Dashboard shows FIFO accounting based on trade history")
    print("- Account shows current balances")
    print(
        "- Differences can occur if you have deposits/withdrawals not captured in trade history"
    )

except Exception as exc:
    print(f"❌ Error: {exc}")
    import traceback

    traceback.print_exc()
