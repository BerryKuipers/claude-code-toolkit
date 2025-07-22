"""Core FIFO P&L calculation logic and Bitvavo API integration.

This module contains the essential business logic for cryptocurrency portfolio
analysis using FIFO accounting with high-precision Decimal arithmetic.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from decimal import Decimal, getcontext
from datetime import datetime, timezone
from typing import Deque, Dict, List, Optional, Tuple

try:
    from python_bitvavo_api.bitvavo import Bitvavo  # type: ignore
except ImportError:  # pragma: no cover
    Bitvavo = None  # keeps the type checker quiet when deps missing

# Set high precision for Decimal calculations
getcontext().prec = 28


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------

class BitvavoAPIException(Exception):
    """Base exception for Bitvavo API errors."""
    pass


class InvalidAPIKeyError(BitvavoAPIException):
    """Raised when API key is invalid or time sync issues occur."""
    pass


class RateLimitExceededError(BitvavoAPIException):
    """Raised when Bitvavo rate limit is exceeded."""
    pass


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class PurchaseLot:
    """Represents a purchase lot in FIFO accounting.

    Attributes:
        amount: Crypto units in this lot
        cost_eur: Total EUR cost including fees
        timestamp: Milliseconds since epoch (for completeness)
    """
    amount: Decimal      # crypto units
    cost_eur: Decimal    # total € incl. fees
    timestamp: int       # ms since epoch (for completeness)


@dataclass
class TransferSummary:
    """Summary of deposits and withdrawals for an asset.

    Attributes:
        total_deposits: Total amount deposited
        total_withdrawals: Total amount withdrawn
        net_transfers: Net transfer amount (deposits - withdrawals)
        deposit_count: Number of deposit transactions
        withdrawal_count: Number of withdrawal transactions
        potential_rewards: Estimated staking rewards/airdrops
    """
    total_deposits: Decimal
    total_withdrawals: Decimal
    net_transfers: Decimal
    deposit_count: int
    withdrawal_count: int
    potential_rewards: Decimal


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _decimal(value: str | float | int | Decimal) -> Decimal:
    """Coerce *value* into a Decimal without rounding."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _check_rate_limit(client: "Bitvavo", threshold: int = 10) -> None:
    """Sleep defensively when close to Bitvavo's weight budget."""
    remaining = int(client.getRemainingLimit())
    if remaining < threshold:
        time.sleep(15)  # simple, effective back‑off


# ---------------------------------------------------------------------------
# API wrappers
# ---------------------------------------------------------------------------

def sync_time(client: "Bitvavo") -> None:
    """Synchronise local clock offset to avoid 304 errors."""
    try:
        time_response = client.time()
        # Based on API test, time() returns a dict with 'time' key
        if isinstance(time_response, dict) and "time" in time_response:
            server_time_ms = int(time_response["time"])
        else:
            # Fallback: use local time (no offset)
            server_time_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
    except Exception as exc:  # pylint: disable=broad-except
        raise BitvavoAPIException(f"Failed to fetch /time: {exc}") from exc

    local_time_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
    client.timeDifference = server_time_ms - local_time_ms  # type: ignore[attr-defined]


def fetch_trade_history(client: "Bitvavo", asset: str) -> List[Dict[str, str]]:
    """Return **complete** trade list for ``asset-EUR`` (oldest‑first)."""
    market = f"{asset}-EUR"
    trades: List[Dict[str, str]] = []
    cursor: Optional[str] = None
    while True:
        _check_rate_limit(client)
        try:
            kwargs = {"limit": 1000}
            if cursor:
                kwargs["tradeIdTo"] = cursor
            batch = client.trades(market, kwargs)  # type: ignore[arg-type]
        except Exception as exc:  # pylint: disable=broad-except
            code = getattr(exc, "errorCode", None)
            if code == 304:
                raise InvalidAPIKeyError("API key / time sync issue.") from exc
            if code == 105:
                raise RateLimitExceededError("Hit Bitvavo rate limit.") from exc
            raise BitvavoAPIException(str(exc)) from exc
        if not batch:
            break
        trades.extend(batch)
        cursor = batch[-1]["id"]
    trades.reverse()  # oldest‑first for FIFO
    return trades


