# Jarvis

[![CI](https://github.com/TrueshotBarrage/jarvis/actions/workflows/ci.yml/badge.svg)](https://github.com/TrueshotBarrage/jarvis/actions/workflows/ci.yml)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> A modular, AI-powered personal assistant built with Python and FastAPI.

## Overview

Jarvis is a voice-enabled personal assistant that provides daily briefings including weather updates, todos, and calendar events. It leverages Google's Gemma AI (via Gemini API) for natural language processing and text-to-speech for vocal output.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        main.py                              │
│                     (Entry Point)                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                       heart.py                              │
│            FastAPI Server (Central Coordinator)             │
│  • Routes: /weather, /daily, /intro, /test                  │
│  • Orchestrates all components                              │
└───────┬─────────────────┬─────────────────┬─────────────────┘
        │                 │                 │
┌───────▼───────┐ ┌───────▼───────┐ ┌───────▼───────┐
│   brain.py    │ │   arms.py     │ │   mouth.py    │
│  (Gemini AI)  │ │ (HTTP Client) │ │    (TTS)      │
│               │ │               │ │               │
│ • LLM calls   │ │ • Weather API │ │ • gTTS output │
│ • Intent      │ │ • Todoist*    │ │ • Audio       │
│   detection   │ │ • GCal*       │ │   playback    │
└───────────────┘ └───────┬───────┘ └───────────────┘
                          │
                  ┌───────▼───────┐
                  │ apis/         │
                  │ weather.py    │
                  │ (Open-Meteo)  │
                  └───────────────┘
                  
* = Planned, not yet implemented
```

## Components

| Component | File | Description |
|-----------|------|-------------|
| **Heart** | `heart.py` | FastAPI server - central coordinator |
| **Brain** | `brain.py` | Gemini AI integration for LLM processing |
| **Arms** | `arms.py` | Async HTTP client for external API calls |
| **Mouth** | `mouth.py` | Text-to-speech via gTTS with audio playback |
| **APIs** | `apis/` | API wrappers (currently: Open-Meteo weather) |

## Installation

### Prerequisites
- Python 3.10+
- A Google Gemini API key

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/jarvis.git
cd jarvis

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure secrets
echo '{"gemini_api_key": "YOUR_API_KEY"}' > secrets.json
```

## Usage

### Start the Server

```bash
python heart.py
```

The server will start at `http://127.0.0.1:8000`.

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/weather` | GET | Get current weather forecast |
| `/daily` | GET | Run daily routine (weather + TTS output) |
| `/intro` | GET | AI-generated assistant introduction |
| `/test` | GET | Test external API connectivity |

### Example

```bash
# Get today's weather
curl http://localhost:8000/weather

# Run daily briefing (speaks aloud)
curl http://localhost:8000/daily
```

## Configuration

### secrets.json

```json
{
  "gemini_api_key": "your-google-gemini-api-key"
}
```

### Weather Location

Default location is set in `apis/weather.py`. To change:

```python
weather_api = WeatherAPI()
weather_api.set_coordinates(lat=40.7128, lon=-74.0060)  # New York
```

## Development Status

### ✅ Completed
- Weather API integration (Open-Meteo)
- Gemini AI integration for natural language processing
- Text-to-speech output with speed adjustment
- Daily routine endpoint

### 🚧 In Progress
- Todoist API integration
- Google Calendar API integration

### 📋 Planned
- Picovoice wake word detection
- iOS companion app
- Autobudget pipeline integration

See [ROADMAP.md](ROADMAP.md) for detailed development plans.

## Development

### Setup Dev Environment

```bash
# Install dev dependencies
source venv/bin/activate
pip install pytest pytest-asyncio pytest-cov ruff
```

### Running Tests

```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Or directly with pytest
python -m pytest tests/ -v
```

### Linting & Formatting

This project uses [Ruff](https://github.com/astral-sh/ruff) for linting and formatting.

```bash
# Check for linting issues
make lint

# Auto-fix issues and format
make fmt

# Or directly with ruff
ruff check .
ruff format .
```

### Available Make Targets

| Command | Description |
|---------|-------------|
| `make install` | Install production dependencies |
| `make dev` | Install dev dependencies (pytest, ruff) |
| `make test` | Run test suite |
| `make test-cov` | Run tests with coverage report |
| `make lint` | Check code quality |
| `make fmt` | Auto-fix and format code |
| `make run` | Start the server |
| `make clean` | Clean generated files |

## License

MIT License