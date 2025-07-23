# Crypto Insight Development Guide

**Project Root**: `D:\berry\Projects\crypto_insight`  
**Repository**: https://github.com/BerryKuipers/crypto-insight

## 🚀 Quick Start

**Use available tools directly** for all operations: `view`, `str-replace-editor`, `save-file`, `launch-process`, `github-api`, etc.

### Development Environment
- **Python Environment**: `.venv` (always activate before running)
- **Main Application**: `streamlit run dashboard.py`
- **Dashboard URL**: `http://localhost:8501`
- **Testing**: `python -m pytest tests/ -v`

### Architecture
- **Frontend**: Streamlit dashboard with interactive portfolio analysis
- **Backend**: Python with Bitvavo API integration
- **AI Integration**: OpenAI GPT-4 + Anthropic Claude for chat and analysis
- **Data**: Real-time crypto portfolio data from Bitvavo exchange

## 🛡️ Safety & Quality Rules

### Critical Safety Checks
- Always use `.venv` virtual environment
- Verify git branch/status after every git operation
- Confirm commits actually happened before proceeding
- Check file existence before assuming operations succeeded
- Never expose API keys in code or logs

### Quality Standards
- **No shortcuts**: Never use fake data, stubs, or placeholder code
- **Genuine fixes only**: Always resolve underlying problems
- **Test coverage**: Write unit tests for complex logic
- **Security first**: Protect API keys and user data
- **Performance**: Optimize for real-time portfolio updates

## 🔧 Development Workflow

### Pre-Action Quality Checks
1. **Virtual Environment**: Always ensure `.venv` is activated
   ```bash
   .venv\Scripts\activate  # Windows
   ```
2. **Dependencies**: Check if all required packages are installed
   ```bash
   pip install -r requirements.txt
   ```
3. **API Keys**: Verify environment variables are set correctly
   ```bash
   python scripts/test-api-keys.py  # If available
   ```

### Testing Framework
- **Unit Tests**: Use `pytest` for comprehensive testing
- **Test Structure**: Organize tests by functionality (portfolio, chat, UI)
- **Coverage**: Aim for high test coverage on critical business logic
- **Real-world Scenarios**: Test with actual portfolio data patterns

### Key Testing Areas
- **Profit Indicators**: Complex scenarios with withdrawals, tiny positions
- **API Integration**: Bitvavo data fetching and processing
- **AI Chat**: Function calling and response generation
- **Cost Tracking**: API usage and cost calculation
- **Portfolio Calculations**: FIFO accounting, P&L calculations

## 📋 PR Review Workflow

**Command**: Use GitHub tools to manage PRs
**Repository**: https://github.com/BerryKuipers/crypto-insight

### Core Process

1. **Fetch PR Details** (GitHub API)
   - Get all comments and suggestions
   - Check for AI-generated feedback (Gemini, etc.)

2. **Critical Analysis**
   - Evaluate suggestions for code quality improvement
   - Check compatibility with Streamlit and crypto data
   - Assess security implications for API keys
   - Ensure proper error handling for API failures

3. **Branch Operations**
   ```bash
   git fetch origin <branch-name>
   git checkout <branch-name>
   git status  # Verify branch switch
   ```

4. **Implementation**
   - Apply suggestions via `str-replace-editor`
   - Follow Python best practices
   - Maintain Streamlit app performance
   - Test with real portfolio data

5. **Testing & Validation**
   ```bash
   # Run tests
   python -m pytest tests/ -v
   
   # Test dashboard
   streamlit run dashboard.py
   
   # Verify AI chat functionality
   # Test with different portfolio scenarios
   ```

6. **Commit & Push**
   ```bash
   git add -A
   git status  # Verify files staged
   git commit -m "Apply PR feedback and improvements"
   git push origin <branch-name>
   ```

7. **Resolve Comments**
   - Use `scripts/resolve-pr-conversations.ps1` for automation
   ```powershell
   .\scripts\resolve-pr-conversations.ps1 -PrNumber <num>
   ```

## 🎯 Project Focus Areas

