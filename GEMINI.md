# Gemini Agent Context

> This file provides context for AI coding assistants working on this project.

## Project Overview

**Jarvis** is a modular, AI-powered personal assistant built with Python and FastAPI. It provides voice-enabled daily briefings including weather, todos, and calendar events.

## Architecture

```
heart.py (FastAPI Server)
    ├── brain.py (Gemini AI)
    ├── arms.py (HTTP Client)
    ├── mouth.py (TTS Output)
    └── apis/
        └── weather.py (Open-Meteo)
```

### Key Design Decisions

1. **Body metaphor**: Components are named after body parts (heart, brain, arms, mouth) to represent their functions
2. **Module-level initialization**: `heart.py` initializes Brain, Arms, and Mouth at module level (before FastAPI app starts)
3. **Async HTTP**: Uses `httpx.AsyncClient` for all external API calls
4. **TTS with speed adjustment**: gTTS output is sped up 1.25x for natural listening

## Important Context for AI Agents

### Testing Considerations

- **heart.py tests require mocking before import** because it initializes components at module level
- Use `@pytest.fixture(scope="module")` to mock `brain.genai`, `mouth.gTTS`, etc. before importing heart
- The `mock_components` fixture in `tests/test_heart.py` demonstrates the pattern

### API Keys & Secrets

- Gemini API key is stored in `secrets.json` (gitignored)
- Format: `{"gemini_api_key": "your-key"}`
- Brain reads from secrets.json on initialization

### Common Tasks

#### Adding a New API Integration

1. Create wrapper class in `apis/` directory (see `weather.py` for pattern)
2. Add async method to `Arms` class in `arms.py`
3. Create endpoint in `heart.py`
4. Add tests in `tests/`

#### Adding a New Endpoint

1. Add route function in `heart.py` with `@app.get()` or `@app.post()`
2. Add to `jarvis_actions` dict if it should be voice-accessible
3. Add integration test in `tests/test_heart.py`

### Current Limitations & TODOs

- **Todoist integration**: Stub exists in `arms.py`, needs API setup
- **Google Calendar**: Stub exists, needs OAuth flow
- **Wake word detection**: Planned iOS app with Picovoice Porcupine
- **User input routing**: Commented out in `heart.py`, needs completion

### Code Style

- **Linter**: Ruff (configured in `pyproject.toml`)
- **Type hints**: All public methods should have type hints
- **Docstrings**: Google-style docstrings for all classes and public methods
- **Import order**: stdlib → third-party → local (enforced by Ruff)

### Running the Project

```bash
# Activate venv
source venv/bin/activate

# Run tests
make test

# Lint
make fmt

# Start server
make run  # or: python heart.py
```

### File Quick Reference

| File | Purpose | Key Classes/Functions |
|------|---------|----------------------|
| `heart.py` | FastAPI server, main entry | `app`, `lifespan()`, route handlers |
| `brain.py` | AI processing | `Brain`, `process()`, `choose()` |
| `arms.py` | HTTP client | `Arms`, `get()`, `get_weather()` |
| `mouth.py` | Text-to-speech | `Mouth`, `speak()` |
| `apis/weather.py` | Weather API wrapper | `WeatherAPI`, builder pattern |

### Debugging Tips

1. **Gemini connection issues**: Check `secrets.json` and API quota
2. **Import errors in tests**: Ensure mocking happens before import
3. **Audio not playing**: Check for `speech.mp3` in project root
4. **Rate limits**: Gemini free tier has request limits, wait or use paid tier
