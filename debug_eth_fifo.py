#!/usr/bin/env python3
"""
Debug script to analyze the ETH FIFO calculation and identify why there's a shortfall.

This script will:
1. Fetch all ETH trades and deposits
2. Simulate the FIFO calculation step by step
3. Identify exactly where the discrepancy occurs
"""

import os
import sys
from decimal import Decimal
from datetime import datetime
from collections import deque
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import the old portfolio system to get raw data
from src.portfolio.core import fetch_trade_history, fetch_deposit_history
from python_bitvavo_api.bitvavo import Bitvavo

def debug_eth_fifo():
    """Debug the ETH FIFO calculation to find the discrepancy."""
    
    # Initialize Bitvavo client
    api_key = os.getenv('BITVAVO_API_KEY')
    api_secret = os.getenv('BITVAVO_API_SECRET')
    
    if not api_key or not api_secret:
        print("ERROR: BITVAVO_API_KEY and BITVAVO_API_SECRET must be set")
        return
    
    client = Bitvavo({
        'APIKEY': api_key,
        'APISECRET': api_secret,
        'RESTURL': 'https://api.bitvavo.com/v2',
        'WSURL': 'wss://ws.bitvavo.com/v2/',
        'ACCESSWINDOW': 10000,
        'DEBUGGING': False
    })
    
    print("=== ETH FIFO Debug Analysis ===")
    print()
    
    # Fetch ETH trades and deposits
    print("1. Fetching ETH trades...")
    trades = fetch_trade_history(client, "ETH")
    print(f"   Found {len(trades)} ETH trades")
    
    print("2. Fetching ETH deposits...")
    deposits = fetch_deposit_history(client, "ETH")
    completed_deposits = [d for d in deposits if d.get('status') == 'completed']
    print(f"   Found {len(completed_deposits)} completed ETH deposits")
    
    # Create combined timeline
    print("\n3. Creating chronological timeline...")
    timeline = []
    
    # Add deposits as zero-cost purchases
    for deposit in completed_deposits:
        timeline.append({
            'type': 'deposit',
            'timestamp': int(deposit['timestamp']),
            'amount': Decimal(deposit['amount']),
            'datetime': datetime.fromtimestamp(int(deposit['timestamp'])/1000)
        })
    
    # Add trades
    for trade in trades:
        timeline.append({
            'type': 'trade',
            'timestamp': int(trade['timestamp']),
            'amount': Decimal(trade['amount']),
            'price': Decimal(trade['price']),
            'fee': Decimal(trade.get('fee', '0')),
            'side': trade['side'],
            'datetime': datetime.fromtimestamp(int(trade['timestamp'])/1000)
        })
    
    # Sort by timestamp
    timeline.sort(key=lambda x: x['timestamp'])
    
    print(f"   Total timeline events: {len(timeline)}")
    
    # Simulate FIFO calculation
    print("\n4. Simulating FIFO calculation...")
    lots = deque()
    
    problematic_timestamp = 1618344156556
    problematic_amount = Decimal('0.11074718')
    
    print(f"\nLooking for trade at {datetime.fromtimestamp(problematic_timestamp/1000)} selling {problematic_amount} ETH")
    print()
    
    for i, event in enumerate(timeline):
        print(f"Event {i+1}: {event['datetime']} - {event['type']}")
        
        if event['type'] == 'deposit':
            # Add deposit as zero-cost lot
            lots.append({
                'amount': event['amount'],
                'cost': Decimal('0'),
                'timestamp': event['timestamp']
            })
            print(f"  + Deposit: {event['amount']} ETH (zero cost)")
            
        elif event['type'] == 'trade':
            if event['side'] == 'buy':
                # Add purchase lot
                cost = event['amount'] * event['price'] + event['fee']
                lots.append({
                    'amount': event['amount'],
                    'cost': cost,
                    'timestamp': event['timestamp']
                })
                print(f"  + Buy: {event['amount']} ETH at {event['price']} EUR (cost: {cost} EUR)")
                
            elif event['side'] == 'sell':
                print(f"  - Sell: {event['amount']} ETH at {event['price']} EUR")
                
                # Check if this is the problematic trade
                if event['timestamp'] == problematic_timestamp:
                    print(f"    *** THIS IS THE PROBLEMATIC TRADE ***")
                    print(f"    Available lots before sell:")
                    total_available = Decimal('0')
                    for j, lot in enumerate(lots):
                        print(f"      Lot {j+1}: {lot['amount']} ETH (cost: {lot['cost']} EUR)")
                        total_available += lot['amount']
                    print(f"    Total available: {total_available} ETH")
                    print(f"    Trying to sell: {event['amount']} ETH")
                    print(f"    Shortfall: {event['amount'] - total_available} ETH")
                    print()
                
                # Process sell using FIFO
                remaining_to_sell = event['amount']
                while remaining_to_sell > 0 and lots:
                    lot = lots[0]
                    if lot['amount'] <= remaining_to_sell:
                        # Consume entire lot
                        remaining_to_sell -= lot['amount']
                        lots.popleft()
                        print(f"    Consumed lot: {lot['amount']} ETH")
                    else:
                        # Partial consumption
                        lot['amount'] -= remaining_to_sell
                        print(f"    Partial consumption: {remaining_to_sell} ETH from lot")
                        remaining_to_sell = Decimal('0')
                
                if remaining_to_sell > 0:
                    print(f"    *** OVERSELLING: {remaining_to_sell} ETH ***")
        
        # Show current holdings
        total_holdings = sum(lot['amount'] for lot in lots)
        print(f"  Current holdings: {total_holdings} ETH ({len(lots)} lots)")
        print()
        
        # Stop after the problematic trade for detailed analysis
        if event.get('timestamp') == problematic_timestamp:
            print("=== Analysis complete - found the problematic trade ===")
            break
    
    print("\n5. Summary:")
    print(f"   The ETH shortfall of 0.004895549999999964 ETH suggests:")
    print(f"   - Either missing deposit/transfer data")
    print(f"   - Or missing buy trades that should have occurred")
    print(f"   - Or precision/rounding issues in the API data")

if __name__ == "__main__":
    debug_eth_fifo()
