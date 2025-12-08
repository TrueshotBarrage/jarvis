# Gemini Agent Context

> This file provides context for AI coding assistants working on this project.
> ALWAYS remember to update this file with any new relevant context that future
> AI agents will need to know. This includes any changes to the project structure,
> new dependencies, new APIs, new endpoints, new actions, new features, etc.

## Project Overview

**Jarvis** is a modular, AI-powered personal assistant built with Python and FastAPI. It provides voice-enabled daily briefings including weather, todos, and calendar events.

## Architecture

```
heart.py (FastAPI Server)
    ├── brain.py (Gemini AI)
    ├── arms.py (HTTP Client)
    ├── mouth.py (TTS Output)
    ├── memory.py (SQLite Conversations)
    ├── cache.py (TTL Data Cache)
    └── apis/
        ├── weather.py (Open-Meteo)
        ├── calendar.py (Google Calendar)
        └── todoist.py (Todoist)
```

### Key Design Decisions

1. **Body metaphor**: Components are named after body parts (heart, brain, arms, mouth) to represent their functions
2. **Module-level initialization**: `heart.py` initializes Brain, Arms, Mouth, Memory, and Cache at module level
3. **Async HTTP**: Uses `httpx.AsyncClient` for all external API calls
4. **TTS with speed adjustment**: gTTS output is sped up 1.4x for natural listening
5. **Conversation memory**: SQLite-based storage with time-based retrieval (last 4 hours)
6. **Data caching**: TTL-based caching (weather 30min, events/todos 5min)

## Important Context for AI Agents

### Testing Considerations

- **heart.py tests require mocking before import** because it initializes components at module level
- Use `@pytest.fixture(scope="module")` to mock `brain.genai`, `mouth.gTTS`, etc. before importing heart
- The `mock_components` fixture in `tests/test_heart.py` demonstrates the pattern

### Configuration

Configuration uses **Pydantic Settings** with environment variable and `.env` file support:

1. **Setup**: Copy `.env.example` to `.env` and fill in your API keys
2. **Priority**: Environment variables > `.env` file > defaults
3. **Config module**: All settings are accessed via `from config import settings`

```bash
# Required
GEMINI_API_KEY=your-gemini-key

# Optional
TODOIST_API_TOKEN=your-todoist-token
GOOGLE_CALENDAR_ID=your.email@gmail.com
WEATHER_LAT=40.789
WEATHER_LON=-73.967
```

**For tests**: Mock `config.settings` instead of creating test files:
```python
@patch("brain.settings")
def test_example(self, mock_settings):
    mock_settings.gemini_api_key = "test-key"
```

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

- **Google Calendar**: ✅ Complete - uses service account auth
- **Todoist**: ✅ Complete - uses API token auth
- **Conversation Memory**: ✅ Complete - SQLite with time-based retrieval
- **Data Cache**: ✅ Complete - TTL-based with force refresh
- **Wake word detection**: Planned iOS app with Picovoice Porcupine
- **User input routing**: Commented out in `heart.py`, needs completion

### Database

- SQLite database stored in `db/jarvis.db` (gitignored)
- Initialize with: `python db/init.py`
- Schema: `messages` table with `id`, `role`, `content`, `created_at`

### Code Style

- **Linter**: Ruff (configured in `pyproject.toml`)
- **Type hints**: All public methods should have type hints
- **Docstrings**: Google-style docstrings for all classes and public methods
- **Import order**: stdlib → third-party → local (enforced by Ruff)

### Running the Project

Always remember to periodically run `make fmt` with every new change.

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
| `heart.py` | FastAPI server, main entry | `app`, `lifespan()`, `/chat`, route handlers |
| `brain.py` | AI processing | `Brain`, `process()`, `choose()`, `chat()` |
| `arms.py` | HTTP client | `Arms`, `get()`, `get_weather()`, `get_events()`, `get_todos()` |
| `mouth.py` | Text-to-speech | `Mouth`, `speak()` |
| `memory.py` | Conversation storage | `Memory`, SQLite, `add_message()`, `get_recent()` |
| `cache.py` | Data caching | `Cache`, TTL-based, `get()`, `get_context_summary()` |
| `context.py` | AI context management | `Context`, `build()`, always-fresh + cached data |
| `intent.py` | Intent detection | `IntentDetector`, hybrid regex + LLM |
| `config.py` | Centralized settings | `Settings`, Pydantic Settings, `.env` support |
| `apis/weather.py` | Weather API wrapper | `WeatherAPI`, builder pattern |
| `apis/calendar.py` | Google Calendar API wrapper | `CalendarAPI`, service account auth |
| `apis/todoist.py` | Todoist API wrapper | `TodoistAPI`, token auth |

### Debugging Tips

1. **Gemini connection issues**: Check `.env` has valid `GEMINI_API_KEY` and API quota
2. **Import errors in tests**: Ensure mocking happens before import
3. **Audio not playing**: Check for `speech.mp3` in project root
4. **Rate limits**: Gemini free tier has request limits, wait or use paid tier

### CI/CD Pipeline

GitHub Actions workflows are in `.github/workflows/`:

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | Push/PR to main | Lint + Test (Python 3.13, 3.14) |
| `dependency-review.yml` | PRs | Check for vulnerable dependencies |
| `release.yml` | Tag push (v*.*.*) | Create GitHub release |

**Creating a Release:**
```bash
git tag v0.2.0
git push origin v0.2.0
```

**Required Secrets:**
- `CODECOV_TOKEN` - For coverage reporting

### Python 3.14 Compatibility

- Uses `playsound3` instead of `playsound` (Python 3.14 compatible)
- Requires `audioop-lts` for `pydub` compatibility (audioop removed in Python 3.13+)
- Mock paths in tests use `mouth.playsound3` not `mouth.playsound`
