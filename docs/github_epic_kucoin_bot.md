# Epic: Isolated AI-Driven Trading Bot on KuCoin with Memory Layer

## Summary
Develop an isolated trading bot system that operates on KuCoin subaccounts with strict budget controls, memory persistence, and future LLM integration capabilities. The system will start with a single bot and scale to support multiple bots with AI orchestration.

## Background and Research Context

Following extensive research on isolated trading bot architectures for Bitvavo and other exchanges, we concluded Bitvavo does not currently support subaccounts, making proper budget isolation unfeasible. Therefore, KuCoin was selected as the preferred exchange because it supports:
- Multiple subaccounts per main account
- API keys scoped to a specific subaccount
- Internal transfers between sub and main account without blockchain fees
- Trade-only API keys without withdrawal permission

This approach provides fund isolation while allowing scalable multi-bot deployment in the future. The research also identified the following key considerations:

### Research Highlights
- Use Freqtrade for the core trading engine, running inside an ephemeral Docker container per bot
- Trade only on the allocated KuCoin subaccount budget, never exceeding funds
- LLM orchestration (optional in later phases) for strategy suggestion, implemented with function calling and strict rate-limiting to control API costs
- Memory layer required for each bot to track trade history, PnL, fee awareness, and learning over time
- Memory options considered: Redis (namespaced per bot), SQLite, or DuckDB. Redis preferred for simplicity and scalability
- Risk management module needed to enforce stop-loss, max exposure, and prevent drawdown beyond allocated budget
- Logs and monitoring for auditable actions, errors, and analysis

We aim to start small, with a single bot trading on a KuCoin subaccount with a small budget (~€50–100), no LLM at first, but architected to scale to LLM integration and multiple bots later.

## Goals
- Deploy an isolated trading bot that only operates within the allocated KuCoin subaccount budget
- Architect the system for future scalability with multiple bots and optional LLM integration
- Include a per-bot memory layer for persistence and learning
- Ensure secure API key usage and no risk to main account funds
- Implement logging, monitoring, and guardrails for safe operation

## Deliverables
- Docker-based deployment scripts and configuration for a single bot
- Redis memory layer implementation with per-bot namespaces
- Risk management and logging modules
- Documentation of the system, phases, and operational procedures
- Optional LLM integration plan for later phases

## Phases
1. **MVP**: Single KuCoin subaccount bot, running on Freqtrade in Docker, no LLM yet. Fixed budget, risk-managed, logs actions, uses trade-only API key.
2. **Memory Layer**: Add Redis memory for the bot to persist trade history, fees, PnL, and insights. Namespaced memory to allow multiple bots later.
3. **LLM Orchestrator**: Add LLM function-calling for strategy suggestions. Implement rate limiting and budget guardrails for LLM API usage.
4. **Multi-Bot Architecture**: Multiple bots running in parallel, each on their own subaccount and container. Central monitoring and orchestration.
5. **Continuous Improvement**: CI/CD pipeline for bot builds, fallback strategies for LLM unavailability, and advanced risk controls.

## Success Criteria
- Bot operates without exceeding allocated budget
- Funds in main account remain untouched and secure
- Memory layer persists relevant data across runs
- Logs and monitors actions and performance
- LLM integration costs stay within predefined limits

---

# User Stories

## Phase 1: MVP - Basic Trading Bot

### Story 1: Isolated KuCoin Subaccount Trading
**As a** crypto trader  
**I want** a trading bot that operates only within a designated KuCoin subaccount with a fixed budget  
**So that** I can automate trading without risking my main account funds

**Acceptance Criteria:**
- [ ] Bot connects to KuCoin API using trade-only API key scoped to subaccount
- [ ] Bot never exceeds the allocated budget (€50-100)
- [ ] Bot cannot access or transfer funds from main account
- [ ] Bot logs all trading actions and decisions
- [ ] Bot implements basic risk management (stop-loss, max exposure)

### Story 2: Docker-Based Bot Deployment
**As a** system administrator  
**I want** the trading bot to run in an isolated Docker container  
**So that** I can ensure consistent deployment and easy scaling

**Acceptance Criteria:**
- [ ] Freqtrade runs inside Docker container
- [ ] Container is ephemeral and can be easily restarted
- [ ] Configuration is externalized and version-controlled
- [ ] Container logs are accessible for monitoring
- [ ] Deployment scripts are documented and automated

