# Jarvis Development Roadmap

This roadmap outlines planned features and improvements based on existing TODOs, comments, and architectural vision.

---

## 🎯 Priority 1: Core Functionality Completion

### Todoist Integration
**Status:** ✅ Complete  
**Effort:** Medium

- [x] Set up Todoist API authentication
- [x] Implement `get_todos(day)` method
- [x] Add daily todos to `/daily` routine
- [x] Create `/todos` endpoint

### Google Calendar Integration
**Status:** ✅ Complete  
**Effort:** Medium

- [x] Set up Google Calendar OAuth flow
- [x] Implement `get_events(day)` method
- [x] Add calendar events to `/daily` routine
- [x] Create `/events` endpoint

### Conversation Memory System
**Status:** ✅ Complete (v0.4.0)  
**Effort:** Medium

- [x] SQLite-based conversation storage (`memory.py`)
- [x] TTL-based data cache (`cache.py`)
- [x] Persistent cache with failure fallback
- [x] `/chat` endpoint for multi-turn conversations
- [x] Context window management

### Hybrid Intent Detection
**Status:** ✅ Complete (v0.5.0)  
**Effort:** Medium

- [x] Regex fast-path for clear queries
- [x] LLM classification with few-shot examples
- [x] Query similarity caching
- [x] Multi-intent support
- [x] Usage logging for pattern analysis

---

## 🎯 Priority 2: Voice Interface

### Wake Word Detection (iOS App)
**Status:** Planned  
**Effort:** High

Architecture:
```
┌─────────────────┐     ┌─────────────────┐
│  iOS App        │────▶│  Jarvis Server  │
│  (Porcupine)    │     │                 │
│                 │◀────│  Audio Response │
└─────────────────┘     └─────────────────┘
```

- [ ] Create Swift iOS project
- [ ] Integrate Picovoice Porcupine SDK
- [ ] Implement background wake word listening
- [ ] Build audio streaming to server
- [ ] Handle server response playback

### Server Audio Endpoints
**Status:** Not started  
**Effort:** Medium

- [ ] POST `/audio/init` - Initialize audio stream
- [ ] POST `/audio/stream` - Handle streaming audio input
- [ ] WebSocket support for real-time audio

---

## 🎯 Priority 3: Advanced Features

### User Intent Routing
**Status:** ✅ Complete  
**Effort:** Medium

- [x] Implement action routing based on AI classification
- [x] Add probability-based action selection
- [x] Hybrid regex + LLM detection

### Autobudget Pipeline
**Status:** Stub in `arms.py`  
**Effort:** Low (external service)

- [ ] Set up cloud/RPi server endpoint
- [ ] Implement `run_autobudget_pipeline()` trigger
- [ ] Create `/budget` endpoint

---

## 🔧 Technical Debt

### Code Quality
- [x] Fix duplicate function names in `heart.py`
- [x] Add proper type hints across all modules
- [x] Add comprehensive docstrings
- [x] Improve error handling

### Infrastructure
- [x] Add unit tests (139 tests)
- [x] Add integration tests
- [x] CI/CD pipeline
- [x] Docker containerization
- [ ] Environment-based configuration

### Documentation
- [x] Comprehensive README
- [x] API documentation
- [ ] Developer setup guide
- [ ] Contributing guidelines

---

## Timeline

| Phase | Focus | Target |
|-------|-------|--------|
| 1 | Core Features | ✅ Complete |
| 2 | Voice Interface | Q2 2025 |
| 3 | Advanced Features | Q3 2025 |
