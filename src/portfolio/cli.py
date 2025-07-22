"""Typer CLI interface for crypto portfolio analysis.

Provides command-line interface for FIFO P&L reporting with support for
asset filtering, price overrides, and what-if scenarios.
"""

import os
import sys
from decimal import Decimal
from typing import Dict, List, Optional

import typer
from python_bitvavo_api.bitvavo import Bitvavo
from tabulate import tabulate

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file."""
    # Look for .env file in the project root (two levels up from this file)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    env_file = os.path.join(project_root, '.env')

    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# Load environment variables at module import
load_env_file()

from .core import (
    sync_time,
    fetch_trade_history,
    calculate_pnl,
    get_current_price,
    get_portfolio_assets,
    _decimal,
    _check_rate_limit,
    BitvavoAPIException,
    InvalidAPIKeyError,
    RateLimitExceededError,
)

app = typer.Typer(
    name="portfolio",
    help="Crypto Portfolio FIFO P&L Analysis Tool",
    no_args_is_help=True,
)


def _parse_price_override(override_str: str) -> Dict[str, Decimal]:
    """Parse price override string like 'BTC=35000,ETH=1800' into dict."""
    overrides = {}
    if not override_str:
        return overrides

    for pair in override_str.split(","):
        pair = pair.strip()
        if not pair:  # Skip empty pairs
            continue
        if "=" not in pair:
            typer.echo(f"Invalid price override format '{pair}': must be ASSET=PRICE", err=True)
            raise typer.Exit(1)

        asset, price_str = pair.split("=", 1)
        asset = asset.strip().upper()
        price_str = price_str.strip()

        if not asset or not price_str:
            typer.echo(f"Invalid price override '{pair}': asset and price cannot be empty", err=True)
            raise typer.Exit(1)

        try:
            overrides[asset] = _decimal(price_str)
        except Exception as exc:
            typer.echo(f"Invalid price value '{price_str}' for {asset}: {exc}", err=True)
            raise typer.Exit(1)

    return overrides


def _get_bitvavo_client() -> Bitvavo:
    """Initialize and return authenticated Bitvavo client."""
    api_key = os.getenv("BITVAVO_API_KEY")
    api_secret = os.getenv("BITVAVO_API_SECRET")
    
    if not api_key or not api_secret:
        typer.echo("Error: Set BITVAVO_API_KEY and BITVAVO_API_SECRET environment variables", err=True)
        raise typer.Exit(1)
    
    client = Bitvavo({"APIKEY": api_key, "APISECRET": api_secret})
    
    try:
        sync_time(client)
    except BitvavoAPIException as exc:
        typer.echo(f"Error connecting to Bitvavo API: {exc}", err=True)
        raise typer.Exit(1)
    
    return client


def _generate_report_table(
    client: Bitvavo, 
    assets: List[str], 
    price_override: Optional[Dict[str, Decimal]] = None
) -> None:
    """Generate and display P&L report table."""
    headers = [
        "Asset",
        "Amount", 
        "Cost €",
        "Value €",
        "Realised €",
        "Unrealised €",
        "PnL %",
    ]
    
    rows = []
    totals = {k: Decimal("0") for k in ("cost", "value", "realised", "unrealised", "buys")}
    
    for asset in assets:
        try:
            trades = fetch_trade_history(client, asset)
            if not trades:
                continue
            
            # Get current price (override or live)
            if price_override and asset in price_override:
                price_eur = price_override[asset]
            else:
                price_eur = get_current_price(client, asset)
            
            pnl = calculate_pnl(trades, price_eur)
            invested = pnl["total_buys_eur"]
            
            # Calculate total return percentage
            pnl_pct = (
                ((pnl["value_eur"] + pnl["realised_eur"]) - invested) / invested * 100
                if invested != 0
                else Decimal("0")
            )
            
            rows.append((
                asset,
                f"{pnl['amount']:.8f}",
                f"{pnl['cost_eur']:.2f}",
                f"{pnl['value_eur']:.2f}",
                f"{pnl['realised_eur']:.2f}",
                f"{pnl['unrealised_eur']:.2f}",
                f"{pnl_pct:.2f}%",
            ))
            
            # Update totals
            totals["cost"] += pnl["cost_eur"]
            totals["value"] += pnl["value_eur"]
            totals["realised"] += pnl["realised_eur"]
            totals["unrealised"] += pnl["unrealised_eur"]
            totals["buys"] += pnl["total_buys_eur"]
            
        except (BitvavoAPIException, InvalidAPIKeyError, RateLimitExceededError) as exc:
            typer.echo(f"Error processing {asset}: {exc}", err=True)
            continue
    
    # Add totals row
    total_pct = (
        ((totals["value"] + totals["realised"]) - totals["buys"]) / totals["buys"] * 100
        if totals["buys"] != 0
        else Decimal("0")
    )
    
    rows.append((
        "Total",
        "",
        f"{totals['cost']:.2f}",
        f"{totals['value']:.2f}",
        f"{totals['realised']:.2f}",
        f"{totals['unrealised']:.2f}",
        f"{total_pct:.2f}%",
    ))
    
    typer.echo(tabulate(rows, headers=headers, tablefmt="grid", numalign="right"))


@app.command()
def report(
    assets: Optional[str] = typer.Option(
        None,
        "--assets",
        "-a",
        help="Comma-separated list of asset tickers (e.g., BTC,ETH). If not provided, all assets with balances are included."
    ),
    override: Optional[str] = typer.Option(
        None,
        "--override",
        "-o", 
        help="Override live prices (e.g., BTC=35000,ETH=1800)"
    ),
) -> None:
    """Generate FIFO P&L report for your portfolio."""
    client = _get_bitvavo_client()
    
    # Parse price overrides
    price_override = _parse_price_override(override or "")
    
    # Determine assets to analyze
    if assets:
        asset_list = [a.strip().upper() for a in assets.split(",") if a.strip()]
    else:
        try:
            asset_list = get_portfolio_assets(client)
        except BitvavoAPIException as exc:
            typer.echo(f"Error fetching portfolio assets: {exc}", err=True)
            raise typer.Exit(1)
    
    if not asset_list:
        typer.echo("No assets found to analyze")
        raise typer.Exit(1)
    
    typer.echo(f"Generating P&L report for: {', '.join(asset_list)}")
    if price_override:
        typer.echo(f"Price overrides: {price_override}")
    typer.echo()
    
    _generate_report_table(client, asset_list, price_override)


@app.command()
def whatif(
    price: str = typer.Argument(
        ...,
        help="Price override in format ASSET=PRICE (e.g., BTC=35000)"
    ),
    assets: Optional[str] = typer.Option(
        None,
        "--assets",
        "-a",
        help="Comma-separated list of asset tickers. If not provided, uses the asset from price argument."
    ),
) -> None:
    """Run what-if scenario with custom price."""
    # Parse the price argument
    if "=" not in price:
        typer.echo("Error: Price must be in format ASSET=PRICE (e.g., BTC=35000)", err=True)
        raise typer.Exit(1)
    
    asset, price_str = price.split("=", 1)
    asset = asset.upper()
    
    try:
        price_value = _decimal(price_str)
    except Exception:
        typer.echo(f"Error: Invalid price value '{price_str}'", err=True)
        raise typer.Exit(1)
    
    price_override = {asset: price_value}
    
    # Determine assets to analyze
    if assets:
        asset_list = [a.strip().upper() for a in assets.split(",") if a.strip()]
    else:
        asset_list = [asset]
    
    client = _get_bitvavo_client()
    
    typer.echo(f"What-if scenario: {asset} at €{price_value}")
    typer.echo(f"Analyzing assets: {', '.join(asset_list)}")
    typer.echo()
    
    _generate_report_table(client, asset_list, price_override)


@app.command()
def sync_balances() -> None:
    """Sync and display current balances (future feature stub)."""
    typer.echo("🚧 Feature coming soon: Sync balances from Bitvavo")
    typer.echo("This will fetch and cache current balances for faster reporting.")


if __name__ == "__main__":
    app()
