#!/usr/bin/env python3
"""
AI Orchestrator Agent - Routes queries to appropriate specialized agents/functions.
Determines the optimal workflow based on user intent and coordinates multiple agents.
"""

import json
import logging
from enum import Enum
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class QueryIntent(Enum):
    """Different types of user query intents."""

    INVESTMENT_RECOMMENDATION = "investment_recommendation"
    PORTFOLIO_ANALYSIS = "portfolio_analysis"
    MARKET_RESEARCH = "market_research"
    RISK_ASSESSMENT = "risk_assessment"
    PERFORMANCE_REVIEW = "performance_review"
    TECHNICAL_ANALYSIS = "technical_analysis"
    NEWS_RESEARCH = "news_research"
    GENERAL_QUESTION = "general_question"


class AgentType(Enum):
    """Different specialized agents available."""

    PORTFOLIO_ANALYZER = "portfolio_analyzer"
    MARKET_RESEARCHER = "market_researcher"
    RISK_ASSESSOR = "risk_assessor"
    INVESTMENT_ADVISOR = "investment_advisor"
    NEWS_ANALYST = "news_analyst"
    TECHNICAL_ANALYST = "technical_analyst"


class OrchestratorAgent:
    """
    Orchestrator that determines query intent and routes to appropriate agents.
    Coordinates multi-step workflows and combines results intelligently.
    """

    def __init__(self, function_handler, llm_client):
        """Initialize orchestrator with function handler and LLM client."""
        self.function_handler = function_handler
        self.llm_client = llm_client
        self.workflow_history = []

    def analyze_query_intent(self, user_query: str) -> QueryIntent:
        """Analyze user query to determine intent using AI."""
        logger.info(f"🧠 Analyzing query intent: '{user_query[:50]}...'")

        # Investment recommendation keywords
        investment_keywords = [
            "what coin should i buy",
            "new coin",
            "add to portfolio",
            "investment recommendation",
            "what to buy",
            "coin recommendation",
            "should i invest",
            "good investment",
            "buy next",
        ]

        # Portfolio analysis keywords
        portfolio_keywords = [
            "portfolio analysis",
            "how is my portfolio",
            "portfolio performance",
            "my holdings",
            "current portfolio",
            "portfolio summary",
        ]

        # Market research keywords
        market_keywords = [
            "market trends",
            "market analysis",
            "crypto market",
            "market opportunities",
            "trending coins",
            "hot sectors",
            "market outlook",
        ]

        # Risk assessment keywords
        risk_keywords = [
            "risk assessment",
            "portfolio risk",
            "diversification",
            "risk analysis",
            "how risky",
            "risk profile",
            "volatility",
        ]

        query_lower = user_query.lower()

        # Determine intent based on keywords
        if any(keyword in query_lower for keyword in investment_keywords):
            logger.info("🎯 Intent: INVESTMENT_RECOMMENDATION")
            return QueryIntent.INVESTMENT_RECOMMENDATION
        elif any(keyword in query_lower for keyword in portfolio_keywords):
            logger.info("📊 Intent: PORTFOLIO_ANALYSIS")
            return QueryIntent.PORTFOLIO_ANALYSIS
        elif any(keyword in query_lower for keyword in market_keywords):
            logger.info("📈 Intent: MARKET_RESEARCH")
            return QueryIntent.MARKET_RESEARCH
        elif any(keyword in query_lower for keyword in risk_keywords):
            logger.info("⚖️ Intent: RISK_ASSESSMENT")
            return QueryIntent.RISK_ASSESSMENT
        else:
            logger.info("❓ Intent: GENERAL_QUESTION")
            return QueryIntent.GENERAL_QUESTION

    def create_workflow_plan(
        self, intent: QueryIntent, user_query: str
    ) -> List[Dict[str, Any]]:
        """Create a step-by-step workflow plan based on query intent."""
        logger.info(f"📋 Creating workflow plan for intent: {intent.value}")

        if intent == QueryIntent.INVESTMENT_RECOMMENDATION:
            return [
                {
                    "step": 1,
                    "agent": AgentType.PORTFOLIO_ANALYZER,
                    "function": "get_current_holdings",
                    "args": {},
                    "description": "Get current portfolio holdings",
                    "required": True,
                },
                {
                    "step": 2,
                    "agent": AgentType.PORTFOLIO_ANALYZER,
                    "function": "get_portfolio_summary",
                    "args": {},
                    "description": "Analyze portfolio allocation and performance",
                    "required": True,
                },
                {
                    "step": 3,
                    "agent": AgentType.MARKET_RESEARCHER,
                    "function": "analyze_market_opportunities",
                    "args": {"sector": "all", "timeframe": "medium"},
                    "description": "Research current market opportunities",
                    "required": True,
                },
                {
                    "step": 4,
                    "agent": AgentType.NEWS_ANALYST,
                    "function": "search_crypto_news",
                    "args": {"query": "cryptocurrency investment opportunities 2025"},
                    "description": "Get latest market news and trends",
                    "required": True,
                },
                {
                    "step": 5,
                    "agent": AgentType.RISK_ASSESSOR,
                    "function": "get_risk_assessment",
                    "args": {},
                    "description": "Assess portfolio risk and diversification needs",
                    "required": True,
                },
                {
                    "step": 6,
                    "agent": AgentType.INVESTMENT_ADVISOR,
                    "function": "synthesize_recommendation",
                    "args": {"query": user_query},
                    "description": "Synthesize all data into specific coin recommendations",
                    "required": True,
                },
            ]

        elif intent == QueryIntent.PORTFOLIO_ANALYSIS:
            return [
                {
                    "step": 1,
                    "agent": AgentType.PORTFOLIO_ANALYZER,
                    "function": "get_current_holdings",
                    "args": {},
                    "description": "Get current holdings",
                    "required": True,
                },
                {
                    "step": 2,
                    "agent": AgentType.PORTFOLIO_ANALYZER,
                    "function": "get_portfolio_summary",
                    "args": {},
                    "description": "Get portfolio summary and metrics",
                    "required": True,
                },
            ]

        # Add more workflow plans for other intents...
        else:
            return [
                {
                    "step": 1,
                    "agent": AgentType.PORTFOLIO_ANALYZER,
                    "function": "get_portfolio_summary",
                    "args": {},
                    "description": "Get basic portfolio information",
                    "required": False,
                }
            ]

    def execute_workflow(self, workflow_plan: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute the workflow plan step by step."""
        logger.info(f"🚀 Executing workflow with {len(workflow_plan)} steps")

        results = {}

        for step_info in workflow_plan:
            step_num = step_info["step"]
            function_name = step_info["function"]
            args = step_info["args"]
            description = step_info["description"]
            required = step_info["required"]

            logger.info(f"📍 Step {step_num}: {description}")

            try:
                if function_name == "synthesize_recommendation":
                    # Special case: synthesize all previous results
                    result = self._synthesize_investment_recommendation(
                        results, args["query"]
                    )
                else:
                    # Regular function call
                    result = self.function_handler.handle_function_call(
                        function_name, json.dumps(args)
                    )
                    result = json.loads(result) if isinstance(result, str) else result

                results[f"step_{step_num}_{function_name}"] = result
                logger.info(f"✅ Step {step_num} completed successfully")

            except Exception as e:
                logger.error(f"❌ Step {step_num} failed: {str(e)}")
                if required:
                    results[f"step_{step_num}_{function_name}"] = {"error": str(e)}
                else:
                    logger.warning(f"⚠️ Optional step {step_num} failed, continuing...")

        return results

    def _synthesize_investment_recommendation(
        self, workflow_results: Dict[str, Any], user_query: str
    ) -> Dict[str, Any]:
        """Synthesize all workflow results into a final investment recommendation."""
        logger.info("🧠 Synthesizing investment recommendation from all data")

        # Extract key data from workflow results
        holdings = workflow_results.get("step_1_get_current_holdings", {})
        portfolio_summary = workflow_results.get("step_2_get_portfolio_summary", {})
        market_opportunities = workflow_results.get(
            "step_3_analyze_market_opportunities", {}
        )
        news_analysis = workflow_results.get("step_4_search_crypto_news", {})
        risk_assessment = workflow_results.get("step_5_get_risk_assessment", {})

        # Create synthesis prompt for specialized investment advisor agent
        synthesis_prompt = f"""
        Based on comprehensive portfolio analysis, provide specific cryptocurrency investment recommendations.
        
        USER QUERY: {user_query}
        
        PORTFOLIO DATA:
        - Current Holdings: {json.dumps(holdings, default=str)[:500]}...
        - Portfolio Summary: {json.dumps(portfolio_summary, default=str)[:500]}...
        - Market Opportunities: {json.dumps(market_opportunities, default=str)[:500]}...
        - Latest News: {json.dumps(news_analysis, default=str)[:300]}...
        - Risk Assessment: {json.dumps(risk_assessment, default=str)[:300]}...
        
        Provide SPECIFIC coin recommendations with:
        1. Exact coin names and symbols
        2. Recommended allocation amounts (€ and %)
        3. Entry strategy (DCA, lump sum, etc.)
        4. Reasoning based on the actual portfolio data
        5. Risk considerations
        6. Timeline expectations
        
        Format as structured JSON with clear recommendations.
        """

        try:
            # Use LLM to synthesize final recommendation
            response = self.llm_client.get_response(synthesis_prompt)

            return {
                "recommendation_type": "investment_advice",
                "synthesis": response,
                "data_sources": list(workflow_results.keys()),
                "confidence": "high" if len(workflow_results) >= 4 else "medium",
            }

        except Exception as e:
            logger.error(f"Failed to synthesize recommendation: {e}")
            return {
                "error": "Failed to synthesize recommendation",
                "raw_data": workflow_results,
            }

    def process_query(self, user_query: str) -> Dict[str, Any]:
        """Main entry point: analyze query, create workflow, execute, and return results."""
        logger.info(f"🎯 Processing query: '{user_query[:100]}...'")

        # Step 1: Analyze query intent
        intent = self.analyze_query_intent(user_query)

        # Step 2: Create workflow plan
        workflow_plan = self.create_workflow_plan(intent, user_query)

        # Step 3: Execute workflow
        workflow_results = self.execute_workflow(workflow_plan)

        # Step 4: Store in history
        self.workflow_history.append(
            {
                "query": user_query,
                "intent": intent.value,
                "workflow_plan": workflow_plan,
                "results": workflow_results,
            }
        )

        logger.info(
            f"🎉 Query processing completed with {len(workflow_results)} results"
        )

        return {
            "intent": intent.value,
            "workflow_executed": len(workflow_plan),
            "results": workflow_results,
            "success": True,
        }
