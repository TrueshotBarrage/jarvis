# Jarvis

Welcome to Jarvis, a fully automated personal assistant.

## Functionality

- Give an overview of the upcoming day: the weather, todos, events.

## Components

- Heart (server): The central coordinator. Stitches everything together into a
  single, cohesive unit.
- Armor (frontend): The pretty face. The visible, exposed parts of Jarvis.
- Mouth (voice interface): Jarvis will interpret your verbal commands and handle
  them properly through this unit.
- Brain (AI): Any complicated operations must be handled intelligently. Those go
  here.
- Arms (API): Reaches out to other components. Features the API interface for
  handling all calls to other internal components or external APIs.

## Development Status

### Completed:

- Overview of upcoming day
  - Today's weather

### In Progress:

- Overview of upcoming day
  - Today's todos
  - Today's events

### Not Started:

- Picovoice Porcupine integration for wake word detection mechanism
  - Likely to be a separate application, probably a Swift project
    for a simple, standalone iOS app that will perpetually run in 
    the background to listen for triggers.
  - The backend routes (on this app) will handle the process 
    post-trigger:
    - Route to handle initializing the audio stream for the user request input
    - Route to handle the actual audio streaming process
  - The server's response audio output will then be sent and handled 
    by the iOS app.
- 