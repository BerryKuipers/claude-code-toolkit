# Crypto Portfolio FIFO P&L Analysis Tool

A comprehensive cryptocurrency portfolio analysis tool that calculates profit and loss using FIFO (First-In-First-Out) accounting with high-precision Decimal arithmetic. Features both CLI and web-based interfaces for analyzing your Bitvavo trading history.

## 🚀 Features

- **FIFO Accounting**: Accurate P&L calculation using First-In-First-Out methodology
- **High Precision**: Uses Python's Decimal class to avoid floating-point errors
- **Bitvavo Integration**: Fetches complete trade history and live prices
- **CLI Interface**: Command-line tool with Typer for terminal users
- **Web Dashboard**: Interactive Streamlit interface with real-time filtering
- **What-If Scenarios**: Override prices to simulate different market conditions
- **Comprehensive Testing**: Full test suite with pytest and mocking

## 📁 Project Structure

```
crypto_insight/
│
├── src/
│   └── portfolio/
│       ├── __init__.py      # Package initialization
│       ├── core.py          # Core FIFO logic and API integration
│       ├── cli.py           # Typer CLI interface
│       └── ui.py            # Streamlit dashboard
│
├── tests/
│   ├── test_core.py         # Core logic tests
│   └── test_cli.py          # CLI interface tests
│
├── docs/
│   └── LLM Python Crypto Script.pdf
│
├── requirements.txt         # Python dependencies
├── README.md               # This file
└── .env                    # API credentials (create this)
```

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd crypto_insight
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file in the project root:
   ```env
   BITVAVO_API_KEY=your_api_key_here
   BITVAVO_API_SECRET=your_api_secret_here
   ```

   Get your API credentials from [Bitvavo API settings](https://account.bitvavo.com/api).

## 💻 CLI Usage

The CLI provides three main commands:

### Generate P&L Report

```bash
# Full portfolio report with live prices
python -m src.portfolio.cli report

# Filter specific assets
python -m src.portfolio.cli report --assets BTC,ETH,ADA

# Override prices for what-if scenarios
python -m src.portfolio.cli report --assets BTC --override BTC=35000

# Combine filtering and overrides
python -m src.portfolio.cli report --assets BTC,ETH --override BTC=35000,ETH=1800
```

### What-If Scenarios

```bash
# Single asset what-if
python -m src.portfolio.cli whatif BTC=35000

# What-if with multiple assets
python -m src.portfolio.cli whatif BTC=35000 --assets BTC,ETH
```

### Sync Balances (Future Feature)

```bash
python -m src.portfolio.cli sync-balances
```

## 🌐 Web Dashboard

Launch the interactive Streamlit dashboard:

```bash
streamlit run src/portfolio/ui.py
```

The dashboard provides:

- **Asset Selection**: Multi-select dropdown for choosing assets to analyze
- **Price Overrides**: Input fields for what-if price scenarios
- **Portfolio Table**: Detailed P&L breakdown with formatting
- **Summary Metrics**: Total portfolio value, costs, and returns
- **Visualizations**: Bar charts showing realized vs unrealized P&L
- **Real-time Updates**: Data refreshes every 5 minutes with manual refresh option

## 🧪 Testing

Run the complete test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/portfolio

# Run specific test files
pytest tests/test_core.py
pytest tests/test_cli.py

# Run with verbose output
pytest -v
```

### Test Structure

- **`tests/test_core.py`**: Tests for FIFO calculation logic, API helpers, and data structures
- **`tests/test_cli.py`**: Tests for CLI commands, argument parsing, and error handling

## 📊 Understanding the Output

### P&L Table Columns

- **Asset**: Cryptocurrency symbol (BTC, ETH, etc.)
- **Amount**: Current holdings in crypto units
- **Cost €**: Total cost basis including fees
- **Value €**: Current market value
- **Realised €**: Profit/loss from completed sales
- **Unrealised €**: Profit/loss on current holdings
- **PnL %**: Total return percentage

### Key Metrics

- **Total Return %**: Overall portfolio performance
- **Realised P&L**: Actual profits/losses from sales
- **Unrealised P&L**: Paper profits/losses on holdings

## 🔧 Configuration

### Environment Variables

- `BITVAVO_API_KEY`: Your Bitvavo API key
- `BITVAVO_API_SECRET`: Your Bitvavo API secret

### API Rate Limiting

The tool automatically handles Bitvavo's rate limits:
- Monitors remaining API weight
- Sleeps when approaching limits
- Implements defensive back-off strategies

## 🚨 Important Notes

### FIFO Accounting

This tool uses strict FIFO (First-In-First-Out) accounting:
- Oldest purchases are sold first
- Maintains accurate cost basis tracking
- Complies with most tax jurisdictions

### Precision

- Uses Python's `Decimal` class for all calculations
- Avoids floating-point rounding errors
- Maintains precision for tax reporting

### API Dependencies

- Requires `bitvavo>=1.4.3` (not `python-bitvavo-api`)
- Needs valid API credentials with trading history access
- Respects Bitvavo's rate limits and terms of service

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This tool is for informational purposes only. Always consult with a tax professional for official tax reporting. The authors are not responsible for any financial decisions made based on this tool's output.
