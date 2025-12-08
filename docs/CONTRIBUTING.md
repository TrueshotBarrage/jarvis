# Contributing to Jarvis

Thank you for your interest in contributing! This guide covers the process.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/jarvis.git`
3. Follow [DEVELOPMENT.md](DEVELOPMENT.md) for setup

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

### 2. Make Changes

- Follow the existing code style
- Add tests for new functionality
- Update documentation if needed

### 3. Run Tests

```bash
make fmt    # Format and lint
make test   # Run all tests
```

**All tests must pass before submitting a PR.**

## Code Style

- **Linter**: Ruff (configured in `pyproject.toml`)
- **Formatter**: Ruff
- **Type hints**: Required for all public functions
- **Docstrings**: Google-style docstrings

Example:
```python
def process(self, message: str, context: str | None = None) -> str:
    """Process a message using the AI model.

    Args:
        message: The input message to process.
        context: Optional context for the AI.

    Returns:
        The AI-generated response text.
    """
```

## Testing Requirements

- New features need tests
- Bug fixes should include regression tests
- Maintain or improve code coverage
- Mock external services (Gemini, APIs)

### Test Mocking Pattern

```python
@patch("brain.settings")
@patch("brain.genai")
def test_example(self, mock_genai, mock_settings):
    mock_settings.gemini_api_key = "test-key"
    # ... test code
```

## Pull Request Process

1. Update `CHANGELOG.md` with your changes
2. Ensure CI passes (lint + tests)
3. Request review
4. Squash and merge after approval

### PR Title Format

```
feat: Add new weather alerts
fix: Handle missing calendar events
docs: Update API documentation
refactor: Simplify intent detection
test: Add cache expiration tests
```

## Questions?

Open an issue or discussion for any questions about contributing.
