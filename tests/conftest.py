"""Shared pytest fixtures."""

import os
import sys
import pytest

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv

load_dotenv()


@pytest.fixture
def check_api_keys():
    """Check that required API keys are set."""
    required_keys = [
        "E2B_API_KEY",
        "PERPLEXITY_API_KEY",
    ]
    missing = [k for k in required_keys if not os.getenv(k)]
    if missing:
        pytest.skip(f"Missing API keys: {', '.join(missing)}")
