"""Model selection UI component for choosing AI models."""

from typing import Dict, Optional

import streamlit as st

from .base_llm_client import AVAILABLE_MODELS, LLMClientFactory, LLMProvider, ModelInfo


def render_model_selector() -> str:
    """Render the model selection UI and return the selected model key.

    Returns:
        Selected model key from AVAILABLE_MODELS
    """
    st.subheader("🤖 AI Model Selection")

    # Get available models
    models = LLMClientFactory.get_available_models()
    default_model = LLMClientFactory.get_default_model()

    # Initialize session state for selected model
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = default_model

    # Create columns for the selector
    col1, col2 = st.columns([2, 3])

    with col1:
        # Model selection dropdown
        model_options = list(models.keys())
        model_labels = [models[key].display_name for key in model_options]

        # Find current selection index
        try:
            current_index = model_options.index(st.session_state.selected_model)
        except ValueError:
            current_index = model_options.index(default_model)

        selected_index = st.selectbox(
            "Choose AI Model:",
            range(len(model_options)),
            index=current_index,
            format_func=lambda i: model_labels[i],
            help="Select the AI model for portfolio analysis and chat",
            key="model_selector_key",  # Stable key to reduce unnecessary reruns
        )

        # Update selected model
        selected_model_key = model_options[selected_index]
        st.session_state.selected_model = selected_model_key

    with col2:
        # Display model information
        selected_model = models[selected_model_key]
        _render_model_info(selected_model)

    # Show cost comparison
    with st.expander("💰 Cost Comparison"):
        _render_cost_comparison(models)

    # Show model capabilities comparison
    with st.expander("⚡ Capabilities Comparison"):
        _render_capabilities_comparison(models)

    return selected_model_key


def _render_model_info(model: ModelInfo):
    """Render detailed information about a specific model."""
    # Provider badge
    provider_colors = {
        LLMProvider.ANTHROPIC: "🟣",
        LLMProvider.OPENAI: "🟢",
        LLMProvider.PERPLEXITY: "🔵",
    }

    provider_emoji = provider_colors.get(model.provider, "⚪")
    st.markdown(f"**{provider_emoji} {model.provider.value.title()}**")

    # Description
    st.markdown(f"*{model.description}*")

    # Key strengths
    st.markdown("**Key Strengths:**")
    for strength in model.strengths:
        st.markdown(f"• {strength}")

    # Technical specs
    st.markdown("**Specifications:**")
    st.markdown(f"• Context: {model.context_window:,} tokens")
    st.markdown(
        f"• Function calling: {'✅' if model.supports_function_calling else '❌'}"
    )
    st.markdown(f"• Vision support: {'✅' if model.supports_vision else '❌'}")

    # Cost info
    st.markdown("**Pricing:**")
    st.markdown(f"• Input: ${model.cost_per_1k_input:.4f}/1K tokens")
    st.markdown(f"• Output: ${model.cost_per_1k_output:.4f}/1K tokens")


def _render_cost_comparison(models: Dict[str, ModelInfo]):
    """Render a cost comparison table."""
    st.markdown("**Cost per 1,000 tokens:**")

    # Create comparison data
    comparison_data = []
    for key, model in models.items():
        comparison_data.append(
            {
                "Model": model.display_name,
                "Provider": model.provider.value.title(),
                "Input Cost": f"${model.cost_per_1k_input:.4f}",
                "Output Cost": f"${model.cost_per_1k_output:.4f}",
                "Typical Query Cost": f"${_estimate_typical_query_cost(model):.4f}",
            }
        )

    st.table(comparison_data)

    st.caption("*Typical query cost assumes ~500 input tokens and ~200 output tokens")


def _render_capabilities_comparison(models: Dict[str, ModelInfo]):
    """Render a capabilities comparison table."""
    st.markdown("**Model Capabilities:**")

    comparison_data = []
    for key, model in models.items():
        comparison_data.append(
            {
                "Model": model.display_name,
                "Context Window": f"{model.context_window:,}",
                "Function Calling": "✅" if model.supports_function_calling else "❌",
                "Vision": "✅" if model.supports_vision else "❌",
                "Best For": _get_best_use_case(model),
            }
        )

    st.table(comparison_data)


def _estimate_typical_query_cost(model: ModelInfo) -> float:
    """Estimate cost for a typical portfolio query."""
    # Assume typical query: 500 input tokens, 200 output tokens
    input_tokens = 500
    output_tokens = 200

    input_cost = (input_tokens / 1000) * model.cost_per_1k_input
    output_cost = (output_tokens / 1000) * model.cost_per_1k_output

    return input_cost + output_cost


def _get_best_use_case(model: ModelInfo) -> str:
    """Get the best use case description for a model."""
    if "claude-sonnet-4" in model.model_id:
        return "Balanced analysis"
    elif "claude-opus-4" in model.model_id:
        return "Complex reasoning"
    elif "gpt-4" in model.model_id:
        return "General purpose"
    elif "gpt-3.5" in model.model_id:
        return "Quick queries"
    else:
        return "General use"


def get_model_recommendation_message(model_key: str) -> str:
    """Get a recommendation message for the selected model."""
    models = LLMClientFactory.get_available_models()
    model = models[model_key]

    if model_key == "claude-sonnet-4":
        return "🎯 **Recommended Choice!** Claude Sonnet 4 offers the best balance of intelligence, speed, and cost for financial analysis."
    elif model_key == "gpt-4o":
        return "🚀 **OpenAI Default!** GPT-4o is OpenAI's latest flagship model with exceptional reasoning and function calling capabilities."
    elif model_key == "claude-opus-4":
        return "🚀 **Premium Choice!** Claude Opus 4 provides the highest level of intelligence for complex financial reasoning."
    elif model_key == "gpt-4-turbo":
        return "🔧 **Reliable Choice!** GPT-4 Turbo offers strong general capabilities with established performance."
    elif model_key == "gpt-4o-mini":
        return "💰 **Budget Choice!** GPT-4o Mini offers GPT-4 level intelligence at a fraction of the cost."
    else:
        return "✅ **Good Choice!** This model will work well for your portfolio analysis needs."


def show_model_switch_success(old_model: str, new_model: str):
    """Show a success message when switching models."""
    models = LLMClientFactory.get_available_models()
    old_name = models[old_model].display_name if old_model in models else old_model
    new_name = models[new_model].display_name if new_model in models else new_model

    st.success(f"🔄 Switched from **{old_name}** to **{new_name}**")

    # Show recommendation for new model
    recommendation = get_model_recommendation_message(new_model)
    st.info(recommendation)


def render_model_status_indicator(model_key: str):
    """Render a small status indicator showing the current model."""
    models = LLMClientFactory.get_available_models()
    if model_key in models:
        model = models[model_key]
        provider_colors = {
            LLMProvider.ANTHROPIC: "🟣",
            LLMProvider.OPENAI: "🟢",
            LLMProvider.PERPLEXITY: "🔵",
        }

        provider_emoji = provider_colors.get(model.provider, "⚪")
        st.caption(f"Using: {provider_emoji} **{model.display_name}**")
    else:
        st.caption(f"Using: **{model_key}**")