def calculate_pnl(trades: List[Dict[str, str]], current_price: Decimal) -> Dict[str, Decimal]:
    """Process *trades* (chronological list) under FIFO and return P&L metrics.
    
    Args:
        trades: List of trade dictionaries with keys: side, amount, price, fee, timestamp
        current_price: Current market price for unrealized P&L calculation
        
    Returns:
        Dictionary with keys:
        - amount: Remaining crypto amount
        - cost_eur: Remaining cost basis in EUR
        - value_eur: Current market value in EUR
        - realised_eur: Realized P&L in EUR
        - unrealised_eur: Unrealized P&L in EUR
        - total_buys_eur: Total amount invested (for return % calculation)
    """
    lots: Deque[PurchaseLot] = deque()
    realised_eur = Decimal("0")
    total_buys_eur = Decimal("0")  # denominator for true return %%
    
    for trade in trades:
        amt = _decimal(trade["amount"])
        price = _decimal(trade["price"])
        fee = _decimal(trade.get("fee", "0"))
        side = trade["side"].lower()
        ts = int(trade.get("timestamp", "0"))
        
        if side == "buy":
            cost = amt * price + fee
            total_buys_eur += cost
            lots.append(PurchaseLot(amount=amt, cost_eur=cost, timestamp=ts))
        elif side == "sell":
            proceeds = amt * price - fee
            sold_left = amt
            cost_basis = Decimal("0")
            
            while sold_left > 0 and lots:
                lot = lots[0]
                take = min(lot.amount, sold_left)
                proportional_cost = (lot.cost_eur / lot.amount) * take
                cost_basis += proportional_cost
                
                lot.amount -= take
                lot.cost_eur -= proportional_cost
                sold_left -= take
                
                if lot.amount == 0:
                    lots.popleft()
                else:
                    lots[0] = lot  # update in place
                    
            realised_eur += proceeds - cost_basis
        else:
            raise ValueError(f"Unknown trade side: {side}")
    
    remaining_amt = sum(lot.amount for lot in lots)
    remaining_cost = sum(lot.cost_eur for lot in lots)
    value_now = remaining_amt * current_price
    unrealised_eur = value_now - remaining_cost
    
    return {
        "amount": remaining_amt,
        "cost_eur": remaining_cost,
        "value_eur": value_now,
        "realised_eur": realised_eur,
        "unrealised_eur": unrealised_eur,
        "total_buys_eur": total_buys_eur,
    }


def get_current_price(client: "Bitvavo", asset: str) -> Decimal:
    """Get current market price for asset-EUR pair."""
    _check_rate_limit(client)
    try:
        ticker = client.tickerPrice({"market": f"{asset}-EUR"})  # type: ignore[arg-type]
        # Based on API test, tickerPrice returns a dict with 'price' key
        if isinstance(ticker, dict) and "price" in ticker:
            return _decimal(ticker["price"])
        else:
            # If no EUR pair or unexpected format, return 0 (asset will be skipped)
            return Decimal("0")
    except Exception:
        # If any error occurs, return 0 (asset will be skipped)
        return Decimal("0")


def get_portfolio_assets(client: "Bitvavo") -> List[str]:
    """Get list of assets with non-zero balances."""
    try:
        balances = client.balance({})  # type: ignore[arg-type]
        if not balances:
            return []

        assets = []
        for b in balances:
            try:
                if "symbol" in b and "available" in b and "inOrder" in b:
                    total_balance = _decimal(b["available"]) + _decimal(b["inOrder"])
                    if total_balance > 0:
                        # Extract base asset (e.g., "BTC-EUR" -> "BTC")
                        symbol = b["symbol"].split("-")[0].upper()
                        if symbol not in assets and symbol != "EUR":  # Skip EUR itself
                            assets.append(symbol)
            except Exception:
                continue  # Skip problematic balance entries

        return assets
    except Exception:
        return []  # Return empty list if balance fetch fails


