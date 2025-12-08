# Development Setup

This guide covers setting up a development environment for Jarvis.

## Prerequisites

- Python 3.13+
- [Google Gemini API key](https://aistudio.google.com/app/apikey)

## Quick Setup

```bash
# Clone and enter directory
git clone https://github.com/TrueshotBarrage/jarvis.git
cd jarvis

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | ✅ | Google Gemini API key |
| `TODOIST_API_TOKEN` | ❌ | Todoist API token |
| `GOOGLE_CALENDAR_ID` | ❌ | Your calendar email |
| `WEATHER_LAT` / `WEATHER_LON` | ❌ | Location coordinates |

## Running the Server

```bash
make run          # Development server with auto-reload
# or
python heart.py   # Direct execution
```

Server starts at `http://127.0.0.1:8000`

## Running Tests

```bash
make test         # Run all tests
make test-cov     # Run with coverage report
make lint         # Check linting
make fmt          # Auto-fix linting + format
```

## Docker

```bash
make docker-build   # Build image
make docker-up      # Start container
make docker-down    # Stop container
make docker-logs    # View logs
```

## Project Structure

```
jarvis/
├── heart.py          # FastAPI server (main entry)
├── brain.py          # Gemini AI integration
├── arms.py           # HTTP client
├── mouth.py          # Text-to-speech
├── memory.py         # Conversation storage
├── cache.py          # Data caching
├── context.py        # AI context management
├── intent.py         # Intent detection
├── config.py         # Centralized settings
├── apis/             # API wrappers
│   ├── weather.py
│   ├── calendar.py
│   └── todoist.py
├── tests/            # Test suite
└── db/               # SQLite database
```

## Makefile Commands

| Command | Description |
|---------|-------------|
| `make install` | Install production deps |
| `make dev` | Install dev deps |
| `make run` | Start dev server |
| `make test` | Run tests |
| `make test-cov` | Tests with coverage |
| `make fmt` | Format + lint fix |
| `make lint` | Check linting |
| `make clean` | Remove generated files |
