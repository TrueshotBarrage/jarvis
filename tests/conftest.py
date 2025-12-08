"""Pytest fixtures for Jarvis tests."""

import sys
from pathlib import Path

# Add src directory to path for package imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
