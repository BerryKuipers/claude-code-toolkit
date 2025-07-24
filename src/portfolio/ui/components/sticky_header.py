"""
Sticky header component for Crypto Insight dashboard.
Provides a fixed navigation header that stays at the top during scrolling.
"""

import streamlit as st


def render(active_tab: str = "Portfolio") -> None:
    """
    Render the sticky header with navigation.

    Args:
        active_tab: Currently active tab name
    """
    # Initialize session state for tab selection
    if "tab" not in st.session_state:
        st.session_state.tab = active_tab

    # Inject CSS for sticky header
    st.markdown(
        """
        <style>
        /* Sticky header container */
        .ci-header {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            background: #0E1117;
            padding: 0.75rem 1rem;
            border-bottom: 1px solid #262730;
            z-index: 1000;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }
        
        /* Brand styling */
        .ci-brand {
            color: #fafafa;
            font-size: 1.5rem;
            font-weight: 700;
            margin: 0;
        }
        
        /* Navigation container */
        .ci-nav {
            display: flex;
            gap: 1rem;
            align-items: center;
        }
        
        /* Navigation buttons */
        .ci-nav-btn {
            background: #262730;
            border: 1px solid #3d4043;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            color: #fafafa;
            text-decoration: none;
            font-weight: 500;
            transition: all 0.2s ease;
            cursor: pointer;
        }
        
        .ci-nav-btn:hover {
            background: #3d4043;
            border-color: #4a5568;
            color: #ffffff;
            transform: translateY(-1px);
        }
        
        .ci-nav-btn.active {
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
            border-color: #3b82f6;
            color: white;
        }
        
        /* Push main content down so it's not hidden under header */
        section.main > div:first-child {
            margin-top: 80px;
        }
        
        /* Hide Streamlit's default header */
        header[data-testid="stHeader"] {
            display: none;
        }
        
        /* Mobile responsiveness */
        @media (max-width: 750px) {
            .ci-header {
                flex-direction: column;
                padding: 0.5rem;
                gap: 0.5rem;
            }
            
            .ci-nav {
                flex-wrap: wrap;
                gap: 0.5rem;
                justify-content: center;
            }
            
            .ci-nav-btn {
                padding: 0.4rem 0.8rem;
                font-size: 0.9rem;
            }
            
            section.main > div:first-child {
                margin-top: 100px;
            }
        }
        
        /* Fix radio button styling if using st.radio */
        div[data-baseweb="radio"] > div {
            gap: 0.5rem;
        }
        
        /* Remove ugly white backgrounds */
        .stApp {
            background-color: #0e1117;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Get current tab
    current_tab = st.session_state.get("tab", "Portfolio")

    # Add sticky header CSS
    st.markdown(
        """
    <style>
    .ci-header {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        z-index: 999998 !important;
        background: #0E1117 !important;
        border-bottom: 1px solid #262730 !important;
        padding: 10px 20px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3) !important;
    }

    .ci-brand {
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        color: #1f2937 !important;
        margin: 0 !important;
    }

    .ci-nav {
        display: flex !important;
        gap: 10px !important;
        align-items: center !important;
    }

    .ci-nav-btn {
        padding: 8px 16px !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        background: #f8f9fa !important;
        color: #495057 !important;
        border: 1px solid #dee2e6 !important;
    }

    .ci-nav-btn.active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border-color: #667eea !important;
    }

    .ci-nav-btn:hover {
        background: #e9ecef !important;
        transform: translateY(-1px) !important;
    }

    .ci-nav-btn.active:hover {
        background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%) !important;
    }

    /* Add margin to main content */
    .main .block-container {
        padding-top: 80px !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Create sticky header with Streamlit components
    header_container = st.container()

    with header_container:
        # Create header layout
        col1, col2, col3, col4, col5 = st.columns([0.5, 2, 1, 1, 1])

        with col1:
            if st.button("☰", key="sidebar_toggle_btn", help="Toggle Sidebar"):
                # Toggle sidebar state
                current_state = st.session_state.get("sidebar_state", "expanded")
                new_state = "collapsed" if current_state == "expanded" else "expanded"
                st.session_state.sidebar_state = new_state
                st.rerun()

        with col2:
            st.markdown(
                '<h1 style="color: #1f2937; margin: 0; font-size: 1.5rem;">📊 Crypto Insight</h1>',
                unsafe_allow_html=True,
            )

        with col3:
            if st.button(
                "💼 Portfolio",
                key="header_portfolio_btn",
                type="primary" if current_tab == "Portfolio" else "secondary",
            ):
                st.session_state.tab = "Portfolio"
                st.rerun()

        with col4:
            if st.button(
                "📈 Analysis",
                key="header_analysis_btn",
                type="primary" if current_tab == "Analysis" else "secondary",
            ):
                st.session_state.tab = "Analysis"
                st.rerun()

        with col5:
            if st.button(
                "⚙️ Settings",
                key="header_settings_btn",
                type="primary" if current_tab == "Settings" else "secondary",
            ):
                st.session_state.tab = "Settings"
                st.rerun()

    # Add CSS to make the header truly sticky
    st.markdown(
        """
    <style>
    /* Hide Streamlit's default header */
    header[data-testid="stHeader"] {
        display: none !important;
    }

    /* Create sticky header */
    .stApp > div:first-child {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        z-index: 999999 !important;
        background: #0E1117 !important;
        border-bottom: 1px solid #262730 !important;
        padding: 10px 20px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3) !important;
    }

    /* Push main content down */
    .main .block-container {
        padding-top: 80px !important;
    }

    /* Style the header buttons */
    .stApp > div:first-child .stButton > button {
        border-radius: 6px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }

    /* Active button styling */
    .stApp > div:first-child .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def get_current_tab() -> str:
    """Get the currently selected tab."""
    return st.session_state.get("tab", "Portfolio")