## Phase 2: Memory Layer

### Story 3: Persistent Bot Memory with Redis
**As a** trading bot  
**I want** to persist my trade history, PnL, and insights in a Redis memory layer  
**So that** I can learn from past trades and maintain state across restarts

**Acceptance Criteria:**
- [ ] Redis instance is configured with per-bot namespaces
- [ ] Bot stores trade history, fees, and PnL data
- [ ] Memory data survives bot restarts
- [ ] Memory layer supports multiple bots (future-proofing)
- [ ] Data retention policies are implemented

### Story 4: Trade History Analysis
**As a** crypto trader  
**I want** the bot to analyze its historical performance using stored memory data  
**So that** I can understand the bot's effectiveness and make informed decisions

**Acceptance Criteria:**
- [ ] Bot calculates cumulative PnL from memory
- [ ] Bot tracks win/loss ratios and trade statistics
- [ ] Bot identifies patterns in successful vs unsuccessful trades
- [ ] Performance metrics are logged and accessible
- [ ] Memory data is used to inform future trading decisions

## Phase 3: LLM Orchestrator

### Story 5: AI-Powered Strategy Suggestions
**As a** crypto trader  
**I want** the bot to use LLM function calling to suggest trading strategies  
**So that** I can benefit from AI analysis while maintaining strict cost controls

**Acceptance Criteria:**
- [ ] LLM integration uses function calling for strategy suggestions
- [ ] Rate limiting prevents excessive API usage
- [ ] LLM API costs are tracked and stay within budget
- [ ] Bot can operate without LLM if service is unavailable
- [ ] LLM suggestions are logged for audit purposes

### Story 6: Budget-Controlled AI Integration
**As a** system administrator  
**I want** strict guardrails on LLM API usage and costs  
**So that** AI features don't exceed predefined spending limits

**Acceptance Criteria:**
- [ ] Daily/monthly LLM API cost limits are enforced
- [ ] Rate limiting prevents API abuse
- [ ] Fallback strategies work when LLM is unavailable
- [ ] Cost tracking and alerts are implemented
- [ ] LLM usage statistics are monitored and reported

## Phase 4: Multi-Bot Architecture

### Story 7: Parallel Multi-Bot Operation
**As a** crypto trader  
**I want** to run multiple trading bots simultaneously on different subaccounts  
**So that** I can diversify strategies and scale my trading operations

**Acceptance Criteria:**
- [ ] Each bot runs in its own Docker container
- [ ] Each bot operates on a separate KuCoin subaccount
- [ ] Bots operate independently without interference
- [ ] Central monitoring dashboard shows all bot statuses
- [ ] Resource allocation prevents bots from competing for system resources

### Story 8: Centralized Monitoring and Orchestration
**As a** system administrator  
**I want** a central monitoring system for all trading bots  
**So that** I can oversee operations and quickly identify issues

**Acceptance Criteria:**
- [ ] Dashboard shows status of all running bots
- [ ] Centralized logging aggregates all bot activities
- [ ] Alerts notify of bot failures or anomalies
- [ ] Performance metrics are compared across bots
- [ ] Central orchestration can start/stop individual bots

## Phase 5: Continuous Improvement

### Story 9: CI/CD Pipeline for Bot Deployment
**As a** developer  
**I want** an automated CI/CD pipeline for bot builds and deployments  
**So that** I can safely update bot strategies and configurations

**Acceptance Criteria:**
- [ ] Automated testing of bot configurations
- [ ] Staged deployment with rollback capabilities
- [ ] Version control for bot strategies and configurations
- [ ] Automated security scanning of Docker images
- [ ] Blue-green deployment for zero-downtime updates

### Story 10: Advanced Risk Controls and Monitoring
**As a** crypto trader  
**I want** advanced risk management and monitoring capabilities  
**So that** I can protect my investments and optimize bot performance

**Acceptance Criteria:**
- [ ] Advanced stop-loss and drawdown protection
- [ ] Market volatility detection and response
- [ ] Automated bot shutdown on critical errors
- [ ] Performance benchmarking against market indices
- [ ] Comprehensive audit trail for all bot actions
