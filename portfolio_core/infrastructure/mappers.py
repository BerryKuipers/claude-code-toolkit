"""
Data Mappers

Convert between external API data formats and domain entities.
These mappers isolate the domain from external data structure changes.
"""

import logging
from decimal import Decimal
from typing import Dict, List, Any

from ..domain.entities import Trade
from ..domain.value_objects import AssetSymbol, AssetAmount, Money, TradeType, Timestamp

logger = logging.getLogger(__name__)


class BitvavoDataMapper:
    """
    Maps Bitvavo API data to domain entities.
    
    This mapper isolates the domain from Bitvavo's specific data formats
    and handles any data transformation needed.
    """
    
    @staticmethod
    def map_trade_data_to_domain(trade_data: Dict[str, Any]) -> Trade:
        """
        Map Bitvavo trade data to domain Trade entity.
        
        Args:
            trade_data: Raw trade data from Bitvavo API
            
        Returns:
            Domain Trade entity
            
        Raises:
            ValueError: If trade data is invalid or incomplete
        """
        try:
            # Extract market symbol (e.g., "BTC-EUR" -> "BTC")
            market = trade_data.get("market", "")
            if "-EUR" in market:
                asset_symbol = market.replace("-EUR", "")
            else:
                # Fallback: try to extract asset from market string
                parts = market.split("-")
                asset_symbol = parts[0] if parts else "UNKNOWN"
            
            # Map trade side
            side = trade_data.get("side", "").lower()
            if side == "buy":
                trade_type = TradeType.BUY
            elif side == "sell":
                trade_type = TradeType.SELL
            else:
                raise ValueError(f"Invalid trade side: {side}")
            
            # Extract amounts and prices
            amount = Decimal(str(trade_data.get("amount", "0")))
            price = Decimal(str(trade_data.get("price", "0")))
            fee = Decimal(str(trade_data.get("fee", "0")))
            timestamp = int(trade_data.get("timestamp", "0"))
            
            # Validate required fields
            if amount <= 0:
                raise ValueError(f"Invalid trade amount: {amount}")
            if price <= 0:
                raise ValueError(f"Invalid trade price: {price}")
            if timestamp <= 0:
                raise ValueError(f"Invalid trade timestamp: {timestamp}")
            
            # Create domain entities
            asset = AssetSymbol(asset_symbol)
            asset_amount = AssetAmount(amount, asset)
            price_money = Money(price, "EUR")
            fee_money = Money(fee, "EUR")
            trade_timestamp = Timestamp(timestamp)
            
            return Trade(
                asset=asset,
                trade_type=trade_type,
                amount=asset_amount,
                price=price_money,
                fee=fee_money,
                timestamp=trade_timestamp
            )
            
        except Exception as e:
            logger.error(f"Failed to map trade data to domain: {e}")
            logger.error(f"Trade data: {trade_data}")
            # Don't raise for negative fees - log and skip instead
            if "Trade fee cannot be negative" in str(e):
                logger.info(f"Skipping trade with negative fee (likely rebate): {trade_data.get('fee', 'N/A')}")
                raise ValueError(f"Trade with negative fee skipped: {e}") from e
            raise ValueError(f"Invalid trade data: {e}") from e
    
    @staticmethod
    def map_trades_list_to_domain(trades_data: List[Dict[str, Any]]) -> List[Trade]:
        """
        Map a list of Bitvavo trade data to domain Trade entities.
        
        Args:
            trades_data: List of raw trade data from Bitvavo API
            
        Returns:
            List of domain Trade entities
        """
        trades = []
        for trade_data in trades_data:
            try:
                trade = BitvavoDataMapper.map_trade_data_to_domain(trade_data)
                trades.append(trade)
            except ValueError as e:
                logger.warning(f"Skipping invalid trade data: {e}")
                continue
        
        return trades
    
    @staticmethod
    def map_balance_data_to_amounts(balance_data: List[Dict[str, Any]]) -> Dict[AssetSymbol, AssetAmount]:
        """
        Map Bitvavo balance data to asset amounts.
        
        Args:
            balance_data: Raw balance data from Bitvavo API
            
        Returns:
            Dictionary mapping asset symbols to amounts
        """
        balances = {}
        
        for balance_item in balance_data:
            try:
                symbol_str = balance_item.get("symbol", "")
                if not symbol_str:
                    continue
                
                available = Decimal(str(balance_item.get("available", "0")))
                in_order = Decimal(str(balance_item.get("inOrder", "0")))
                total_amount = available + in_order
                
                if total_amount > 0:
                    # Skip EUR as it's the base currency, not a tradeable asset
                    if symbol_str.upper() == "EUR":
                        continue

                    # Validate symbol before creating AssetSymbol
                    if len(symbol_str) < 2 or len(symbol_str) > 10:
                        logger.warning(f"Skipping invalid asset symbol '{symbol_str}': length {len(symbol_str)} (must be 2-10 characters)")
                        continue

                    asset_symbol = AssetSymbol(symbol_str)
                    asset_amount = AssetAmount(total_amount, asset_symbol)
                    balances[asset_symbol] = asset_amount
                    
            except Exception as e:
                logger.warning(f"Skipping invalid balance data: {e}")
                continue
        
        return balances
    
    @staticmethod
    def map_ticker_data_to_price(ticker_data: Dict[str, Any]) -> Money:
        """
        Map Bitvavo ticker data to Money price.
        
        Args:
            ticker_data: Raw ticker data from Bitvavo API
            
        Returns:
            Money object representing the price
            
        Raises:
            ValueError: If ticker data is invalid
        """
        try:
            price_str = ticker_data.get("price", "0")
            price = Decimal(str(price_str))
            
            if price <= 0:
                raise ValueError(f"Invalid ticker price: {price}")
            
            return Money(price, "EUR")
            
        except Exception as e:
            logger.error(f"Failed to map ticker data to price: {e}")
            logger.error(f"Ticker data: {ticker_data}")
            raise ValueError(f"Invalid ticker data: {e}") from e
    
    @staticmethod
    def extract_asset_symbols_from_trades(trades_data: List[Dict[str, Any]]) -> List[AssetSymbol]:
        """
        Extract unique asset symbols from trade data.
        
        Args:
            trades_data: List of raw trade data from Bitvavo API
            
        Returns:
            List of unique asset symbols
        """
        symbols = set()
        
        for trade_data in trades_data:
            try:
                market = trade_data.get("market", "")
                if "-EUR" in market:
                    asset_symbol_str = market.replace("-EUR", "")
                    symbols.add(AssetSymbol(asset_symbol_str))
            except Exception as e:
                logger.warning(f"Could not extract symbol from trade data: {e}")
                continue
        
        return list(symbols)
    
    @staticmethod
    def map_deposit_withdrawal_data(deposit_data: List[Dict[str, Any]], 
                                   withdrawal_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Map deposit and withdrawal data to transfer summaries.
        
        Args:
            deposit_data: Raw deposit data from Bitvavo API
            withdrawal_data: Raw withdrawal data from Bitvavo API
            
        Returns:
            Dictionary with transfer summary data by asset
        """
        transfer_summaries = {}
        
        # Process deposits
        for deposit in deposit_data:
            try:
                symbol = deposit.get("symbol", "")
                amount = Decimal(str(deposit.get("amount", "0")))
                
                if symbol and amount > 0:
                    if symbol not in transfer_summaries:
                        transfer_summaries[symbol] = {
                            "total_deposits": Decimal("0"),
                            "total_withdrawals": Decimal("0"),
                            "deposit_count": 0,
                            "withdrawal_count": 0,
                        }
                    
                    transfer_summaries[symbol]["total_deposits"] += amount
                    transfer_summaries[symbol]["deposit_count"] += 1
                    
            except Exception as e:
                logger.warning(f"Skipping invalid deposit data: {e}")
                continue
        
        # Process withdrawals
        for withdrawal in withdrawal_data:
            try:
                symbol = withdrawal.get("symbol", "")
                amount = Decimal(str(withdrawal.get("amount", "0")))
                
                if symbol and amount > 0:
                    if symbol not in transfer_summaries:
                        transfer_summaries[symbol] = {
                            "total_deposits": Decimal("0"),
                            "total_withdrawals": Decimal("0"),
                            "deposit_count": 0,
                            "withdrawal_count": 0,
                        }
                    
                    transfer_summaries[symbol]["total_withdrawals"] += amount
                    transfer_summaries[symbol]["withdrawal_count"] += 1
                    
            except Exception as e:
                logger.warning(f"Skipping invalid withdrawal data: {e}")
                continue
        
        # Calculate net transfers
        for symbol, summary in transfer_summaries.items():
            summary["net_transfers"] = summary["total_deposits"] - summary["total_withdrawals"]
        
        return transfer_summaries
