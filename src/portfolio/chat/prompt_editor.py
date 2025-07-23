"""Editable system prompts and AI message configuration.

This module provides UI components for editing system prompts, AI personalities,
and message templates with live preview and save functionality.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st

logger = logging.getLogger(__name__)


class PromptEditor:
    """Manages editable system prompts and AI configurations."""

    def __init__(self):
        """Initialize prompt editor."""
        self.default_prompts = self._get_default_prompts()
        self.prompt_categories = {
            "system": "System Prompts",
            "personality": "AI Personality",
            "templates": "Response Templates",
            "functions": "Function Descriptions",
        }

    def render_prompt_editor(self):
        """Render the prompt editor interface."""
        st.subheader("🎭 AI Prompt & Personality Editor")

        # Initialize session state for prompts
        if "custom_prompts" not in st.session_state:
            st.session_state.custom_prompts = self.default_prompts.copy()

        # Tabs for different prompt categories
        tab1, tab2, tab3, tab4 = st.tabs(
            [
                "🤖 System Prompts",
                "🎭 AI Personality",
                "📝 Response Templates",
                "⚙️ Settings",
            ]
        )

        with tab1:
            self._render_system_prompts_editor()

        with tab2:
            self._render_personality_editor()

        with tab3:
            self._render_templates_editor()

        with tab4:
            self._render_settings_editor()

    def _render_system_prompts_editor(self):
        """Render system prompts editor."""
        st.markdown("### System Prompts")
        st.markdown(
            "*These prompts define the AI's core behavior and knowledge about your portfolio.*"
        )

        # Main system prompt
        current_system_prompt = st.session_state.custom_prompts.get("system_prompt", "")

        new_system_prompt = st.text_area(
            "Main System Prompt",
            value=current_system_prompt,
            height=200,
            help="This is the primary instruction that tells the AI how to behave and what it knows about your portfolio.",
        )

        if new_system_prompt != current_system_prompt:
            st.session_state.custom_prompts["system_prompt"] = new_system_prompt

        # Portfolio context prompt
        current_context_prompt = st.session_state.custom_prompts.get(
            "portfolio_context", ""
        )

        new_context_prompt = st.text_area(
            "Portfolio Context Prompt",
            value=current_context_prompt,
            height=150,
            help="Additional context about your portfolio, trading strategy, and preferences.",
        )

        if new_context_prompt != current_context_prompt:
            st.session_state.custom_prompts["portfolio_context"] = new_context_prompt

        # Function calling instructions
        current_function_prompt = st.session_state.custom_prompts.get(
            "function_instructions", ""
        )

        new_function_prompt = st.text_area(
            "Function Calling Instructions",
            value=current_function_prompt,
            height=100,
            help="Instructions for how the AI should use function calls to access portfolio data.",
        )

        if new_function_prompt != current_function_prompt:
            st.session_state.custom_prompts["function_instructions"] = (
                new_function_prompt
            )

        # Preview section
        with st.expander("📋 Preview Combined System Prompt"):
            combined_prompt = self._build_combined_system_prompt()
            st.code(combined_prompt, language="text")
            st.caption(f"Total characters: {len(combined_prompt)}")

    def _render_personality_editor(self):
        """Render AI personality editor."""
        st.markdown("### AI Personality & Style")
        st.markdown("*Customize how the AI communicates and its personality traits.*")

        col1, col2 = st.columns(2)

        with col1:
            # Communication style
            current_style = st.session_state.custom_prompts.get(
                "communication_style", "professional"
            )

            communication_style = st.selectbox(
                "Communication Style",
                options=[
                    "professional",
                    "friendly",
                    "casual",
                    "technical",
                    "enthusiastic",
                ],
                index=[
                    "professional",
                    "friendly",
                    "casual",
                    "technical",
                    "enthusiastic",
                ].index(current_style),
                help="How formal or casual should the AI be?",
            )

            st.session_state.custom_prompts["communication_style"] = communication_style

            # Risk tolerance in advice
            current_risk_stance = st.session_state.custom_prompts.get(
                "risk_stance", "balanced"
            )

            risk_stance = st.selectbox(
                "Risk Advice Stance",
                options=["conservative", "balanced", "aggressive", "neutral"],
                index=["conservative", "balanced", "aggressive", "neutral"].index(
                    current_risk_stance
                ),
                help="How should the AI approach risk in its recommendations?",
            )

            st.session_state.custom_prompts["risk_stance"] = risk_stance

        with col2:
            # Explanation depth
            current_depth = st.session_state.custom_prompts.get(
                "explanation_depth", "detailed"
            )

            explanation_depth = st.selectbox(
                "Explanation Depth",
                options=["brief", "moderate", "detailed", "comprehensive"],
                index=["brief", "moderate", "detailed", "comprehensive"].index(
                    current_depth
                ),
                help="How detailed should explanations be?",
            )

            st.session_state.custom_prompts["explanation_depth"] = explanation_depth

            # Use emojis
            use_emojis = st.checkbox(
                "Use Emojis",
                value=st.session_state.custom_prompts.get("use_emojis", True),
                help="Should the AI use emojis in responses?",
            )

            st.session_state.custom_prompts["use_emojis"] = use_emojis

        # Custom personality traits
        current_traits = st.session_state.custom_prompts.get("personality_traits", "")

        personality_traits = st.text_area(
            "Custom Personality Traits",
            value=current_traits,
            height=100,
            help="Describe specific personality traits or behaviors you want the AI to have.",
        )

        st.session_state.custom_prompts["personality_traits"] = personality_traits

        # Preview personality prompt
        with st.expander("👤 Preview Personality Prompt"):
            personality_prompt = self._build_personality_prompt()
            st.code(personality_prompt, language="text")

    def _render_templates_editor(self):
        """Render response templates editor."""
        st.markdown("### Response Templates")
        st.markdown("*Customize how the AI formats different types of responses.*")

        template_types = {
            "portfolio_summary": "Portfolio Summary Template",
            "asset_analysis": "Asset Analysis Template",
            "risk_warning": "Risk Warning Template",
            "profit_loss": "Profit/Loss Explanation Template",
        }

        for template_key, template_name in template_types.items():
            current_template = st.session_state.custom_prompts.get(
                f"template_{template_key}", ""
            )

            new_template = st.text_area(
                template_name,
                value=current_template,
                height=80,
                help=f"Template for {template_name.lower()} responses. Use {{variable}} for dynamic content.",
            )

            st.session_state.custom_prompts[f"template_{template_key}"] = new_template

        # Template variables reference
        with st.expander("📚 Available Template Variables"):
            st.markdown(
                """
            **Portfolio Summary Variables:**
            - `{total_value}` - Total portfolio value
            - `{total_return}` - Total return percentage
            - `{best_performer}` - Best performing asset
            - `{worst_performer}` - Worst performing asset
            
            **Asset Analysis Variables:**
            - `{asset}` - Asset symbol
            - `{current_price}` - Current price
            - `{return_pct}` - Return percentage
            - `{position_size}` - Position size
            - `{unrealized_pnl}` - Unrealized P&L
            
            **Risk Warning Variables:**
            - `{risk_level}` - Risk level (LOW, MEDIUM, HIGH)
            - `{risk_factors}` - List of risk factors
            - `{recommendation}` - Risk management recommendation
            """
            )

    def _render_settings_editor(self):
        """Render settings and actions."""
        st.markdown("### Settings & Actions")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Save & Load")

            # Save prompts
            if st.button("💾 Save Current Prompts", type="primary"):
                self._save_prompts_to_session()
                st.success("Prompts saved successfully!")

            # Reset to defaults
            if st.button("🔄 Reset to Defaults", type="secondary"):
                if st.button("Confirm Reset", type="secondary"):
                    st.session_state.custom_prompts = self.default_prompts.copy()
                    st.success("Prompts reset to defaults!")
                    st.rerun()

        with col2:
            st.markdown("#### Export & Import")

            # Export prompts
            if st.button("📤 Export Prompts"):
                prompts_json = json.dumps(st.session_state.custom_prompts, indent=2)
                st.download_button(
                    label="Download Prompts JSON",
                    data=prompts_json,
                    file_name=f"ai_prompts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                )

            # Import prompts
            uploaded_file = st.file_uploader("📥 Import Prompts", type="json")
            if uploaded_file is not None:
                try:
                    imported_prompts = json.load(uploaded_file)
                    st.session_state.custom_prompts.update(imported_prompts)
                    st.success("Prompts imported successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error importing prompts: {e}")

        # Current prompt statistics
        st.markdown("#### Current Configuration")
        total_chars = sum(len(str(v)) for v in st.session_state.custom_prompts.values())
        st.metric("Total Prompt Characters", f"{total_chars:,}")

        # Show active configuration
        with st.expander("🔍 Current Configuration Summary"):
            config_summary = {
                "Communication Style": st.session_state.custom_prompts.get(
                    "communication_style", "professional"
                ),
                "Risk Stance": st.session_state.custom_prompts.get(
                    "risk_stance", "balanced"
                ),
                "Explanation Depth": st.session_state.custom_prompts.get(
                    "explanation_depth", "detailed"
                ),
                "Use Emojis": st.session_state.custom_prompts.get("use_emojis", True),
                "Custom Traits": bool(
                    st.session_state.custom_prompts.get("personality_traits", "")
                ),
                "System Prompt Length": len(
                    st.session_state.custom_prompts.get("system_prompt", "")
                ),
                "Templates Configured": sum(
                    1
                    for k in st.session_state.custom_prompts.keys()
                    if k.startswith("template_")
                ),
            }

            for key, value in config_summary.items():
                st.write(f"**{key}:** {value}")

    def _get_default_prompts(self) -> Dict[str, str]:
        """Get default system prompts."""
        return {
            "system_prompt": """You are an expert crypto portfolio analyst with deep knowledge of cryptocurrency markets, technical analysis, and risk management. You have access to the user's real portfolio data through function calls and can provide detailed analysis of their positions.

