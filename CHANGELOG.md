# Changelog

All notable changes to the Jarvis project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.3.0] - 2025-12-08

### Added

#### Todoist Integration
- **apis/todoist.py** - Todoist REST API v2 wrapper with direct HTTP requests
- **`/todos` endpoint** - Get today's tasks from Todoist
- **Tests** - 12 unit tests for TodoistAPI, 2 integration tests for endpoints
- Todoist API token support in `secrets.json`

#### Daily Briefing Improvements
- **Unified AI prompt** - Single consolidated prompt for weather, events, and todos
- **Intelligent summarization** - AI now prioritizes 2-3 key items instead of listing everything
- **Nova persona** - AI assistant with personality and natural speech patterns
- **`briefing` response key** - AI-generated text now included in `/daily` and `/intro` responses

#### Developer Experience
- **`--reload` flag** for uvicorn in `make run` - Auto-restart on code changes
- **`autoplay` parameter** for `mouth.speak()` - Control audio playback (default: off)

### Changed

#### Mouth Module
- `speak()` now defaults to `autoplay=False` - Audio file is generated but not played automatically
- Playback speed increased from 1.25x to 1.4x for more natural listening

#### Heart Module
- `/daily` now uses single AI call instead of three separate calls
- `/daily` response includes `briefing` key with AI-generated summary
- `/intro` response changed from `result` to `intro` key with actual AI output

#### Documentation
- Updated `GEMINI.md` with Todoist API info, architecture, and secrets format
- Updated `ROADMAP.md` to mark Todoist integration as complete

### Fixed
- Fixed Python 3.14 compatibility by replacing `todoist-api-python` SDK with direct REST API calls
  (SDK's `dataclass-wizard` dependency has Python 3.14 compatibility issues)

---

## [0.2.0] - 2025-12-07

### Added

#### Testing & Code Quality
- **Test suite** with pytest (34 tests covering all modules)
- **pytest-asyncio** for async endpoint testing
- **pytest-cov** for code coverage reporting
- **Ruff** for linting and formatting
- `pyproject.toml` with project configuration
- `Makefile` with convenient dev commands (`make test`, `make lint`, etc.)

#### Documentation
- Comprehensive `README.md` with architecture diagram, installation guide, and API docs
- `ROADMAP.md` with prioritized development initiatives
- `GEMINI.md` with agentic context for AI pair programming

#### Test Files
- `tests/test_weather.py` - WeatherAPI unit tests
- `tests/test_arms.py` - HTTP client tests with mocking
- `tests/test_brain.py` - AI module tests with mocked Gemini
- `tests/test_mouth.py` - TTS module tests
- `tests/test_heart.py` - FastAPI integration tests

### Changed

#### Code Quality Improvements
- **brain.py**: Added module docstring, comprehensive docstrings, type hints, extracted `_verify_connection()` method
- **arms.py**: Added `APIResponse` TypedDict, docstrings, type hints, improved null safety
- **mouth.py**: Made audio path configurable, removed unused Brain dependency, added docstrings
- **heart.py**: Fixed duplicate function names (`test` → `test_external_api`, `test` → `get_introduction`), fixed f-string syntax error, added module docstring, removed duplicate imports
- **apis/weather.py**: Added type hints

#### Configuration
- Updated `requirements.txt` with `google-generativeai` and organized with comments
- Enhanced `.gitignore` with `*.mp3`, test cache, and coverage directories
- Updated AI model from `gemini-1.5-flash` to `gemma-3-27b-it` (free, 27B params, 128K context)

### Removed
- `main.py` - Outdated entry point that referenced non-existent methods

### Fixed
- Duplicate function name `test` defined twice in `heart.py`
- F-string quoting error on line 62 of original `heart.py`
- Mouth class no longer requires Brain instance (was unused)

---

## [0.1.0] - 2024-10-31

### Added
- Initial implementation of Jarvis personal assistant
- **heart.py** - FastAPI server with weather and daily routine endpoints
- **brain.py** - Gemini AI integration for LLM processing
- **arms.py** - Async HTTP client for external APIs
- **mouth.py** - Text-to-speech using gTTS
- **apis/weather.py** - Open-Meteo weather API wrapper
- Weather API integration with daily briefing
- Voice output with speed adjustment
