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
│  • Routes: /weather, /daily, /events, /todos, /intro        │
│  • Orchestrates all components                              │
└───────┬─────────────────┬─────────────────┬─────────────────┘
        │                 │                 │
┌───────▼───────┐ ┌───────▼───────┐ ┌───────▼───────┐
│   brain.py    │ │   arms.py     │ │   mouth.py    │
│  (Gemini AI)  │ │ (HTTP Client) │ │    (TTS)      │
│               │ │               │ │               │
│ • LLM calls   │ │ • Weather API │ │ • gTTS output │
│ • Intent      │ │ • Todoist API │ │ • Audio       │
│   detection   │ │ • Calendar    │ │   playback    │
└───────────────┘ └───────┬───────┘ └───────────────┘
                          │
                  ┌───────▼───────┐
                  │ apis/         │
                  │ weather.py    │
                  │ calendar.py   │
                  │ todoist.py    │
                  └───────────────┘
```

## Components

| Component | File | Description |
|-----------|------|-------------|
| **Heart** | `heart.py` | FastAPI server - central coordinator |
| **Brain** | `brain.py` | Gemini AI integration for LLM processing |
| **Arms** | `arms.py` | Async HTTP client for external API calls |
| **Mouth** | `mouth.py` | Text-to-speech via gTTS with audio playback |
| **APIs** | `apis/` | API wrappers (weather, calendar, todoist) |

## Installation

### Prerequisites
- Python 3.13+
- A [Google Gemini API key](https://aistudio.google.com/app/apikey)
- (Optional) Google Cloud project for Calendar integration

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/TrueshotBarrage/jarvis.git
cd jarvis

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment (required)
cp .env.example .env
# Edit .env with your API keys:
# GEMINI_API_KEY=your-gemini-key
# TODOIST_API_TOKEN=your-todoist-token (optional)

# 5. Start the server
make run
```

### Google Calendar Setup (Optional)

To enable calendar events in daily briefings:

1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project and enable the **Google Calendar API**

2. **Create Service Account**
   - Go to APIs & Services → Credentials → Create Credentials → Service Account
   - Download the JSON key file and save as `google_credentials.json` in project root

3. **Share Your Calendar**
   - Open Google Calendar → Settings → Your calendar → Share with specific people
   - Add the service account email (from `client_email` in your JSON file)
   - Grant "See all event details" permission

4. **Configure Environment Variable**
   ```bash
   cp .env.example .env
   # Edit .env and set your calendar email:
   # GOOGLE_CALENDAR_ID=your.email@gmail.com
   ```

5. **Run with Calendar**
   ```bash
   export GOOGLE_CALENDAR_ID="your.email@gmail.com"
   make run
   ```

### Docker (Alternative)

Run Jarvis in a container:

```bash
# Build and start
make docker-build
make docker-up

# View logs
make docker-logs

# Stop
make docker-down
```

> **Note:** Ensure `secrets.json` exists before running. The database is persisted in a Docker volume.

## Usage

### Start the Server

```bash
python heart.py
# or
make run
```

The server will start at `http://127.0.0.1:8000`.

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | Conversational interface with Nova |
| `/weather` | GET | Get current weather forecast |
| `/events` | GET | Get today's calendar events |
| `/todos` | GET | Get today's tasks from Todoist |
| `/daily` | GET | Run daily routine (weather + calendar + todos + AI briefing) |
| `/intro` | GET | AI-generated assistant introduction |
| `/test` | GET | Test external API connectivity |

### Example

```bash
# Get today's weather
curl http://localhost:8000/weather

# Run daily briefing (speaks aloud)
curl http://localhost:8000/daily

# Chat with Nova
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the weather like?"}'

# Follow-up question (Nova remembers context)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Will I need an umbrella?"}'
```

### How Intent Detection Works

Nova uses a **hybrid intent detection** system to understand your requests:

```
User: "What meetings do I have today?"
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. Regex Fast Path                                              │
│    → "meetings" matches EVENTS pattern → confidence 0.7         │
└─────────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Data Fetch                                                   │
│    → Intent.EVENTS detected → fetch calendar via cache          │
│    → Events: [{title: "Team Standup", time: "10:00 AM"}, ...]   │
└─────────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. AI Response                                                  │
│    → Context includes current time + events                     │
│    → Nova: "You have 3 meetings today. Your next one is..."     │
└─────────────────────────────────────────────────────────────────┘
```

| Intent | Triggers | Example |
|--------|----------|---------|
| Weather | weather, rain, temperature, umbrella | "Do I need a jacket?" |
| Events | calendar, meeting, schedule | "What's on my calendar?" |
| Todos | todo, task, reminder | "What tasks do I have?" |
| Refresh | refresh, update, check again | "Refresh my calendar" |

For ambiguous queries like *"Do I need an umbrella for my meeting?"*, Nova uses LLM classification to detect **both** weather and events intents.

## Configuration

### secrets.json

```json
{
  "gemini_api_key": "your-google-gemini-api-key",
  "todoist_api_token": "your-todoist-api-token"
}
```

Get your Todoist API token from: **Todoist Settings → Integrations → Developer**

### Weather Location

Default location is set in `apis/weather.py`. To change:

```python
weather_api = WeatherAPI()
weather_api.set_coordinates(lat=40.7128, lon=-74.0060)  # New York
```

## Development Status

### ✅ Completed
- Conversation memory with SQLite storage
- TTL-based data caching
- Weather API integration (Open-Meteo)
- Google Calendar API integration (service account)
- Todoist API integration (REST API v2)
- Gemini AI integration for natural language processing
- Text-to-speech output with speed adjustment
- Daily routine endpoint with unified AI briefing

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