def fetch_deposit_history(client: "Bitvavo", asset: str) -> List[Dict[str, str]]:
    """Fetch complete deposit history for an asset."""
    _check_rate_limit(client)
    try:
        deposits = client.depositHistory({"symbol": asset})  # type: ignore[arg-type]
        if not deposits:
            return []
        # Ensure we return a list of dictionaries
        if isinstance(deposits, list):
            return [d for d in deposits if isinstance(d, dict)]
        return []
    except Exception:
        return []


def fetch_withdrawal_history(client: "Bitvavo", asset: str) -> List[Dict[str, str]]:
    """Fetch complete withdrawal history for an asset."""
    _check_rate_limit(client)
    try:
        withdrawals = client.withdrawalHistory({"symbol": asset})  # type: ignore[arg-type]
        if not withdrawals:
            return []
        # Ensure we return a list of dictionaries
        if isinstance(withdrawals, list):
            return [w for w in withdrawals if isinstance(w, dict)]
        return []
    except Exception:
        return []


def analyze_transfers(client: "Bitvavo", asset: str) -> TransferSummary:
    """Analyze deposit and withdrawal history for an asset.

    Returns:
        TransferSummary with deposit/withdrawal analysis and potential rewards detection
    """
    deposits = fetch_deposit_history(client, asset)
    withdrawals = fetch_withdrawal_history(client, asset)

    total_deposits = Decimal("0")
    total_withdrawals = Decimal("0")
    deposit_count = len(deposits)
    withdrawal_count = len(withdrawals)

    # Process deposits
    for deposit in deposits:
        # Ensure deposit is a dictionary
        if not isinstance(deposit, dict):
            continue
        if deposit.get("status") == "completed":
            amount = _decimal(deposit.get("amount", "0"))
            total_deposits += amount

    # Process withdrawals
    for withdrawal in withdrawals:
        # Ensure withdrawal is a dictionary
        if not isinstance(withdrawal, dict):
            continue
        if withdrawal.get("status") == "completed":
            amount = _decimal(withdrawal.get("amount", "0"))
            total_withdrawals += amount

    net_transfers = total_deposits - total_withdrawals

    # Detect potential staking rewards/airdrops
    # Look for small, regular deposits that might be staking rewards
    potential_rewards = _detect_potential_rewards(deposits)

    return TransferSummary(
        total_deposits=total_deposits,
        total_withdrawals=total_withdrawals,
        net_transfers=net_transfers,
        deposit_count=deposit_count,
        withdrawal_count=withdrawal_count,
        potential_rewards=potential_rewards
    )


