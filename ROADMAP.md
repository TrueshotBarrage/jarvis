# Jarvis Development Roadmap

This roadmap outlines planned features and improvements based on existing TODOs, comments, and architectural vision.

---

## 🎯 Priority 1: Core Functionality ✅ Complete

### Todoist Integration ✅
- [x] Set up Todoist API authentication
- [x] Implement `get_todos(day)` method
- [x] Create `/todos` endpoint

### Google Calendar Integration ✅
- [x] Set up Google Calendar service account auth
- [x] Implement `get_events(day)` method
- [x] Multi-calendar support

### Conversation Memory System ✅ (v0.4.0)
- [x] SQLite-based conversation storage
- [x] TTL-based data cache with persistence
- [x] `/chat` endpoint for multi-turn conversations

### Hybrid Intent Detection ✅ (v0.5.0)
- [x] Regex fast-path + LLM fallback
- [x] Multi-intent support
- [x] Query similarity caching

### Environment Configuration ✅ (v0.6.0)
- [x] Pydantic Settings with `.env` support
- [x] Docker containerization
- [x] CI/CD pipeline

---

## 🎯 Priority 2: Personal Data Integration

### Google Sheets Integration
**Status:** Planned  
**Effort:** Medium

Read-only access to personal spreadsheets, with write as a future phase.

#### Phase 1: Read Access
- [ ] Google Sheets API setup (service account)
- [ ] `apis/sheets.py` wrapper class
- [ ] Generic cell/range reading
- [ ] `/sheets/{sheet_id}` endpoint

#### Phase 2: Spreadsheet Types
- [ ] **Budget sheet** - Read spending categories, totals
- [ ] **People catalog** - Names, numbers, notes, gift ideas
- [ ] **Topical Bible** - Topics with verse references

#### Phase 3: Write Access (Future)
- [ ] Add expense entries to budget
- [ ] Add verses to topical Bible categories
- [ ] Update people catalog notes

---

### Calendar Intelligence System
**Status:** Planned  
**Effort:** Medium-High

Intelligent handling of different calendar types with specialized workflows.

#### Calendar Type Detection
Intent-based classification of calendars (similar to message intent detection):
- [ ] `calendar_classifier.py` - Detect calendar purpose from name/events
- [ ] Categories: `birthdays`, `social`, `work`, `personal`, `recurring`
- [ ] Config-based overrides for known calendars

#### Birthday Calendar Workflows
- [ ] Configurable reminder window (1 day, 1 week, etc.)
- [ ] Template-based message drafting
- [ ] Draft review before sending
- [ ] **Future:** Platform-specific sending (iMessage, SMS, etc.)

#### Social/Food Calendar Workflows
- [ ] Extract attendee names from events
- [ ] Link to People Catalog for context
- [ ] "Dinner with Sarah tomorrow" style summaries
- [ ] **Future:** Suggest conversation topics from notes

#### Calendar Context in Prompts
- [ ] Include calendar source in event context
- [ ] Tailored AI responses based on calendar type
- [ ] "Your birthday reminder" vs "Your meeting"

---

### People Catalog Integration
**Status:** Planned  
**Effort:** Medium

Central repository of people metadata, linked to calendars and spreadsheets.

#### Phase 1: Read from Sheets
- [ ] Define People Catalog schema (name, phone, notes, gifts, etc.)
- [ ] Query by name: "Tell me about Sarah"
- [ ] Birthday lookup: "Whose birthday is this week?"

#### Phase 2: Calendar Linking
- [ ] Match event attendees to catalog entries
- [ ] Enrich calendar summaries with context
- [ ] "Lunch with Sarah (colleague, likes Thai food)"

#### Phase 3: Write Access (Future)
- [ ] "Add note about Sarah: prefers window seats"
- [ ] "Gift idea for Mom: new cookbook"

---

## 🎯 Priority 3: Voice Interface

### Wake Word Detection (iOS App)
**Status:** Planned  
**Effort:** High

```
┌─────────────────┐     ┌─────────────────┐
│  iOS App        │────▶│  Jarvis Server  │
│  (Porcupine)    │     │                 │
│                 │◀────│  Audio Response │
└─────────────────┘     └─────────────────┘
```

- [ ] Create Swift iOS project
- [ ] Integrate Picovoice Porcupine SDK
- [ ] Background wake word listening
- [ ] Audio streaming to server

### Server Audio Endpoints
- [ ] POST `/audio/stream` - Handle audio input
- [ ] WebSocket support for real-time audio
- [ ] Speech-to-text integration

---

## 🎯 Priority 4: Future Features

### Message Sending Automation
- [ ] Platform-agnostic message queue
- [ ] Draft review workflow
- [ ] **Future:** iMessage via AppleScript (macOS only)
- [ ] **Future:** SMS via Twilio or similar
- [ ] **Future:** Android intent support

### Autobudget Pipeline
- [ ] Cloud/RPi server endpoint
- [ ] Trigger from Jarvis command
- [ ] `/budget` endpoint

### Advanced Personalization
- [ ] Learning user preferences over time
- [ ] Proactive suggestions based on patterns
- [ ] Cross-calendar and cross-spreadsheet insights

---

## 🔧 Technical Debt ✅ Complete

### Code Quality ✅
- [x] Type hints across all modules
- [x] Comprehensive docstrings
- [x] Error handling

### Infrastructure ✅
- [x] 137 unit tests
- [x] CI/CD pipeline
- [x] Docker containerization
- [x] Environment-based configuration

### Documentation ✅
- [x] README, DEVELOPMENT, CONTRIBUTING
- [x] API documentation
- [x] GEMINI.md for AI agents

---

## Timeline

| Phase | Focus | Target |
|-------|-------|--------|
| 1 | Core Features | ✅ Complete |
| 2 | Personal Data (Sheets, Calendar Intelligence) | Q1 2025 |
| 3 | Voice Interface | Q2 2025 |
| 4 | Future Features | Q3 2025+ |
