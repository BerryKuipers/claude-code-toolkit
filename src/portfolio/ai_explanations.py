"""Natural language explanations for crypto portfolio positions.

This module provides functions to generate human-readable explanations
of cryptocurrency positions, including profit/loss analysis and transfer details.
"""

from typing import Any, Dict

# Constants
FLOAT_EQUALITY_THRESHOLD = 1e-6  # Threshold for float comparison


def generate_coin_explanation(
    asset_data: Dict[str, Any], include_transfers: bool = True
) -> str:
    """Generate natural language explanation for a coin position.

    Args:
        asset_data: Dictionary containing asset information with keys:
            - Asset: Asset symbol (e.g., 'BTC', 'ETH')
            - FIFO Amount: Amount calculated from trade history
            - Actual Amount: Real current balance on exchange
            - Amount Diff: Difference between FIFO and actual amounts
            - Cost €: Total EUR cost including fees
            - FIFO Value €: Value based on FIFO calculation
            - Actual Value €: Value based on real holdings
            - Realised €: Profit/loss from completed trades
            - Unrealised €: Current profit/loss on holdings
            - Total Return %: Overall performance percentage
            - Current Price €: Current market price per coin
            - Net Transfers: Net amount transferred (deposits - withdrawals)
            - Total Deposits: Total amount deposited
            - Total Withdrawals: Total amount withdrawn
            - Deposit Count: Number of deposit transactions
            - Withdrawal Count: Number of withdrawal transactions
        include_transfers: Whether to include transfer information in explanation

    Returns:
        Natural language explanation string
    """
    asset = asset_data["Asset"]
    fifo_amount = asset_data["FIFO Amount"]
    actual_amount = asset_data["Actual Amount"]
    amount_diff = asset_data["Amount Diff"]
    cost_eur = asset_data["Cost €"]
    actual_value_eur = asset_data["Actual Value €"]
    unrealised_eur = asset_data["Unrealised €"]
    total_return_pct = asset_data["Total Return %"]
    current_price = asset_data["Current Price €"]
    net_transfers = asset_data.get("Net Transfers", 0)
    total_deposits = asset_data.get("Total Deposits", 0)
    total_withdrawals = asset_data.get("Total Withdrawals", 0)

    # Determine profit/loss status and emoji
    if unrealised_eur > 0:
        status_emoji = "🟢"
        action_word = "profit"
        direction = "gain"
    elif unrealised_eur < 0:
        status_emoji = "🔴"
        action_word = "lose"
        direction = "loss"
    else:
        status_emoji = "🟡"
        action_word = "break even"
        direction = "break-even"

    # Handle different scenarios based on transfers and amount differences
    if (
        abs(amount_diff) < FLOAT_EQUALITY_THRESHOLD
    ):  # No significant difference between FIFO and actual
        # Standard trading position
        if fifo_amount > 0:
            avg_price = cost_eur / fifo_amount
            explanation = f"{status_emoji} You own {actual_amount:.6f} {asset} "
            explanation += f"purchased at an average price of {format_currency(avg_price)} per coin. "
            explanation += f"If you sell now at {format_currency(current_price)}, you would {action_word} "
            explanation += f"€{abs(unrealised_eur):.2f} ({total_return_pct:+.1f}%). "
            explanation += f"Your total investment of €{cost_eur:.2f} would become €{actual_value_eur:.2f}."
        else:
            explanation = f"🔵 You currently have no {asset} position from trading."

    elif amount_diff > 0:  # More actual than FIFO (deposits/transfers in)
        if fifo_amount > 0:
            # Mixed position: some from trading, some from deposits
            avg_price = cost_eur / fifo_amount
            explanation = f"{status_emoji} You own {actual_amount:.6f} {asset} with "
            explanation += (
                f"{fifo_amount:.6f} from trades (avg {format_currency(avg_price)}) and "
            )
            explanation += f"{amount_diff:.6f} from deposits/transfers. "

            if include_transfers and total_deposits > 0:
                explanation += (
                    f"You've deposited {total_deposits:.6f} {asset} in total. "
                )

            explanation += f"If you sell now at {format_currency(current_price)}, your traded coins would {action_word} "
            explanation += f"€{abs(unrealised_eur):.2f} ({total_return_pct:+.1f}%). "
            explanation += f"Your total position is worth €{actual_value_eur:.2f}."
        else:
            # Only deposits, no trading
            explanation = f"🔵 You own {actual_amount:.6f} {asset} entirely from deposits/transfers. "
            if include_transfers and total_deposits > 0:
                explanation += (
                    f"You've deposited {total_deposits:.6f} {asset} in total. "
                )
            explanation += f"Your position is currently worth €{actual_value_eur:.2f} at {format_currency(current_price)} per coin."

    else:  # Less actual than FIFO (withdrawals/transfers out)
        # Some coins were withdrawn
        withdrawn_amount = abs(amount_diff)
        if actual_amount > 0:
            avg_price = cost_eur / fifo_amount if fifo_amount > 0 else 0
            explanation = f"{status_emoji} You own {actual_amount:.6f} {asset} "
            explanation += f"(originally had {fifo_amount:.6f} from trades at avg {format_currency(avg_price)}). "
            explanation += f"You've withdrawn {withdrawn_amount:.6f} {asset}. "

            if include_transfers and total_withdrawals > 0:
                explanation += f"Total withdrawals: {total_withdrawals:.6f} {asset}. "

            explanation += f"If you sell your remaining {actual_amount:.6f} now at {format_currency(current_price)}, "
            explanation += f"you would {action_word} €{abs(unrealised_eur):.2f} ({total_return_pct:+.1f}%). "
            explanation += f"Your remaining position is worth €{actual_value_eur:.2f}."
        else:
            # All coins were withdrawn
            explanation = (
                f"🔵 You previously owned {fifo_amount:.6f} {asset} from trades "
            )
            explanation += f"but have withdrawn all of it. "
            if include_transfers and total_withdrawals > 0:
                explanation += f"Total withdrawals: {total_withdrawals:.6f} {asset}. "
            explanation += f"You currently have no {asset} position."

    return explanation


