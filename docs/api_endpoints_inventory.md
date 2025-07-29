# Backend API Endpoints Inventory

## Overview
Complete inventory of all FastAPI backend endpoints with functionality, AI usage, and dependencies.

## Core Application Endpoints

### Root & Health Endpoints
| Method | Path | AI Usage | Description |
|--------|------|----------|-------------|
| GET | `/` | ❌ | Root endpoint with API information |
| GET | `/health` | ❌ | Health check for monitoring and load balancers |

## Portfolio Endpoints (`/api/v1/portfolio`)

| Method | Path | AI Usage | Description | Dependencies |
|--------|------|----------|-------------|--------------|
| GET | `/summary` | ❌ | Get comprehensive portfolio summary with total value, P&L, and key metrics | Bitvavo API, Clean Architecture |
| GET | `/holdings` | ❌ | Get complete portfolio data including holdings and summary | Bitvavo API, Clean Architecture |
| GET | `/holdings/complete` | ❌ | Get detailed portfolio holdings with complete asset information | Bitvavo API, Clean Architecture |
| GET | `/performance/{asset}` | ❌ | Get detailed performance analysis for specific asset | Bitvavo API, Clean Architecture |
| GET | `/transactions` | ❌ | Get transaction history with optional asset filtering | Bitvavo API, Clean Architecture |
| GET | `/reconciliation` | ❌ | Perform portfolio reconciliation analysis comparing FIFO vs actual balances | Bitvavo API, Clean Architecture |
| POST | `/refresh` | ❌ | Force refresh of portfolio data from exchange | Bitvavo API, Clean Architecture |

## Market Endpoints (`/api/v1/market`)

| Method | Path | AI Usage | Description | Dependencies |
|--------|------|----------|-------------|--------------|
| GET | `/data` | ❌ | Get comprehensive market data including prices, trends, and sentiment | Bitvavo API, Market Data Providers |
| GET | `/prices` | ❌ | Get current market prices for all or specific assets | Bitvavo API |
| GET | `/prices/{asset}` | ❌ | Get current price for specific asset | Bitvavo API |
| GET | `/opportunities` | ❌ | Get market opportunities and trading signals | Bitvavo API, Market Analysis |
| GET | `/analysis/{asset}` | ❌ | Get technical analysis for specific asset | Bitvavo API, Technical Analysis |
| POST | `/refresh` | ❌ | Force refresh of market data from external sources | Market Data Providers |

## Chat Endpoints (`/api/v1/chat`) - AI-Powered

| Method | Path | AI Usage | Description | Dependencies |
|--------|------|----------|-------------|--------------|
| POST | `/query` | ✅ | Process chat query with AI function calling support | OpenAI/Anthropic APIs, Portfolio/Market Services |
| GET | `/functions` | ❌ | Get list of all available functions for AI function calling | Internal Function Registry |
| GET | `/functions/{function_name}` | ❌ | Get specific function definition for AI | Internal Function Registry |
| POST | `/conversations` | ❌ | Create new conversation for chat history | Internal Storage |
| GET | `/conversations/{conversation_id}` | ❌ | Get chat history for specific conversation | Internal Storage |
| DELETE | `/conversations/{conversation_id}` | ❌ | Delete conversation and its history | Internal Storage |

## API Features Summary

### Non-AI Features (Pure Data)
- **Portfolio Management**: 7 endpoints for portfolio data, calculations, and reconciliation
- **Market Data**: 6 endpoints for real-time market information and analysis
- **System Health**: 2 endpoints for monitoring and API information

### AI-Powered Features
- **Chat Interface**: 1 primary endpoint (`/chat/query`) with full LLM integration
- **Function Calling**: AI can call any portfolio/market endpoint through function calling
- **Multi-Model Support**: OpenAI GPT-4o, Claude Sonnet 4, etc.
- **Cost Tracking**: Token usage and API cost monitoring

### Architecture Patterns
- **Clean Architecture**: All endpoints use dependency injection and service layers
- **Type Safety**: Full Pydantic model validation for all requests/responses
- **Error Handling**: Comprehensive exception handling with proper HTTP status codes
- **Documentation**: Auto-generated OpenAPI/Swagger documentation

### External Dependencies
- **Bitvavo API**: Primary data source for portfolio and market data
- **OpenAI API**: GPT-4o and other OpenAI models for chat
- **Anthropic API**: Claude models for chat
- **Market Data Providers**: Additional market data sources

### Performance Features
- **Async Operations**: All endpoints are async for high performance
- **Caching**: Intelligent caching for frequently accessed data
- **Parallel Processing**: Concurrent API calls where possible
- **Request Timing**: Middleware tracks processing time for all requests

## Total Endpoint Count
- **Portfolio**: 7 endpoints
- **Market**: 6 endpoints  
- **Chat**: 6 endpoints
- **System**: 2 endpoints
- **Total**: 21 endpoints

## AI Integration Summary
- **AI-Powered Endpoints**: 1 direct endpoint (`/chat/query`)
- **AI-Accessible Endpoints**: All 13 portfolio/market endpoints via function calling
- **Non-AI Endpoints**: 7 endpoints (system, function definitions, conversation management)
