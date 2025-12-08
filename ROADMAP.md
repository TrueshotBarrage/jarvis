# Jarvis Development Roadmap

This roadmap outlines planned features and improvements based on existing TODOs, comments, and architectural vision.

---

## 🎯 Priority 1: Core Functionality Completion

### Todoist Integration
**Status:** Stub exists in `arms.py`  
**Effort:** Medium

- [ ] Set up Todoist API authentication
- [ ] Implement `get_todos(day)` method
- [ ] Add daily todos to `/daily` routine
- [ ] Create `/todos` endpoint

### Google Calendar Integration
**Status:** Stub exists in `arms.py`  
**Effort:** Medium

- [ ] Set up Google Calendar OAuth flow
- [ ] Implement `get_events(day)` method
- [ ] Add calendar events to `/daily` routine
- [ ] Create `/events` endpoint

---

## 🎯 Priority 2: Voice Interface

### Wake Word Detection (iOS App)
**Status:** Planned in README  
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
**Status:** Commented out in `heart.py`  
**Effort:** Medium

- [ ] Finish `/user_input` endpoint
- [ ] Implement action routing based on AI classification
- [ ] Add probability-based action selection

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
- [ ] Add unit tests
- [ ] Add integration tests
- [ ] CI/CD pipeline
- [ ] Docker containerization
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
| 1 | Todoist + Calendar | Q1 2025 |
| 2 | Voice Interface | Q2 2025 |
| 3 | Advanced Features | Q3 2025 |
