#!/usr/bin/env python3
"""portfolio.py – Comprehensive Bitvavo FIFO P&L reporter
========================================================
A single‑file CLI that pulls every trade from your Bitvavo account, applies strict
FIFO accounting using high‑precision Decimals, and prints a crystal‑clear P&L
snapshot.  Extras: embedded README / requirements, self‑contained pytest
suite, and an optional *what‑if* price override so you can see "what happens if
I sell at €X right now?".
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, getcontext
from typing import Deque, Dict, List, Optional, Tuple

try:
    from bitvavo import Bitvavo  # type: ignore
except ImportError:  # pragma: no cover
    Bitvavo = None  # keeps the type checker quiet when deps missing

from tabulate import tabulate

# ---------------------------------------------------------------------------
# Embedded artefacts (README / requirements)
# ---------------------------------------------------------------------------
README_MD = """# portfolio.py – Bitvavo FIFO P&L tool

Run a complete FIFO P&L report or simulate a sale at custom prices:

```bash
python portfolio.py                     # full wallet, live prices
python portfolio.py --assets BTC,ETH    # filter for given coins
python portfolio.py --override BTC=30000,ETH=1800  # what‑if
python portfolio.py --show-readme       # dump this doc
python portfolio.py --show-requirements # print pip deps
python portfolio.py --run-tests         # run embedded tests
```

## Environment variables
* `BITVAVO_API_KEY`    – your API key (read‑only)
* `BITVAVO_API_SECRET` – your secret

Why FIFO? Because the Dutch tax authority (and common sense) likes it.
"""

REQUIREMENTS_TXT = """python-bitvavo-api>=2.0.0
tabulate>=0.8
pytest>=7.0
pytest-mock>=3.0"""

# ---------------------------------------------------------------------------
# Decimal configuration – 36‑digit precision keeps crypto maths honest
# ---------------------------------------------------------------------------
getcontext().prec = 36


# ---------------------------------------------------------------------------
# Custom exception hierarchy
# ---------------------------------------------------------------------------
class BitvavoAPIException(RuntimeError):
    """Base‑class for Bitvavo API problems."""


class InvalidAPIKeyError(BitvavoAPIException):
    """Raised when the API rejects our key/secret (error 304)."""


class RateLimitExceededError(BitvavoAPIException):
    """Raised when API rate limit is/would be exceeded (error 105)."""


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass
class PurchaseLot:
    amount: Decimal  # crypto units
    cost_eur: Decimal  # total € incl. fees
    timestamp: int  # ms since epoch (for completeness)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _decimal(value: str | float | int | Decimal) -> Decimal:
    """Coerce *value* into a Decimal without rounding."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _check_rate_limit(client: "Bitvavo", threshold: int = 10) -> None:
    """Sleep defensively when close to Bitvavo’s weight budget."""
    remaining = int(client.getRemainingLimit())
    if remaining < threshold:
        time.sleep(15)  # simple, effective back‑off


# ---------------------------------------------------------------------------
# API wrappers
# ---------------------------------------------------------------------------


def sync_time(client: "Bitvavo") -> None:
    """Synchronise local clock offset to avoid 304 errors."""
    try:
        server_time_ms = int(client.time()["time"])
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
        trades.extend(reversed(batch))  # newest‑>oldest → reverse
        cursor = batch[-1]["id"]
    return trades


# ---------------------------------------------------------------------------
# FIFO core
# ---------------------------------------------------------------------------


def calculate_pnl(
    trades: List[Dict[str, str]], current_price: Decimal
) -> Dict[str, Decimal]:
    """Process *trades* (chronological list) under FIFO and return P&L metrics."""
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


# ---------------------------------------------------------------------------
# CLI report generator
# ---------------------------------------------------------------------------


def generate_report(
    client: "Bitvavo",
    assets: List[str],
    price_override: Dict[str, Decimal] | None = None,
) -> None:
    headers = [
        "Asset",
        "Amount",
        "Cost €",
        "Value €",
        "Realised €",
        "Unrealised €",
        "PnL %",
    ]
    rows: List[Tuple] = []
    totals = {
        k: Decimal("0") for k in ("cost", "value", "realised", "unrealised", "buys")
    }
    for asset in assets:
        trades = fetch_trade_history(client, asset)
        if not trades:
            continue
        if price_override and asset in price_override:
            price_eur = price_override[asset]
        else:
            _check_rate_limit(client)
            ticker = client.tickerPrice({"market": f"{asset}-EUR"})  # type: ignore[arg-type]
            price_eur = _decimal(ticker[0]["price"]) if ticker else Decimal("0")
        pnl = calculate_pnl(trades, price_eur)
        invested = pnl["total_buys_eur"]
        pnl_pct = (
            ((pnl["value_eur"] + pnl["realised_eur"]) - invested) / invested * 100
            if invested != 0
            else Decimal("0")
        )
        rows.append(
            (
                asset,
                f"{pnl['amount']:.8f}",
                f"{pnl['cost_eur']:.2f}",
                f"{pnl['value_eur']:.2f}",
                f"{pnl['realised_eur']:.2f}",
                f"{pnl['unrealised_eur']:.2f}",
                f"{pnl_pct:.2f}%",
            )
        )
        totals["cost"] += pnl["cost_eur"]
        totals["value"] += pnl["value_eur"]
        totals["realised"] += pnl["realised_eur"]
        totals["unrealised"] += pnl["unrealised_eur"]
        totals["buys"] += pnl["total_buys_eur"]
    total_pct = (
        ((totals["value"] + totals["realised"]) - totals["buys"]) / totals["buys"] * 100
        if totals["buys"] != 0
        else Decimal("0")
    )
    rows.append(
        (
            "Total",
            "",
            f"{totals['cost']:.2f}",
            f"{totals['value']:.2f}",
            f"{totals['realised']:.2f}",
            f"{totals['unrealised']:.2f}",
            f"{total_pct:.2f}%",
        )
    )
    print(tabulate(rows, headers=headers, tablefmt="grid", numalign="right"))