def _detect_potential_rewards(deposits: List[Dict[str, str]]) -> Decimal:
    """Detect potential staking rewards or airdrops from deposit patterns.

    This is a heuristic approach that looks for:
    - Small, regular deposits (likely staking rewards)
    - Deposits with specific patterns that suggest automated rewards
    - Deposits that are significantly smaller than typical manual deposits
    """
    if not deposits:
        return Decimal("0")

    potential_rewards = Decimal("0")

    # Sort deposits by timestamp, filtering out non-dict entries
    valid_deposits = [d for d in deposits if isinstance(d, dict)]
    sorted_deposits = sorted(valid_deposits, key=lambda x: int(x.get("timestamp", "0")))

    if len(sorted_deposits) < 2:
        return Decimal("0")  # Need at least 2 deposits to detect patterns

    # Calculate statistics about deposit amounts
    amounts = []
    for deposit in sorted_deposits:
        if deposit.get("status") == "completed":
            amount = _decimal(deposit.get("amount", "0"))
            if amount > 0:
                amounts.append(amount)

    if not amounts:
        return Decimal("0")

    # Calculate median and mean to identify outliers
    amounts.sort()
    median_amount = amounts[len(amounts) // 2]
    mean_amount = sum(amounts) / len(amounts)

    # Detect potential rewards using multiple heuristics
    for deposit in sorted_deposits:
        if deposit.get("status") != "completed":
            continue

        amount = _decimal(deposit.get("amount", "0"))
        if amount <= 0:
            continue

        # Heuristic 1: Very small amounts (< 1% of median) are likely rewards
        if amount < median_amount * Decimal("0.01"):
            potential_rewards += amount
            continue

        # Heuristic 2: Regular small amounts that are much smaller than typical deposits
        if amount < Decimal("1") and amount < mean_amount * Decimal("0.1"):
            # Check if this is part of a pattern of similar small amounts
            similar_count = sum(1 for a in amounts if abs(a - amount) < amount * Decimal("0.1"))
            if similar_count >= 3:  # At least 3 similar amounts suggest a pattern
                potential_rewards += amount
                continue

        # Heuristic 3: Amounts that are suspiciously round numbers in small denominations
        # (e.g., exactly 0.001, 0.01, etc.) might be automated rewards
        if amount in [Decimal("0.001"), Decimal("0.01"), Decimal("0.1")]:
            potential_rewards += amount

    return potential_rewards


def calculate_discrepancy_breakdown(
    fifo_amount: Decimal,
    actual_amount: Decimal,
    transfer_summary: TransferSummary
) -> Dict[str, Decimal]:
    """Calculate a breakdown of discrepancies between FIFO and actual amounts.

    Returns:
        Dictionary with discrepancy analysis:
        - total_discrepancy: Total difference between actual and FIFO
        - transfer_explained: Amount explained by net transfers
        - rewards_explained: Amount explained by potential rewards
        - unexplained: Remaining unexplained discrepancy
    """
    # Ensure both amounts are Decimal for consistent arithmetic
    fifo_amount = _decimal(str(fifo_amount))
    actual_amount = _decimal(str(actual_amount))

    total_discrepancy = actual_amount - fifo_amount

    # Amount explained by net transfers (deposits - withdrawals)
    transfer_explained = transfer_summary.net_transfers

    # Amount explained by potential rewards
    rewards_explained = transfer_summary.potential_rewards

    # Calculate unexplained discrepancy
    unexplained = total_discrepancy - transfer_explained - rewards_explained

    return {
        "total_discrepancy": total_discrepancy,
        "transfer_explained": transfer_explained,
        "rewards_explained": rewards_explained,
        "unexplained": unexplained,
        "explanation_percentage": (
            abs(transfer_explained + rewards_explained) / abs(total_discrepancy) * 100
            if total_discrepancy != 0 else Decimal("100")
        )
    }


def reconcile_portfolio_balances(client: "Bitvavo", assets: List[str]) -> Dict[str, Dict]:
    """Perform comprehensive reconciliation of portfolio balances.

    This function analyzes all assets and provides a complete breakdown of:
    - FIFO calculations vs actual balances
    - Transfer analysis (deposits/withdrawals)
    - Potential rewards detection
    - Discrepancy explanations

    Returns:
        Dictionary with reconciliation data for each asset and portfolio totals
    """
    reconciliation_data = {}
    portfolio_totals = {
        "total_fifo_amount": Decimal("0"),
        "total_actual_amount": Decimal("0"),
        "total_discrepancy": Decimal("0"),
        "total_transfer_explained": Decimal("0"),
        "total_rewards_explained": Decimal("0"),
        "total_unexplained": Decimal("0"),
        "assets_with_discrepancies": 0,
        "assets_fully_explained": 0,
    }

    for asset in assets:
        try:
            # Get FIFO calculation
            pnl = calculate_pnl(client, asset)
            fifo_amount = pnl["amount"]

            # Get actual balance
            balances = client.balance({"symbol": asset})  # type: ignore[arg-type]
            actual_amount = Decimal("0")
            if balances:
                balance = balances[0]
                actual_amount = _decimal(balance["available"]) + _decimal(balance["inOrder"])

            # Analyze transfers
            transfer_summary = analyze_transfers(client, asset)

            # Calculate discrepancy breakdown
            discrepancy_breakdown = calculate_discrepancy_breakdown(
                fifo_amount, actual_amount, transfer_summary
            )

            # Store asset reconciliation data
            reconciliation_data[asset] = {
                "fifo_amount": fifo_amount,
                "actual_amount": actual_amount,
                "transfer_summary": transfer_summary,
                "discrepancy_breakdown": discrepancy_breakdown,
                "reconciliation_status": _determine_reconciliation_status(discrepancy_breakdown)
            }

            # Update portfolio totals
            portfolio_totals["total_fifo_amount"] += fifo_amount
            portfolio_totals["total_actual_amount"] += actual_amount
            portfolio_totals["total_discrepancy"] += discrepancy_breakdown["total_discrepancy"]
            portfolio_totals["total_transfer_explained"] += discrepancy_breakdown["transfer_explained"]
            portfolio_totals["total_rewards_explained"] += discrepancy_breakdown["rewards_explained"]
            portfolio_totals["total_unexplained"] += discrepancy_breakdown["unexplained"]

            # Count assets with discrepancies
            if abs(discrepancy_breakdown["total_discrepancy"]) > Decimal("0.000001"):
                portfolio_totals["assets_with_discrepancies"] += 1

                # Check if discrepancy is well explained (>80% explained)
                if discrepancy_breakdown["explanation_percentage"] > 80:
                    portfolio_totals["assets_fully_explained"] += 1

        except Exception as exc:
            # Log error but continue with other assets
            reconciliation_data[asset] = {
                "error": str(exc),
                "reconciliation_status": "error"
            }

    # Calculate portfolio-level explanation percentage
    if portfolio_totals["total_discrepancy"] != 0:
        portfolio_totals["portfolio_explanation_percentage"] = (
            abs(portfolio_totals["total_transfer_explained"] + portfolio_totals["total_rewards_explained"])
            / abs(portfolio_totals["total_discrepancy"]) * 100
        )
    else:
        portfolio_totals["portfolio_explanation_percentage"] = Decimal("100")

    return {
        "assets": reconciliation_data,
        "portfolio_totals": portfolio_totals,
        "reconciliation_summary": _generate_reconciliation_summary(portfolio_totals)
    }


def _determine_reconciliation_status(discrepancy_breakdown: Dict[str, Decimal]) -> str:
    """Determine the reconciliation status based on discrepancy breakdown."""
    total_discrepancy = abs(discrepancy_breakdown["total_discrepancy"])
    explanation_pct = discrepancy_breakdown["explanation_percentage"]

    if total_discrepancy < Decimal("0.000001"):
        return "perfect_match"
    elif explanation_pct > 95:
        return "fully_explained"
    elif explanation_pct > 80:
        return "well_explained"
    elif explanation_pct > 50:
        return "partially_explained"
    else:
        return "poorly_explained"


def _generate_reconciliation_summary(portfolio_totals: Dict) -> Dict[str, str]:
    """Generate a human-readable summary of the reconciliation results."""
    total_assets = portfolio_totals["assets_with_discrepancies"]
    explained_assets = portfolio_totals["assets_fully_explained"]
    explanation_pct = float(portfolio_totals["portfolio_explanation_percentage"])

    if total_assets == 0:
        status = "excellent"
        message = "Perfect match! All FIFO calculations align with actual balances."
    elif explanation_pct > 90:
        status = "excellent"
        message = f"Excellent reconciliation! {explanation_pct:.1f}% of discrepancies explained by transfers and rewards."
    elif explanation_pct > 70:
        status = "good"
        message = f"Good reconciliation. {explanation_pct:.1f}% of discrepancies explained. Some minor unexplained differences remain."
    elif explanation_pct > 50:
        status = "fair"
        message = f"Fair reconciliation. {explanation_pct:.1f}% explained. Consider reviewing missing transactions or data."
    else:
        status = "poor"
        message = f"Poor reconciliation. Only {explanation_pct:.1f}% explained. Significant data may be missing."

    return {
        "status": status,
        "message": message,
        "assets_with_discrepancies": total_assets,
        "assets_fully_explained": explained_assets,
        "explanation_percentage": explanation_pct
    }