Key capabilities:
- Analyze portfolio performance and individual asset positions
- Provide technical analysis and price predictions
- Assess risk levels and provide risk management advice
- Explain complex crypto concepts in simple terms
- Give actionable investment insights based on actual data

Always verify information using function calls before making statements about the user's portfolio.""",
            "portfolio_context": """The user's portfolio contains various cryptocurrency positions with real-time data including:
- Current balances and values
- Historical cost basis and P&L
- Transfer history (deposits/withdrawals)
- Performance metrics and returns

Focus on providing insights that are relevant to their actual holdings and investment situation.""",
            "function_instructions": """Use function calls to access real portfolio data before answering questions. Available functions include:
- get_portfolio_summary: Overall portfolio metrics
- get_asset_performance: Individual asset analysis
- get_technical_analysis: Technical indicators and signals
- get_risk_assessment: Risk analysis and recommendations
- get_price_prediction: Price forecasts and targets

Always call relevant functions to get current data rather than making assumptions.""",
            "communication_style": "professional",
            "risk_stance": "balanced",
            "explanation_depth": "detailed",
            "use_emojis": True,
            "personality_traits": "",
            "template_portfolio_summary": "Portfolio Overview: {total_value} total value with {total_return}% overall return. Top performer: {best_performer}, needs attention: {worst_performer}.",
            "template_asset_analysis": "{asset} Analysis: Current price {current_price}, position size {position_size}, return {return_pct}%, unrealized P&L {unrealized_pnl}.",
            "template_risk_warning": "⚠️ Risk Alert: {risk_level} risk detected. Key factors: {risk_factors}. Recommendation: {recommendation}",
            "template_profit_loss": "P&L Summary: {unrealized_pnl} unrealized, {return_pct}% return. {interpretation}",
        }

    def _build_combined_system_prompt(self) -> str:
        """Build the complete system prompt from components."""
        prompts = st.session_state.custom_prompts

        combined = prompts.get("system_prompt", "")

        if prompts.get("portfolio_context"):
            combined += f"\n\nPortfolio Context:\n{prompts['portfolio_context']}"

        if prompts.get("function_instructions"):
            combined += f"\n\nFunction Usage:\n{prompts['function_instructions']}"

        personality_prompt = self._build_personality_prompt()
        if personality_prompt:
            combined += f"\n\nCommunication Style:\n{personality_prompt}"

        return combined

    def _build_personality_prompt(self) -> str:
        """Build personality prompt from settings."""
        prompts = st.session_state.custom_prompts

        style_descriptions = {
            "professional": "Maintain a professional, authoritative tone with clear, structured responses.",
            "friendly": "Be warm and approachable while maintaining expertise and helpfulness.",
            "casual": "Use a relaxed, conversational tone that's easy to understand.",
            "technical": "Focus on technical accuracy with detailed explanations and precise terminology.",
            "enthusiastic": "Show enthusiasm for crypto and investing while being informative.",
        }

        risk_descriptions = {
            "conservative": "Emphasize risk management and capital preservation in all advice.",
            "balanced": "Provide balanced advice considering both opportunities and risks.",
            "aggressive": "Focus on growth opportunities while acknowledging associated risks.",
            "neutral": "Present information objectively without strong directional bias.",
        }

        depth_descriptions = {
            "brief": "Keep responses concise and to the point.",
            "moderate": "Provide adequate detail without being overwhelming.",
            "detailed": "Give comprehensive explanations with supporting context.",
            "comprehensive": "Provide thorough analysis with multiple perspectives and detailed reasoning.",
        }

        personality_parts = []

        # Communication style
        style = prompts.get("communication_style", "professional")
        if style in style_descriptions:
            personality_parts.append(style_descriptions[style])

        # Risk stance
        risk_stance = prompts.get("risk_stance", "balanced")
        if risk_stance in risk_descriptions:
            personality_parts.append(risk_descriptions[risk_stance])

        # Explanation depth
        depth = prompts.get("explanation_depth", "detailed")
        if depth in depth_descriptions:
            personality_parts.append(depth_descriptions[depth])

        # Emoji usage
        if prompts.get("use_emojis", True):
            personality_parts.append(
                "Use relevant emojis to make responses more engaging and easier to read."
            )

        # Custom traits
        custom_traits = prompts.get("personality_traits", "").strip()
        if custom_traits:
            personality_parts.append(f"Additional personality traits: {custom_traits}")

        return " ".join(personality_parts)

    def _save_prompts_to_session(self):
        """Save prompts to session state for persistence."""
        # Already saved in session state during editing
        # This could be extended to save to file or database
        pass

    def get_active_system_prompt(self) -> str:
        """Get the currently active system prompt."""
        if "custom_prompts" not in st.session_state:
            st.session_state.custom_prompts = self.default_prompts.copy()

        return self._build_combined_system_prompt()

    def get_response_template(self, template_type: str) -> str:
        """Get a specific response template."""
        if "custom_prompts" not in st.session_state:
            st.session_state.custom_prompts = self.default_prompts.copy()

        return st.session_state.custom_prompts.get(f"template_{template_type}", "")