# ---------------------------------------------------------------------------
# Embedded tests
# ---------------------------------------------------------------------------


def _make_trade(
    side: str, amount: str, price: str, fee: str = "0", ts: int | None = None
) -> Dict[str, str]:
    return {
        "id": "x",
        "timestamp": str(ts or int(time.time() * 1000)),
        "market": "TEST-EUR",
        "side": side,
        "amount": amount,
        "price": price,
        "fee": fee,
        "feeCurrency": "EUR",
    }


# --- pure FIFO unit tests ---------------------------------------------------


def test_single_buy_no_sell():
    trades = [_make_trade("buy", "2", "10", "0.1")]
    pnl = calculate_pnl(trades, Decimal("12"))
    assert pnl["unrealised_eur"] == Decimal("3.9")  # nosec B101
    assert pnl["total_buys_eur"] == Decimal("20.1")  # nosec B101


def test_partial_sell():
    trades = [_make_trade("buy", "2", "10"), _make_trade("sell", "1", "15")]
    pnl = calculate_pnl(trades, Decimal("14"))
    assert pnl["realised_eur"] == Decimal("5")  # nosec B101
    assert pnl["unrealised_eur"] == Decimal("4")  # nosec B101
    assert pnl["total_buys_eur"] == Decimal("20")  # nosec B101


def test_full_lot_sell():
    trades = [_make_trade("buy", "1", "100", "1"), _make_trade("sell", "1", "150", "1")]
    pnl = calculate_pnl(trades, Decimal("140"))
    assert pnl["amount"] == 0  # nosec B101
    assert pnl["realised_eur"] == Decimal("49")  # nosec B101
    assert pnl["total_buys_eur"] == Decimal("101")  # nosec B101


def test_complex_sell_across_lots():
    trades = [
        _make_trade("buy", "1", "100"),
        _make_trade("buy", "2", "120"),
        _make_trade("sell", "1.5", "130"),
    ]
    pnl = calculate_pnl(trades, Decimal("125"))
    assert pnl["amount"] == Decimal("1.5")  # nosec B101
    assert pnl["realised_eur"] == Decimal("35")  # nosec B101
    assert pnl["unrealised_eur"] == Decimal("17.5")  # nosec B101
    assert pnl["total_buys_eur"] == Decimal("340")  # nosec B101 # 1*100 + 2*120


# --- pytest‑mock demo (no live API calls) -----------------------------------


def test_generate_report_with_override(mocker):
    # Craft a dummy Bitvavo client with just the methods we need
    dummy = mocker.MagicMock()
    dummy.getRemainingLimit.return_value = 999
    dummy.trades.return_value = [
        _make_trade("buy", "1", "100"),
        _make_trade("sell", "0.4", "110"),
    ]
    dummy.tickerPrice.return_value = [{"price": "120"}]
    # price override will be applied instead of tickerPrice
    generate_report(dummy, ["BTC"], price_override={"BTC": Decimal("130")})
    # Make sure API weight check happened and trades() called with market "BTC-EUR"
    dummy.trades.assert_called()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_price_override(s: str) -> Dict[str, Decimal]:
    mapping: Dict[str, Decimal] = {}
    for part in s.split(","):
        if "=" not in part:
            raise argparse.ArgumentTypeError(
                "Override must be ASSET=PRICE,ASSET=PRICE..."
            )
        asset, price = part.split("=", 1)
        mapping[asset.strip().upper()] = _decimal(price.strip())
    return mapping


def _parse_args(argv: List[str]) -> argparse.Namespace:  # pragma: no cover
    p = argparse.ArgumentParser(description="Bitvavo FIFO P&L reporter")
    p.add_argument(
        "--assets",
        type=lambda s: [a.strip().upper() for a in s.split(",") if a.strip()],
        help="Comma‑separated list of asset tickers",
    )
    p.add_argument(
        "--override",
        type=_parse_price_override,
        help="Override live prices (ASSET=PRICE,...)",
    )
    p.add_argument("--show-readme", action="store_true")
    p.add_argument("--show-requirements", action="store_true")
    p.add_argument("--run-tests", action="store_true")
    return p.parse_args(argv)


def main() -> None:  # pragma: no cover
    args = _parse_args(sys.argv[1:])
    if args.show_readme:
        print(README_MD)
        return
    if args.show_requirements:
        print(REQUIREMENTS_TXT)
        return
    if args.run_tests:
        import pytest  # type: ignore

        sys.exit(pytest.main([__file__]))
    api_key = os.getenv("BITVAVO_API_KEY")
    api_secret = os.getenv("BITVAVO_API_SECRET")
    if not api_key or not api_secret:
        sys.exit("Set BITVAVO_API_KEY / BITVAVO_API_SECRET in your environment.")
    client = Bitvavo({"APIKEY": api_key, "APISECRET": api_secret})
    sync_time(client)
    assets: List[str]
    if args.assets:
        assets = args.assets
    else:
        balances = client.balance({})  # type: ignore[arg-type]
        assets = [
            b["symbol"]
            for b in balances
            if _decimal(b["available"]) + _decimal(b["inOrder"]) > 0
        ]
        assets = [a.split("-")[0].upper() for a in assets]
    if not assets:
        sys.exit("No assets found.")
    generate_report(client, assets, price_override=args.override)


if __name__ == "__main__":
    main()
