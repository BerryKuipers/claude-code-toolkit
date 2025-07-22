# Contributing to Crypto Portfolio Dashboard

Thank you for your interest in contributing to the Crypto Portfolio Dashboard! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- Git
- Bitvavo account with API access (for testing)

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/BerryKuipers/crypto-portfolio-dashboard.git
   cd crypto-portfolio-dashboard
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e .  # Install in development mode
   ```

4. **Set Up Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your Bitvavo API credentials
   ```

5. **Run Tests**
   ```bash
   pytest tests/
   ```

## 🛠️ Development Guidelines

### Code Style
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for all public functions
- Keep functions focused and small
- Use meaningful variable names

### Testing
- Write tests for all new functionality
- Maintain test coverage above 80%
- Use pytest for testing framework
- Mock external API calls in tests
- Test both success and error cases

### Documentation
- Update README.md for new features
- Add docstrings to all functions
- Update CHANGELOG.md for releases
- Include usage examples

## 📝 Pull Request Process

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write code following style guidelines
   - Add tests for new functionality
   - Update documentation as needed

3. **Test Your Changes**
   ```bash
   pytest tests/
   python -m streamlit run dashboard.py  # Test dashboard
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a pull request on GitHub.

## 🐛 Bug Reports

When reporting bugs, please include:
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages (if any)
- Relevant log files

## 💡 Feature Requests

For feature requests, please provide:
- Clear description of the feature
- Use case and motivation
- Proposed implementation (if any)
- Potential impact on existing functionality

## 🏗️ Architecture Overview

### Core Components
- `src/portfolio/core.py`: FIFO calculations and API interactions
- `src/portfolio/cli.py`: Command-line interface
- `src/portfolio/ui.py`: Streamlit dashboard components
- `dashboard.py`: Main dashboard application

### Key Design Principles
- **Separation of Concerns**: Clear boundaries between components
- **Decimal Precision**: All financial calculations use Decimal type
- **Error Handling**: Graceful handling of API failures
- **Extensibility**: Easy to add new exchanges or features

## 🔒 Security Considerations

- Never commit API keys or secrets
- Use environment variables for configuration
- Validate all user inputs
- Handle API rate limits properly
- Follow secure coding practices

## 📊 Performance Guidelines

- Use efficient data structures
- Implement proper caching where appropriate
- Minimize API calls through batching
- Profile code for bottlenecks
- Consider memory usage for large datasets

## 🤝 Community

- Be respectful and inclusive
- Help others learn and grow
- Share knowledge and best practices
- Provide constructive feedback
- Follow the code of conduct

## 📞 Getting Help

- Check existing issues and documentation
- Ask questions in GitHub discussions
- Join our community chat (if available)
- Contact maintainers for urgent issues

Thank you for contributing to make this project better! 🎉
