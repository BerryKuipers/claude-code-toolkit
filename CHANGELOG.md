# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-22

### Added
- **Core FIFO P&L Calculation Engine**
  - First-In-First-Out accounting for crypto trades
  - Precise decimal arithmetic for financial calculations
  - Support for multiple cryptocurrencies
  - Real-time price fetching from Bitvavo API

- **Advanced Transfer Tracking**
  - Deposit and withdrawal history analysis
  - Net transfer calculations per asset
  - Transaction counting and categorization
  - External wallet transfer detection

- **Staking Rewards & Airdrops Detection**
  - Smart pattern recognition for reward identification
  - Heuristic analysis of deposit patterns
  - Conservative estimation algorithms
  - Separation of rewards from trading performance

- **Comprehensive Discrepancy Analysis**
  - Transfer-explained discrepancies
  - Rewards-explained discrepancies
  - Unexplained remainder tracking
  - Explanation percentage calculations

- **Interactive Streamlit Dashboard**
  - Real-time portfolio overview
  - Mobile-responsive design
  - Price override functionality
  - Advanced filtering and sorting

- **Enhanced Visualizations**
  - P&L overview charts
  - Portfolio allocation pie charts
  - Transfer flow analysis
  - Discrepancy breakdown visualizations
  - Performance ranking displays

- **Command Line Interface**
  - Portfolio reporting commands
  - What-if price scenario analysis
  - Balance synchronization tools
  - Typer-based CLI framework

- **Comprehensive Testing Suite**
  - Unit tests for core functionality
  - CLI testing with mock data
  - Integration tests for API calls
  - Pytest-based test framework

- **Professional Documentation**
  - Detailed README with setup instructions
  - API documentation
  - Usage examples and tutorials
  - Troubleshooting guides

### Technical Features
- **Bitvavo API Integration**
  - Complete trade history fetching
  - Real-time price data
  - Deposit/withdrawal history
  - Rate limiting and error handling

- **Data Processing**
  - Decimal precision for financial calculations
  - Efficient FIFO queue implementation
  - Transfer pattern analysis
  - Discrepancy reconciliation

- **User Interface**
  - Streamlit-based web dashboard
  - Interactive charts with Plotly
  - Responsive design for mobile
  - Real-time data updates

- **Architecture**
  - Modular package structure
  - Separation of concerns
  - Extensible design patterns
  - Professional error handling

### Security
- Environment variable configuration
- API key protection
- No hardcoded credentials
- Secure data handling practices

### Performance
- Efficient API rate limiting
- Caching for repeated calculations
- Optimized data structures
- Minimal memory footprint
