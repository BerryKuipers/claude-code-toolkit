# Epic: Isolated AI-Driven Trading Bot on KuCoin with Memory Layer

## Background and Research Context

Following extensive research on isolated trading bot architectures for Bitvavo and other exchanges, we concluded Bitvavo does not currently support subaccounts, making proper budget isolation unfeasible. Therefore, KuCoin was selected as the preferred exchange because it supports:
- Multiple subaccounts per main account
- API keys scoped to a specific subaccount
- Internal transfers between sub and main account without blockchain fees
- Trade-only API keys without withdrawal permission

This approach provides fund isolation while allowing scalable multi-bot deployment in the future. The research also identified the following key considerations:

### Research Highlights
- Use Freqtrade for the core trading engine, running inside an ephemeral Docker container per bot.
- Trade only on the allocated KuCoin subaccount budget, never exceeding funds.
- LLM orchestration (optional in later phases) for strategy suggestion, implemented with function calling and strict rate-limiting to control API costs.
- Memory layer required for each bot to track trade history, PnL, fee awareness, and learning over time.
- Memory options considered: Redis (namespaced per bot), SQLite, or DuckDB. Redis preferred for simplicity and scalability.
- Risk management module needed to enforce stop-loss, max exposure, and prevent drawdown beyond allocated budget.
- Logs and monitoring for auditable actions, errors, and analysis.

We aim to start small, with a single bot trading on a KuCoin subaccount with a small budget (~€50–100), no LLM at first, but architected to scale to LLM integration and multiple bots later.

## Goals
- Deploy an isolated trading bot that only operates within the allocated KuCoin subaccount budget.
- Architect the system for future scalability with multiple bots and optional LLM integration.
- Include a per-bot memory layer for persistence and learning.
- Ensure secure API key usage and no risk to main account funds.
- Implement logging, monitoring, and guardrails for safe operation.

## Deliverables
- Docker-based deployment scripts and configuration for a single bot.
- Redis memory layer implementation with per-bot namespaces.
- Risk management and logging modules.
- Documentation of the system, phases, and operational procedures.
- Optional LLM integration plan for later phases.

## Phases
1️⃣ MVP:  
- Single KuCoin subaccount bot, running on Freqtrade in Docker, no LLM yet.  
- Fixed budget, risk-managed, logs actions, uses trade-only API key.

2️⃣ Memory Layer:  
- Add Redis memory for the bot to persist trade history, fees, PnL, and insights.  
- Namespaced memory to allow multiple bots later.

3️⃣ LLM Orchestrator:  
- Add LLM function-calling for strategy suggestions.  
- Implement rate limiting and budget guardrails for LLM API usage.

4️⃣ Multi-Bot Architecture:  
- Multiple bots running in parallel, each on their own subaccount and container.  
- Central monitoring and orchestration.

5️⃣ Continuous Improvement:  
- CI/CD pipeline for bot builds, fallback strategies for LLM unavailability, and advanced risk controls.

## Success Criteria
- Bot operates without exceeding allocated budget.
- Funds in main account remain untouched and secure.
- Memory layer persists relevant data across runs.
- Logs and monitors actions and performance.
- LLM integration costs stay within predefined limits.

