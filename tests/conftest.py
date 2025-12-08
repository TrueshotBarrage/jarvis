"""Pytest fixtures for Jarvis tests."""

import sys
from pathlib import Path

import pytest

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def mock_secrets(tmp_path):
    """Create a temporary secrets file for testing."""
    secrets_file = tmp_path / "secrets.json"
    secrets_file.write_text('{"gemini_api_key": "test-api-key"}')
    return str(secrets_file)
