# Crypto Portfolio Backend API

A strongly typed FastAPI backend for crypto portfolio analysis, providing C#-like development experience with comprehensive type safety and auto-generated documentation.

## 🚀 Features

- **🔒 Full Type Safety**: Comprehensive Pydantic models with runtime validation
- **📚 Auto-Generated Docs**: OpenAPI documentation with type information
- **🏗️ C# Developer Experience**: Interfaces, DTOs, dependency injection patterns
- **⚡ High Performance**: FastAPI with async support and caching
- **🔄 Hot Reload**: Development server with automatic restart on changes
- **🧪 Comprehensive Testing**: Type-safe test fixtures and mocks

## 🏗️ Architecture

```
backend/app/
├── main.py                    # FastAPI application entry point
├── models/                    # Pydantic models (like C# DTOs)
│   ├── portfolio.py           # Portfolio data models
│   ├── market.py              # Market data models
│   ├── chat.py                # AI chat models
│   └── common.py              # Shared models & enums
├── api/v1/                    # Controllers (like C# Controllers)
│   ├── endpoints/
│   │   ├── portfolio.py       # Portfolio endpoints
│   │   ├── market.py          # Market endpoints
│   │   └── chat.py            # Chat endpoints
│   └── api.py                 # API router
├── services/                  # Business logic (like C# Services)
│   ├── interfaces/            # Abstract base classes
│   ├── portfolio_service.py   # Portfolio business logic
│   ├── market_service.py      # Market analysis logic
│   └── chat_service.py        # AI chat logic
├── core/                      # Configuration & DI
│   ├── config.py              # Strongly typed settings
│   ├── dependencies.py        # Dependency injection
│   └── exceptions.py          # Custom exceptions
└── clients/                   # External API clients
    ├── bitvavo_client.py      # Typed Bitvavo client
    └── ai_client.py           # Typed AI client
```

## 🔧 Development Setup

### Prerequisites

- Python 3.9+
- Virtual environment activated
- Environment variables configured

### Environment Variables

Create a `.env` file in the project root:

```env
# Bitvavo API (Required)
BITVAVO_API_KEY=your_bitvavo_api_key
BITVAVO_API_SECRET=your_bitvavo_api_secret

# AI APIs (Optional)
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Backend Configuration (Optional)
DEBUG=true
LOG_LEVEL=INFO
CACHE_TTL_SECONDS=300
```

### Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

2. **Start Development Server**:
   ```bash
   # From project root
   .\scripts\start-backend.ps1
   
   # Or manually
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Access API Documentation**:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
   - OpenAPI JSON: http://localhost:8000/openapi.json

## 📊 API Endpoints

### Portfolio Endpoints

- `GET /api/v1/portfolio/summary` - Portfolio summary with P&L
- `GET /api/v1/portfolio/holdings` - Current holdings list
- `GET /api/v1/portfolio/holdings/complete` - Holdings with summary
- `GET /api/v1/portfolio/performance/{asset}` - Asset performance
- `GET /api/v1/portfolio/transactions` - Transaction history
- `GET /api/v1/portfolio/reconciliation` - Portfolio reconciliation
- `POST /api/v1/portfolio/refresh` - Refresh portfolio data

### Market Endpoints

- `GET /api/v1/market/data` - Comprehensive market data
- `GET /api/v1/market/prices` - Current prices
- `GET /api/v1/market/prices/{asset}` - Specific asset price
- `GET /api/v1/market/opportunities` - Market opportunities
- `GET /api/v1/market/analysis/{asset}` - Technical analysis
- `POST /api/v1/market/refresh` - Refresh market data

### Chat Endpoints

- `POST /api/v1/chat/query` - Process chat query with function calling
- `GET /api/v1/chat/functions` - Available functions
- `GET /api/v1/chat/functions/{function_name}` - Function definition
- `POST /api/v1/chat/conversations` - Create conversation
- `GET /api/v1/chat/conversations/{id}` - Get chat history
- `DELETE /api/v1/chat/conversations/{id}` - Delete conversation

## 🔒 Type Safety

### Pydantic Models (C# DTO-like)

```python
class PortfolioSummaryResponse(BaseResponse):
    total_value: Decimal = Field(..., description="Total portfolio value in EUR")
    total_cost: Decimal = Field(..., description="Total cost basis in EUR")
    realized_pnl: Decimal = Field(..., description="Realized P&L in EUR")
    unrealized_pnl: Decimal = Field(..., description="Unrealized P&L in EUR")
    total_return_percentage: Decimal = Field(..., description="Total return %")
    asset_count: int = Field(..., description="Number of assets held")
    last_updated: datetime = Field(..., description="Last update timestamp")
```

### Service Interfaces (C# Interface-like)

```python
class IPortfolioService(ABC):
    @abstractmethod
    async def get_portfolio_summary(self) -> PortfolioSummaryResponse:
        """Get comprehensive portfolio summary."""
        pass
    
    @abstractmethod
    async def get_current_holdings(self) -> List[HoldingResponse]:
        """Get list of all currently held assets."""
        pass
```

### Dependency Injection (C# DI-like)

```python
@router.get("/summary", response_model=PortfolioSummaryResponse)
async def get_portfolio_summary(
    portfolio_service: PortfolioServiceDep
) -> PortfolioSummaryResponse:
    return await portfolio_service.get_portfolio_summary()
```

## 🧪 Testing

### Run Tests

```bash
# All tests
pytest backend/tests/

# With coverage
pytest backend/tests/ --cov=app --cov-report=html

# Type checking
mypy backend/app --strict
```

### Test Structure

```python
class TestPortfolioAPI:
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    async def test_get_portfolio_summary(self, client):
        response = client.get("/api/v1/portfolio/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_value" in data
        assert "total_return_percentage" in data
```

## 🔧 Type Checking

### MyPy Configuration

The backend uses strict type checking with MyPy:

```bash
# Run type checking
mypy backend/app --strict --ignore-missing-imports

# Check specific file
mypy backend/app/services/portfolio_service.py
```

### IDE Support

For the best C# developer experience:

- **VS Code**: Install Python and Pylance extensions
- **PyCharm**: Enable type checking in settings
- **IntelliSense**: Full autocomplete with type information

## 🚀 Deployment

### Development

```bash
# Start with hot reload
.\scripts\start-backend.ps1

# With type checking
.\scripts\start-backend.ps1 -TypeCheck
```

### Production

```bash
# Production mode
.\scripts\start-backend.ps1 -Production

# Or with uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📈 Performance

- **Async Support**: All endpoints use async/await
- **Response Caching**: Configurable TTL for expensive operations
- **Rate Limiting**: Built-in protection for external APIs
- **Connection Pooling**: Efficient database and API connections

## 🔐 Security

- **Input Validation**: Pydantic models validate all inputs
- **Error Handling**: Structured error responses without sensitive data
- **CORS Configuration**: Properly configured for frontend integration
- **API Key Management**: Secure environment variable handling

## 🤝 Contributing

1. Follow the existing type-safe patterns
2. Add comprehensive type hints to all functions
3. Write tests for new functionality
4. Update API documentation
5. Run type checking before committing

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
- [OpenAPI Specification](https://swagger.io/specification/)
