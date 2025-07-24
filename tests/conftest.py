"""Test configuration and fixtures for crypto-insight tests."""

import os
import sys
from pathlib import Path

# Add the project root to Python path so tests can import from src
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# Load environment variables from .env file for tests
def load_env_file():
    """Load environment variables from .env file."""
    env_file = project_root / ".env"
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()


# Load environment variables at test startup
load_env_file()
