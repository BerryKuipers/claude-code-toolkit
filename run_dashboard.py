#!/usr/bin/env python3
"""
Launcher script for the Streamlit dashboard.
This script sets up the Python path correctly and launches the dashboard.
"""

import sys
import os
import subprocess

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Set environment variables from .env file
env_file = os.path.join(project_root, ".env")
if os.path.exists(env_file):
    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

# Launch Streamlit
if __name__ == "__main__":
    # Import and run the main function
    from src.portfolio.ui import main

    # Set up Streamlit configuration
    import streamlit as st

    # Configure the page
    st.set_page_config(
        page_title="Crypto Portfolio Dashboard",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Run the main function
    main()
