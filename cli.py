"""
Modern CLI interface for crypto portfolio analysis using Clean Architecture backend.

Provides command-line interface for portfolio reporting, analysis, and AI chat.
"""

import sys
import os
from typing import Optional, List
import typer
import requests
from rich.console import Console
from rich.table import Table
from rich import print as rprint

# Add frontend to path for API client
sys.path.append("frontend")
from frontend.api_client import SyncCryptoPortfolioAPIClient, APIException

app = typer.Typer(help="🚀 Crypto Portfolio CLI - Clean Architecture Edition")
console = Console()

def get_api_client() -> SyncCryptoPortfolioAPIClient:
    """Get API client instance."""
    return SyncCryptoPortfolioAPIClient(base_url="http://localhost:8000")

@app.command()
def summary():
    """📊 Display portfolio summary."""
    try:
        client = get_api_client()
        summary = client.get_portfolio_summary()
        
        console.print("\n🚀 [bold blue]Portfolio Summary[/bold blue]")
        console.print("=" * 50)
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Value", f"€{summary.total_value_eur:,.2f}")
        table.add_row("Total Cost", f"€{summary.total_cost_eur:,.2f}")
        table.add_row("Unrealized P&L", f"€{summary.unrealized_pnl:,.2f}")
        table.add_row("Realized P&L", f"€{summary.realized_pnl:,.2f}")
        table.add_row("Total Return", f"{summary.total_return_percentage:.2f}%")
        table.add_row("Assets Count", str(summary.assets_count))
        
        console.print(table)
        
    except APIException as e:
        console.print(f"[red]❌ API Error: {e.message}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def holdings(
    asset: Optional[str] = typer.Option(None, "--asset", "-a", help="Filter by specific asset"),
    top: Optional[int] = typer.Option(None, "--top", "-t", help="Show top N performers"),
    losers: Optional[int] = typer.Option(None, "--losers", "-l", help="Show worst N performers")
):
    """💰 Display portfolio holdings."""
    try:
        client = get_api_client()
        holdings = client.get_current_holdings()
        
        # Apply filters
        if asset:
            holdings = [h for h in holdings if h.asset.upper() == asset.upper()]
        elif top:
            holdings = sorted(holdings, key=lambda h: h.total_return_percentage, reverse=True)[:top]
        elif losers:
            holdings = sorted(holdings, key=lambda h: h.total_return_percentage)[:losers]
        
        if not holdings:
            console.print("[yellow]⚠️ No holdings found matching criteria[/yellow]")
            return
        
        console.print(f"\n💰 [bold blue]Portfolio Holdings[/bold blue] ({len(holdings)} assets)")
        console.print("=" * 80)
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Asset", style="cyan")
        table.add_column("Quantity", justify="right")
        table.add_column("Price €", justify="right")
        table.add_column("Value €", justify="right", style="green")
        table.add_column("P&L €", justify="right")
        table.add_column("Return %", justify="right")
        
        for holding in holdings:
            pnl_style = "green" if holding.unrealized_pnl >= 0 else "red"
            return_style = "green" if holding.total_return_percentage >= 0 else "red"
            
            table.add_row(
                holding.asset,
                f"{holding.quantity:.6f}",
                f"{holding.current_price_eur:.4f}",
                f"{holding.value_eur:,.2f}",
                f"[{pnl_style}]{holding.unrealized_pnl:,.2f}[/{pnl_style}]",
                f"[{return_style}]{holding.total_return_percentage:.2f}%[/{return_style}]"
            )
        
        console.print(table)
        
    except APIException as e:
        console.print(f"[red]❌ API Error: {e.message}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def chat(message: str = typer.Argument(..., help="Message to send to AI")):
    """🤖 Chat with AI about your portfolio."""
    try:
        client = get_api_client()
        
        console.print(f"\n🤖 [bold blue]AI Analysis[/bold blue]")
        console.print("=" * 50)
        console.print(f"[cyan]You:[/cyan] {message}")
        
        with console.status("[bold green]AI is thinking..."):
            response = client.chat_query(
                message=message,
                use_function_calling=True,
                temperature=0.1
            )
        
        console.print(f"\n[green]🤖 AI:[/green] {response.response}")
        
        # Show function calls if any
        if hasattr(response, 'function_calls') and response.function_calls:
            console.print("\n[yellow]🔧 Function Calls Used:[/yellow]")
            for func_call in response.function_calls:
                status = "✅" if func_call.success else "❌"
                console.print(f"  {status} {func_call.function_name}")
        
    except APIException as e:
        console.print(f"[red]❌ API Error: {e.message}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def refresh():
    """🔄 Refresh portfolio data from Bitvavo."""
    try:
        client = get_api_client()
        
        with console.status("[bold green]Refreshing portfolio data..."):
            success = client.refresh_portfolio_data()
        
        if success:
            console.print("[green]✅ Portfolio data refreshed successfully![/green]")
        else:
            console.print("[red]❌ Failed to refresh portfolio data[/red]")
            raise typer.Exit(1)
            
    except APIException as e:
        console.print(f"[red]❌ API Error: {e.message}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def status():
    """🔗 Check backend connection status."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            console.print("[green]✅ Backend is running and healthy![/green]")
        else:
            console.print(f"[red]❌ Backend returned status {response.status_code}[/red]")
            raise typer.Exit(1)
    except requests.exceptions.ConnectionError:
        console.print("[red]❌ Backend is not running![/red]")
        console.print("[yellow]💡 Start it with: .\\scripts\\start-local.ps1[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error checking backend: {e}[/red]")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