def get_position_summary(asset_data: Dict[str, Any]) -> str:
    """Get a brief summary of the position status.

    Args:
        asset_data: Dictionary containing asset information

    Returns:
        Brief position summary string
    """
    asset = asset_data["Asset"]
    actual_amount = asset_data["Actual Amount"]
    unrealised_eur = asset_data["Unrealised €"]
    total_return_pct = asset_data["Total Return %"]

    if actual_amount <= 0:
        return f"No {asset} position"

    if unrealised_eur > 0:
        return f"Profitable {asset} position (+{total_return_pct:.1f}%)"
    elif unrealised_eur < 0:
        return f"Loss {asset} position ({total_return_pct:.1f}%)"
    else:
        return f"Break-even {asset} position"


def format_currency(amount: float, currency: str = "€") -> str:
    """Format currency amount with appropriate precision.

    Args:
        amount: Amount to format
        currency: Currency symbol

    Returns:
        Formatted currency string
    """
    if abs(amount) >= 1000:
        return f"{currency}{amount:,.0f}"
    elif abs(amount) >= 1:
        return f"{currency}{amount:.2f}"
    elif abs(amount) >= 0.01:
        return f"{currency}{amount:.4f}"
    elif abs(amount) >= 0.0001:
        return f"{currency}{amount:.6f}"
    else:
        return f"{currency}{amount:.8f}"


def format_crypto_amount(amount: float, asset: str) -> str:
    """Format cryptocurrency amount with appropriate precision.

    Args:
        amount: Amount to format
        asset: Asset symbol

    Returns:
        Formatted crypto amount string
    """
    if abs(amount) >= 1:
        return f"{amount:.6f} {asset}"
    else:
        return f"{amount:.8f} {asset}"