### Core Features ✅
- **Portfolio Dashboard**: Real-time crypto portfolio visualization
- **AI Chat Interface**: Natural language portfolio analysis
- **Profit Indicators**: Accurate P&L calculation with edge cases
- **Multi-Model AI**: OpenAI + Anthropic integration
- **Cost Tracking**: API usage monitoring

### Current Priorities
1. **AI Model Optimization**: Implement Research 03 recommendations
2. **RAG Implementation**: Handle large portfolio histories
3. **Forecasting**: Add time-series prediction capabilities
4. **Performance**: Optimize for large portfolios
5. **Testing**: Expand test coverage for edge cases

### Technical Debt
- **Model Selection**: Implement smart model switching
- **Data Persistence**: Better caching and storage
- **Error Handling**: Robust API failure recovery
- **UI/UX**: Improve navigation and responsiveness

## 🔮 AI Enhancement Roadmap

### Immediate (Current Branch)
- ✅ Fix API cost tracking
- ✅ Enhance profit indicators for tiny positions
- ✅ Add comprehensive unit tests
- ✅ Improve navigation and UX

### Short-term (1-2 weeks)
- 🎯 Optimize model selection (GPT-4o default, Claude for large context)
- 🎯 Implement function calling reliability improvements
- 🎯 Add RAG for large portfolio analysis
- 🎯 Enhance chat interface with streaming

### Medium-term (1-2 months)
- 📈 Time-series forecasting (StatsForecast, Prophet)
- 💾 PostgreSQL migration for better data handling
- 🔍 Advanced portfolio analytics
- ⚡ Performance optimizations

### Long-term (3-6 months)
- 🤖 Advanced ML forecasting models (TFT, TimeGPT)
- 📊 Professional-grade visualizations
- 🔄 Real-time data streaming
- 🎨 Enhanced UI/UX design

## 📊 Success Metrics

### Performance Targets
- **Response Time**: <2s for simple queries, <10s for complex analysis
- **Cost Efficiency**: 40-60% reduction through smart model selection
- **Accuracy**: 95%+ for portfolio calculations
- **Reliability**: Handle API failures gracefully

### User Experience
- **Intuitive Navigation**: Smooth scrolling, clear indicators
- **Accurate Data**: Proper handling of tiny positions and edge cases
- **Helpful AI**: Natural language explanations of portfolio data
- **Cost Transparency**: Clear API usage tracking

## 🛠️ Common Commands

### Development
```bash
# Start development
.venv\Scripts\activate
streamlit run dashboard.py

# Run tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_profit_indicators.py -v

# Check code quality
flake8 src/ --count --select=E9,F63,F7,F82
```

### Git Workflow
```bash
# Create feature branch
git checkout development
git pull origin development
git checkout -b feature/description

# Commit changes
git add -A
git commit -m "feat: description of changes"
git push origin feature/description
```

### PR Management
```powershell
# Resolve PR conversations
.\scripts\resolve-pr-conversations.ps1 -PrNumber 3

# Dry run first
.\scripts\resolve-pr-conversations.ps1 -PrNumber 3 -DryRun
```

## 🔐 Security Guidelines

### API Key Management
- Store keys in `.env` file (never commit)
- Use environment variables in code
- Rotate keys regularly
- Monitor usage and costs

### Data Protection
- Never log sensitive portfolio data
- Sanitize user inputs
- Validate API responses
- Handle errors gracefully

## 📚 Key Files & Directories

```
crypto_insight/
├── dashboard.py              # Main Streamlit application
├── src/portfolio/           # Core portfolio logic
│   ├── chat/               # AI chat interface
│   ├── ui/                 # UI components
│   └── data/               # Data processing
├── tests/                  # Test suite
├── scripts/                # Utility scripts
├── .env                    # Environment variables (not committed)
├── requirements.txt        # Python dependencies
└── prompt.md              # This file
```

## 🎯 Quality Gates

### Before Commit
- [ ] All tests pass
- [ ] Dashboard loads without errors
- [ ] AI chat responds correctly
- [ ] Cost tracking works
- [ ] No API keys in code

### Before PR
- [ ] Feature works end-to-end
- [ ] Edge cases tested
- [ ] Documentation updated
- [ ] Performance acceptable
- [ ] Security reviewed

---

**READY** – Await commands for development, testing, or PR management
