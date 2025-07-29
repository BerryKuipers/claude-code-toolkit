I need to separate my crypto portfolio dashboard into a strongly typed API backend + frontend architecture. Coming from a C# background, I want comprehensive type safety throughout the codebase.

**Context:**
- Current issue: Monolithic Streamlit app where every change requires new Bitvavo API calls (major development overhead)
- Goal: FastAPI backend with Pydantic models + Streamlit frontend with typed API client
- Strong typing requirement: Full type annotations, runtime validation, interfaces like C#

**GitHub Issue:** #41 - https://github.com/BerryKuipers/crypto-insight/issues/41

**Current Status:**
- ✅ PR #37 (tab navigation) merged to main
- ✅ All existing functionality working in monolithic architecture
- ✅ Ready to start API separation with strong typing

**What I need:**

1. **Strongly Typed Backend (FastAPI + Pydantic)**:
   - Comprehensive Pydantic models (like C# DTOs) for all data structures
   - Strongly typed controllers with full type annotations
   - Service layer with interfaces (using Protocol/ABC like C# interfaces)
   - Typed configuration with Pydantic Settings
   - Full mypy/pyright type checking

2. **Key Requirements**:
   - **FAST DEVELOPMENT**: Backend caches data, frontend changes don't trigger API calls
   - **TYPE SAFETY**: 100% type coverage, runtime validation, IntelliSense
   - **C# Developer Experience**: Interfaces, DTOs, dependency injection patterns
   - **Auto-generated docs**: OpenAPI documentation from types

3. **Architecture**:
Backend (Port 8000): FastAPI + Pydantic + Redis caching
Frontend (Port 8501): Streamlit + Typed API client

4. **File Structure**:`
backend/app/
├── models/ # Pydantic models (DTOs)
├── api/v1/ # Controllers
├── services/ # Business logic with interfaces
├── core/ # Config & DI
└── clients/ # External API clients

frontend/
├── dashboard.py # Streamlit app
├── clients/ # Typed backend API client
└── components/ # UI components

**Expected Benefits:**
- ⚡ 10x faster development (no repeated API calls)
- 🔒 Compile-time-like safety with runtime validation  
- 🧠 Better AI-assisted development (strongly typed = fewer mistakes)
- 📚 Auto-generated API documentation
- 🔄 Independent backend/frontend development

**Repository:** https://github.com/BerryKuipers/crypto-insight
**Branch:** Create new branch from `development`

Please help me implement this strongly typed API separation to get that familiar C# development experience with Python, while solving the slow development cycle caused by repeated Bitvavo API calls.